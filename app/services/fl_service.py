"""Orchestrator service for Federated Learning training, aggregation,
checkpointing, cleanup, and forecast generation.
"""
from uuid import UUID
from datetime import date, datetime, timedelta, timezone
from typing import Optional, List, Dict, Any, Tuple
import os
import time
import tempfile
import math
import torch
from sqlalchemy.orm import Session
from sqlalchemy import text
from fastapi import HTTPException, status

from app.models.user import User
from app.models.geography import State, District, Facility
from app.models.drug import Drug
from app.models.inventory import InventoryBatch
from app.models.audit import AuditResultEnum
from app.models.fl import (
    FlRound,
    FlModel,
    FlForecast,
    FlRoundStatusEnum,
    FlNodeLevelEnum,
    DrugConsumptionHistory,
)
from app.schemas.fl import (
    FlRoundTriggerResponse,
    FlRoundDetailResponse,
    FlRoundListResponse,
    FlStatusResponse,
    FacilityForecastResponse,
    DrugForecastResponse,
    ForecastItemResponse,
    FlModelResponse,
)
from app.schemas.common import PaginationMeta
from app.repositories.fl_repo import FlRepository
from app.services.audit_service import AuditService
from app.ml.model import RegionalDemandNet, ARCHITECTURE_HASH
from app.ml.features import build_drug_index_map
from app.ml.trainer import train_local_model
from app.ml.aggregator import federated_average
from app.ml.inference import forecast_from_serving_model
from app.ml.storage import get_storage, StorageBackend
from app.core.config import settings


def cleanup_old_archives(storage: StorageBackend, db: Session, keep_last_n: int = 5) -> None:
    """Keeps the last keep_last_n completed rounds in archive/, deletes older round archives."""
    completed_rounds = (
        db.query(FlRound.round_number)
        .filter(FlRound.status == FlRoundStatusEnum.COMPLETED)
        .order_by(FlRound.round_number.desc())
        .all()
    )
    if len(completed_rounds) > keep_last_n:
        rounds_to_delete = completed_rounds[keep_last_n:]
        for (r_num,) in rounds_to_delete:
            archive_prefix = f"fl/archive/round_{r_num}"
            try:
                storage.delete(archive_prefix)
            except Exception:
                pass


class FlService:
    @staticmethod
    def rollup_consumption_history(db: Session, from_date: date, to_date: date) -> int:
        """Rollup dispense transactions into drug_consumption_history. Idempotent."""
        return FlRepository.rollup_dispense_transactions(db, from_date, to_date)

    @classmethod
    def trigger_round(cls, db: Session, actor: User, ip_address: str) -> FlRoundTriggerResponse:
        """
        Orchestrates an end-to-end 3-tier hierarchical Federated Learning round:
        1. Advisory lock protection against concurrent execution
        2. Rollup consumption history for past 90 days
        3. Warm start lineage from previous nation/serving model
        4. District-level local training
        5. State-level FedAvg
        6. Nation-level FedAvg
        7. 7-day facility forecast generation
        8. Rolling archive cleanup
        9. Audit logging
        """
        lock_key = "fl_round_trigger"
        is_postgres = db.bind.dialect.name == "postgresql"

        # ALWAYS check for a stuck RUNNING round in the DB first (any dialect)
        running_round = db.query(FlRound).filter(
            FlRound.status == FlRoundStatusEnum.RUNNING
        ).first()
        if running_round:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"Round {running_round.round_number} is still marked RUNNING. "
                    f"Investigate or abandon it before triggering a new round."
                ),
            )

        # THEN check the advisory lock (Postgres only — SQLite tests skip this)
        if is_postgres:
            acquired = db.execute(
                text("SELECT pg_try_advisory_lock(hashtext(:k))"),
                {"k": lock_key},
            ).scalar()
            if not acquired:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Another FL round is currently in progress",
                )

        start_time = time.time()
        start_dt = datetime.now(timezone.utc)
        storage = get_storage()

        # Step 1: Rollup consumption history (past 90 days)
        today = date.today()
        from_d = today - timedelta(days=90)
        cls.rollup_consumption_history(db, from_d, today)

        # Step 2: Determine next round_number & create round row
        latest_round = FlRepository.get_latest_round(db)
        round_number = (latest_round.round_number + 1) if latest_round else 1
        parent_round_id = latest_round.id if latest_round else None

        fl_round = FlRound(
            round_number=round_number,
            status=FlRoundStatusEnum.RUNNING,
            started_at=start_dt,
            parent_round_id=parent_round_id,
            participating_districts=0,
            participating_states=0,
            total_samples=0,
        )
        db.add(fl_round)
        db.commit()
        db.refresh(fl_round)

        model_paths_map: Dict[str, str] = {}

        try:
            # Step 3: Warm start weights: try loading current nation model
            base_state_dict: Optional[Dict[str, torch.Tensor]] = None
            nation_key = "fl/current/nation.pt"
            if storage.exists(nation_key):
                tmp_fd, tmp_path = tempfile.mkstemp(suffix=".pt")
                os.close(tmp_fd)
                try:
                    storage.load(nation_key, tmp_path)
                    base_state_dict = torch.load(tmp_path, map_location="cpu")
                finally:
                    if os.path.exists(tmp_path):
                        os.remove(tmp_path)

            # Step 4: Tier 1 - District local training
            all_drugs = db.query(Drug).filter(Drug.is_active == True).order_by(Drug.id).all()
            drug_index_map = build_drug_index_map([d.id for d in all_drugs])

            districts = db.query(District).all()
            district_state_dicts: Dict[UUID, Dict[str, torch.Tensor]] = {}
            district_sample_counts: Dict[UUID, int] = {}
            district_to_state: Dict[UUID, UUID] = {}

            total_round_samples = 0

            for dist in districts:
                district_to_state[dist.id] = dist.state_id

                drug_series_list = []
                for drug in all_drugs:
                    series = FlRepository.get_district_drug_consumption_history(
                        db, dist.id, drug.id, from_date=from_d
                    )
                    if len(series) >= 20:  # require minimum history per drug
                        drug_series_list.append((drug.id, series))

                if not drug_series_list:
                    # Skip this district — insufficient history
                    continue

                state_dict, metrics = train_local_model(
                    base_state_dict=base_state_dict,
                    drug_series_list=drug_series_list,
                    drug_index_map=drug_index_map,
                    epochs=15,
                    batch_size=32,
                    lr=0.005,
                )

                samples = metrics.get("sample_count", 0)
                district_state_dicts[dist.id] = state_dict
                district_sample_counts[dist.id] = samples
                total_round_samples += samples

                # Save district .pt
                archive_key = f"fl/archive/round_{round_number}/districts/{dist.id}.pt"
                serving_key = f"fl/current/districts/{dist.id}.pt"

                tmp_fd, tmp_path = tempfile.mkstemp(suffix=".pt")
                os.close(tmp_fd)
                try:
                    torch.save(state_dict, tmp_path)
                    size_bytes = storage.save(tmp_path, archive_key)
                    storage.copy(archive_key, serving_key)
                finally:
                    if os.path.exists(tmp_path):
                        os.remove(tmp_path)

                model_paths_map[f"district_{dist.code}"] = serving_key

                # Clear previous is_serving for this district
                FlRepository.clear_serving_flags_for_node(db, FlNodeLevelEnum.DISTRICT, dist.id)

                hyperparameters = {
                    "epochs": 15,
                    "batch_size": 32,
                    "lr": 0.005,
                    "n_features": 32,
                    "norm_denom_map": {
                        str(k): v for k, v in metrics.get("norm_denom_map", {}).items()
                    },
                }

                dist_model = FlModel(
                    round_id=fl_round.id,
                    node_level=FlNodeLevelEnum.DISTRICT,
                    node_id=dist.id,
                    archive_path=archive_key,
                    serving_path=serving_key,
                    is_serving=True,
                    model_size_bytes=size_bytes,
                    architecture_hash=ARCHITECTURE_HASH,
                    hyperparameters=hyperparameters,
                    training_metrics=metrics,
                    sample_count=samples,
                )
                db.add(dist_model)

            # Step 5: Tier 2 - State Aggregation (FedAvg)
            states = db.query(State).all()
            state_state_dicts: Dict[UUID, Dict[str, torch.Tensor]] = {}
            state_sample_counts: Dict[UUID, int] = {}

            for state in states:
                child_district_ids = [d.id for d in districts if d.state_id == state.id and d.id in district_state_dicts]
                if not child_district_ids:
                    continue

                dicts_to_avg = [district_state_dicts[did] for did in child_district_ids]
                counts_to_avg = [district_sample_counts[did] for did in child_district_ids]
                st_state_dict = federated_average(dicts_to_avg, counts_to_avg)
                st_samples = sum(counts_to_avg)

                state_state_dicts[state.id] = st_state_dict
                state_sample_counts[state.id] = st_samples

                archive_key = f"fl/archive/round_{round_number}/states/{state.id}.pt"
                serving_key = f"fl/current/states/{state.id}.pt"

                tmp_fd, tmp_path = tempfile.mkstemp(suffix=".pt")
                os.close(tmp_fd)
                try:
                    torch.save(st_state_dict, tmp_path)
                    size_bytes = storage.save(tmp_path, archive_key)
                    storage.copy(archive_key, serving_key)
                finally:
                    if os.path.exists(tmp_path):
                        os.remove(tmp_path)

                model_paths_map[f"state_{state.code}"] = serving_key

                FlRepository.clear_serving_flags_for_node(db, FlNodeLevelEnum.STATE, state.id)

                state_model = FlModel(
                    round_id=fl_round.id,
                    node_level=FlNodeLevelEnum.STATE,
                    node_id=state.id,
                    archive_path=archive_key,
                    serving_path=serving_key,
                    is_serving=True,
                    model_size_bytes=size_bytes,
                    architecture_hash=ARCHITECTURE_HASH,
                    hyperparameters={"aggregation": "FedAvg"},
                    training_metrics={"participating_nodes": len(child_district_ids)},
                    sample_count=st_samples,
                )
                db.add(state_model)

            # Step 6: Tier 3 - Nation Aggregation
            # If >1 state: FedAvg over state models. If 1 state: copy state model as national model.
            nation_state_dict: Optional[Dict[str, torch.Tensor]] = None
            if len(state_state_dicts) > 1:
                nation_state_dict = federated_average(
                    list(state_state_dicts.values()),
                    list(state_sample_counts.values()),
                )
            elif len(state_state_dicts) == 1:
                nation_state_dict = list(state_state_dicts.values())[0]

            if nation_state_dict is not None:
                archive_key = f"fl/archive/round_{round_number}/nation.pt"
                serving_key = "fl/current/nation.pt"

                tmp_fd, tmp_path = tempfile.mkstemp(suffix=".pt")
                os.close(tmp_fd)
                try:
                    torch.save(nation_state_dict, tmp_path)
                    size_bytes = storage.save(tmp_path, archive_key)
                    storage.copy(archive_key, serving_key)
                finally:
                    if os.path.exists(tmp_path):
                        os.remove(tmp_path)

                model_paths_map["nation"] = serving_key

                FlRepository.clear_serving_flags_for_node(db, FlNodeLevelEnum.NATION, None)

                nation_model = FlModel(
                    round_id=fl_round.id,
                    node_level=FlNodeLevelEnum.NATION,
                    node_id=None,
                    archive_path=archive_key,
                    serving_path=serving_key,
                    is_serving=True,
                    model_size_bytes=size_bytes,
                    architecture_hash=ARCHITECTURE_HASH,
                    hyperparameters={"aggregation": "FedAvg"},
                    training_metrics={"participating_states": len(state_state_dicts)},
                    sample_count=sum(state_sample_counts.values()),
                )
                db.add(nation_model)

            db.commit()

            # Step 7: Forecast generation per facility (7 days)
            facilities = db.query(Facility).all()

            for fac in facilities:
                district_model_record = (
                    db.query(FlModel)
                    .filter(
                        FlModel.node_level == FlNodeLevelEnum.DISTRICT,
                        FlModel.node_id == fac.district_id,
                        FlModel.is_serving == True,
                    )
                    .first()
                )
                if not district_model_record:
                    # No serving model for this district — skip this facility
                    continue

                facility_drug_ids = {
                    row[0] for row in db.query(InventoryBatch.drug_id)
                    .filter(InventoryBatch.facility_id == fac.id)
                    .distinct()
                    .all()
                }
                facility_drugs = [d for d in all_drugs if d.id in facility_drug_ids]

                for drug in facility_drugs:
                    hist = FlRepository.get_consumption_history_for_facility_drug(
                        db=db,
                        facility_id=fac.id,
                        drug_id=drug.id,
                        from_date=today - timedelta(days=30),
                    )
                    if len(hist) < 10:
                        # Not enough history — use a fallback baseline
                        hist = [(today - timedelta(days=i), 5.0) for i in range(10, 0, -1)]

                    forecast_items = forecast_from_serving_model(
                        db=db,
                        storage=storage,
                        node_level=FlNodeLevelEnum.DISTRICT,
                        node_id=fac.district_id,
                        drug_id=drug.id,
                        drug_index_map=drug_index_map,
                        recent_history=hist,
                        n_days=7,
                        start_date=today + timedelta(days=1),
                    )

                    for f_date, pred_qty in forecast_items:
                        db.add(
                            FlForecast(
                                round_id=fl_round.id,
                                model_id=district_model_record.id,
                                facility_id=fac.id,
                                drug_id=drug.id,
                                forecast_date=f_date,
                                predicted_quantity=pred_qty,
                            )
                        )

            # Step 8: Update round metadata
            duration = round(time.time() - start_time, 2)
            fl_round.status = FlRoundStatusEnum.COMPLETED
            fl_round.completed_at = datetime.now(timezone.utc)
            fl_round.participating_districts = len(district_state_dicts)
            fl_round.participating_states = len(state_state_dicts)
            fl_round.total_samples = total_round_samples
            fl_round.duration_seconds = duration
            db.commit()

            # Step 9: Cleanup old archives
            cleanup_old_archives(storage, db, keep_last_n=settings.MODELS_ARCHIVE_KEEP_ROUNDS)

            # Step 10: Audit log
            AuditService.log_event(
                db=db,
                action="fl_round_triggered",
                ip_address=ip_address,
                result=AuditResultEnum.SUCCESS,
                user_id=actor.id,
                resource_type="fl_round",
                resource_id=fl_round.id,
                metadata={
                    "round_number": round_number,
                    "duration_seconds": duration,
                    "participating_districts": len(district_state_dicts),
                    "participating_states": len(state_state_dicts),
                    "total_samples": total_round_samples,
                },
            )
            db.commit()

            return FlRoundTriggerResponse(
                round_number=round_number,
                status=FlRoundStatusEnum.COMPLETED,
                participating_districts=len(district_state_dicts),
                participating_states=len(state_state_dicts),
                total_samples=total_round_samples,
                duration_seconds=duration,
                model_paths=model_paths_map,
            )

        except Exception as e:
            db.rollback()
            fl_round_record = db.query(FlRound).filter(FlRound.id == fl_round.id).first()
            if fl_round_record:
                fl_round_record.status = FlRoundStatusEnum.FAILED
                fl_round_record.error_message = str(e)[:1000]
                fl_round_record.duration_seconds = round(time.time() - start_time, 2)
                db.commit()

            AuditService.log_event(
                db=db,
                action="fl_round_triggered",
                ip_address=ip_address,
                result=AuditResultEnum.FAILED,
                user_id=actor.id,
                resource_type="fl_round",
                resource_id=fl_round.id,
                metadata={"round_number": round_number, "error": str(e)},
            )
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"FL round execution failed: {str(e)}",
            )
        finally:
            if is_postgres:
                db.execute(
                    text("SELECT pg_advisory_unlock(hashtext(:k))"),
                    {"k": lock_key},
                )
                db.commit()

    @staticmethod
    def get_status(db: Session) -> FlStatusResponse:
        latest = FlRepository.get_latest_round(db)
        serving_models = FlRepository.get_serving_models(db)
        serving_paths: Dict[str, str] = {}
        for m in serving_models:
            key = f"{m.node_level.value}_{m.node_id or 'all'}"
            serving_paths[key] = m.serving_path

        forecast_count = 0
        if latest:
            forecast_count = db.query(FlForecast).filter(FlForecast.round_id == latest.id).count()

        latest_detail = (
            FlRoundDetailResponse(
                id=latest.id,
                round_number=latest.round_number,
                status=latest.status,
                started_at=latest.started_at,
                completed_at=latest.completed_at,
                parent_round_id=latest.parent_round_id,
                participating_districts=latest.participating_districts,
                participating_states=latest.participating_states,
                total_samples=latest.total_samples,
                duration_seconds=latest.duration_seconds,
                error_message=latest.error_message,
                notes=latest.notes,
                models=[FlModelResponse.model_validate(m) for m in latest.models],
            )
            if latest
            else None
        )

        return FlStatusResponse(
            latest_round=latest_detail,
            serving_model_paths=serving_paths,
            last_forecast_count=forecast_count,
        )

    @staticmethod
    def list_rounds(db: Session, page: int = 1, page_size: int = 20) -> FlRoundListResponse:
        items, total = FlRepository.list_rounds(db, page=page, page_size=page_size)
        res_items = []
        for r in items:
            res_items.append(
                FlRoundDetailResponse(
                    id=r.id,
                    round_number=r.round_number,
                    status=r.status,
                    started_at=r.started_at,
                    completed_at=r.completed_at,
                    parent_round_id=r.parent_round_id,
                    participating_districts=r.participating_districts,
                    participating_states=r.participating_states,
                    total_samples=r.total_samples,
                    duration_seconds=r.duration_seconds,
                    error_message=r.error_message,
                    notes=r.notes,
                    models=[FlModelResponse.model_validate(m) for m in r.models],
                )
            )
        total_pages = math.ceil(total / page_size) if total > 0 else 0
        return FlRoundListResponse(
            items=res_items,
            pagination=PaginationMeta(
                page=page,
                page_size=page_size,
                total_items=total,
                total_pages=total_pages,
            ),
        )

    @staticmethod
    def get_round_detail(db: Session, round_id: UUID) -> FlRoundDetailResponse:
        r = FlRepository.get_round_by_id(db, round_id)
        if not r:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="FL round not found")
        return FlRoundDetailResponse(
            id=r.id,
            round_number=r.round_number,
            status=r.status,
            started_at=r.started_at,
            completed_at=r.completed_at,
            parent_round_id=r.parent_round_id,
            participating_districts=r.participating_districts,
            participating_states=r.participating_states,
            total_samples=r.total_samples,
            duration_seconds=r.duration_seconds,
            error_message=r.error_message,
            notes=r.notes,
            models=[FlModelResponse.model_validate(m) for m in r.models],
        )

    @staticmethod
    def get_model_detail(db: Session, model_id: UUID) -> FlModelResponse:
        m = FlRepository.get_model_by_id(db, model_id)
        if not m:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="FL model not found")
        return FlModelResponse.model_validate(m)

    @staticmethod
    def get_facility_forecast(
        db: Session, facility_id: UUID, drug_id: Optional[UUID] = None, days: int = 7
    ) -> FacilityForecastResponse:
        fac = db.query(Facility).filter(Facility.id == facility_id).first()
        if not fac:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Facility not found")

        forecasts = FlRepository.get_facility_forecasts(db, facility_id=facility_id, drug_id=drug_id, days=days)
        if not forecasts:
            return FacilityForecastResponse(
                facility_id=fac.id,
                facility_name=fac.name,
                round_number=None,
                generated_at=None,
                drugs=[],
            )

        round_num = forecasts[0].round.round_number if forecasts[0].round else None
        gen_at = forecasts[0].generated_at

        # Group by drug
        by_drug: Dict[UUID, List[ForecastItemResponse]] = {}
        drug_names: Dict[UUID, str] = {}
        for f in forecasts:
            if f.drug_id not in by_drug:
                by_drug[f.drug_id] = []
                drug_names[f.drug_id] = f.drug.name if f.drug else "Unknown Drug"
            by_drug[f.drug_id].append(
                ForecastItemResponse(
                    forecast_date=f.forecast_date,
                    predicted_quantity=f.predicted_quantity,
                )
            )

        drug_res = [
            DrugForecastResponse(
                drug_id=d_id,
                drug_name=drug_names[d_id],
                forecasts=by_drug[d_id][:days],
            )
            for d_id in by_drug
        ]

        return FacilityForecastResponse(
            facility_id=fac.id,
            facility_name=fac.name,
            round_number=round_num,
            generated_at=gen_at,
            drugs=drug_res,
        )

    @staticmethod
    def abandon_round(
        db: Session,
        round_id: UUID,
        actor: User,
        ip_address: str,
    ) -> FlRoundDetailResponse:
        """
        Mark a RUNNING round as failed with an admin reason.
        """
        round_rec = FlRepository.get_round_by_id(db, round_id)
        if not round_rec:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="FL round not found",
            )
        if round_rec.status != FlRoundStatusEnum.RUNNING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Only RUNNING rounds can be abandoned (current status: {round_rec.status.value})",
            )

        round_rec.status = FlRoundStatusEnum.FAILED
        round_rec.error_message = "Manually abandoned by admin"
        round_rec.completed_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(round_rec)

        AuditService.log_event(
            db=db,
            action="fl_round_abandoned",
            ip_address=ip_address,
            result=AuditResultEnum.SUCCESS,
            user_id=actor.id,
            resource_type="fl_round",
            resource_id=str(round_rec.id),
            metadata={"round_number": round_rec.round_number},
        )
        db.commit()

        return FlService.get_round_detail(db, round_rec.id)

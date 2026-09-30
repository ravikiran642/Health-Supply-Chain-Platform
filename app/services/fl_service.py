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
        # Use postgres advisory lock if on postgres, else pass (e.g. SQLite tests)
        is_postgres = db.bind.dialect.name == "postgresql"
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
        else:
            # Check for any currently running round in DB
            running_round = db.query(FlRound).filter(FlRound.status == FlRoundStatusEnum.RUNNING).first()
            if running_round:
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
            districts = db.query(District).all()
            district_state_dicts: Dict[UUID, Dict[str, torch.Tensor]] = {}
            district_sample_counts: Dict[UUID, int] = {}
            district_to_state: Dict[UUID, UUID] = {}

            total_round_samples = 0

            for dist in districts:
                district_to_state[dist.id] = dist.state_id
                consumption_series = FlRepository.get_district_consumption_history(db, dist.id, from_date=from_d)
                
                # If district has no history, generate zero-history baseline so node participates
                if not consumption_series:
                    consumption_series = [(from_d + timedelta(days=i), 0) for i in range(15)]

                state_dict, metrics = train_local_model(
                    base_state_dict=base_state_dict,
                    consumption_series=consumption_series,
                    epochs=15,
                    batch_size=32,
                    lr=0.005,
                )
                samples = metrics.get("sample_count", len(consumption_series))
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

                dist_model = FlModel(
                    round_id=fl_round.id,
                    node_level=FlNodeLevelEnum.DISTRICT,
                    node_id=dist.id,
                    archive_path=archive_key,
                    serving_path=serving_key,
                    is_serving=True,
                    model_size_bytes=size_bytes,
                    architecture_hash=ARCHITECTURE_HASH,
                    hyperparameters={"epochs": 15, "batch_size": 32, "lr": 0.005},
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
            drugs = db.query(Drug).filter(Drug.is_active == True).all()

            for fac in facilities:
                # Find serving model for this facility's district
                dist_serving_model = (
                    db.query(FlModel)
                    .filter(
                        FlModel.node_level == FlNodeLevelEnum.DISTRICT,
                        FlModel.node_id == fac.district_id,
                        FlModel.is_serving == True,
                    )
                    .first()
                )
                model_to_use = dist_serving_model

                for drug in drugs:
                    hist = FlRepository.get_consumption_history_for_facility_drug(
                        db=db,
                        facility_id=fac.id,
                        drug_id=drug.id,
                        from_date=today - timedelta(days=30),
                    )
                    if not hist:
                        # Construct baseline history so forecasting succeeds
                        hist = [(today - timedelta(days=i), 5.0) for i in range(10, 0, -1)]

                    forecast_items = forecast_from_serving_model(
                        db=db,
                        storage=storage,
                        node_level=FlNodeLevelEnum.DISTRICT,
                        node_id=fac.district_id,
                        recent_history=hist,
                        n_days=7,
                        start_date=today + timedelta(days=1),
                    )

                    for f_date, pred_qty in forecast_items:
                        db.add(
                            FlForecast(
                                round_id=fl_round.id,
                                model_id=model_to_use.id if model_to_use else fl_round.models[0].id,
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

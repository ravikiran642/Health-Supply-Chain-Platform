"""Inference module for serving forecasts from active RegionalDemandNet models."""
from uuid import UUID
from datetime import date, timedelta
from typing import List, Tuple, Optional, Any, Union, Dict
import os
import tempfile
import torch
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.fl import FlModel, FlNodeLevelEnum
from app.ml.model import RegionalDemandNet, ARCHITECTURE_HASH
from app.ml.features import build_inference_input
from app.ml.storage import StorageBackend


def forecast_from_serving_model(
    db: Session,
    storage: StorageBackend,
    node_level: FlNodeLevelEnum,
    node_id: Optional[UUID],
    drug_id: Any,
    drug_index_map: dict,
    recent_history: List[Tuple[Union[date, str], Union[int, float]]],
    n_days: int = 7,
    start_date: Optional[date] = None,
) -> List[Tuple[date, float]]:
    """
    Load the district-level model. Read norm_denom_map from
    model_record.hyperparameters["norm_denom_map"]. Look up norm_denom = 
    norm_denom_map[str(drug_id)]. If missing, fall back to max(recent_history)
    or 1.0.

    Build inference input with drug_id + drug_index_map + norm_denom.
    Model output is already on raw scale; clamp to non-negative and round to 2 decimals.
    Return list of (date, predicted_quantity).
    """
    query = db.query(FlModel).filter(
        FlModel.node_level == node_level,
        FlModel.is_serving == True,
    )
    if node_id is not None:
        query = query.filter(FlModel.node_id == node_id)
    else:
        query = query.filter(FlModel.node_id.is_(None))

    model_record = query.first()
    if not model_record:
        # Fallback to nation if district/state model not yet trained or not serving
        if node_level != FlNodeLevelEnum.NATION:
            return forecast_from_serving_model(
                db=db,
                storage=storage,
                node_level=FlNodeLevelEnum.NATION,
                node_id=None,
                drug_id=drug_id,
                drug_index_map=drug_index_map,
                recent_history=recent_history,
                n_days=n_days,
                start_date=start_date,
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"No serving model available for {node_level.value} (node_id: {node_id})",
        )

    # Verify architecture hash
    if model_record.architecture_hash != ARCHITECTURE_HASH:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                f"Model architecture mismatch: record hash '{model_record.architecture_hash}' "
                f"!= runtime class hash '{ARCHITECTURE_HASH}'"
            ),
        )

    # Extract per-drug normalization denominator
    norm_denom = 1.0
    if model_record.hyperparameters and isinstance(model_record.hyperparameters, dict):
        norm_map = model_record.hyperparameters.get("norm_denom_map", {})
        if str(drug_id) in norm_map:
            norm_denom = float(norm_map[str(drug_id)])
        elif recent_history:
            max_hist = max(float(q) for _, q in recent_history)
            norm_denom = max_hist if max_hist > 0 else 1.0
    elif recent_history:
        max_hist = max(float(q) for _, q in recent_history)
        norm_denom = max_hist if max_hist > 0 else 1.0

    # Download .pt to temp file and load
    temp_fd, temp_path = tempfile.mkstemp(suffix=".pt")
    os.close(temp_fd)

    try:
        storage.load(model_record.serving_path, temp_path)
        state_dict = torch.load(temp_path, map_location="cpu")
        model = RegionalDemandNet(n_features=32)
        model.load_state_dict(state_dict)
        model.eval()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load serving model from '{model_record.serving_path}': {str(e)}",
        )
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

    # Autoregressive generation for n_days
    curr_history = list(recent_history)
    curr_date = start_date if start_date is not None else (date.today() + timedelta(days=1))
    forecasts: List[Tuple[date, float]] = []

    with torch.no_grad():
        for day_idx in range(n_days):
            target_date = curr_date + timedelta(days=day_idx)
            input_tensor = build_inference_input(
                recent_history=curr_history,
                drug_id=drug_id,
                drug_index_map=drug_index_map,
                norm_denom=norm_denom,
                seq_len=7,
            )
            raw_output = model(input_tensor).item()
            pred_qty = round(max(0.0, raw_output * norm_denom), 2)
            forecasts.append((target_date, pred_qty))
            curr_history.append((target_date, pred_qty))

    return forecasts

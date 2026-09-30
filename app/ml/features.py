"""Feature engineering for RegionalDemandNet using pure Python and numpy (no pandas)."""
from datetime import date, datetime
from typing import List, Tuple, Union, Dict, Any
from uuid import UUID
import numpy as np
import torch


def _parse_date(d: Union[date, datetime, str]) -> date:
    if isinstance(d, datetime):
        return d.date()
    elif isinstance(d, date):
        return d
    elif isinstance(d, str):
        return datetime.fromisoformat(d).date()
    raise ValueError(f"Unsupported date format: {type(d)}")


def build_drug_index_map(all_drug_ids: list) -> dict:
    """Map drug UUID -> stable index 0..N-1 for one-hot encoding.
    Sort drug IDs to keep the mapping deterministic across runs.
    """
    sorted_ids = sorted(all_drug_ids, key=lambda x: str(x))
    return {drug_id: idx for idx, drug_id in enumerate(sorted_ids)}


def build_feature_tensors(
    drug_series_list: list,
    drug_index_map: dict,
    seq_len: int = 7,
) -> tuple:
    """
    drug_series_list: list of (drug_id: UUID, [(date, quantity), ...])
    drug_index_map: {drug_id: index}

    Returns (X, y, norm_denom_map):
      X: torch.Tensor shape (n_samples, seq_len, 32)
      y: torch.Tensor shape (n_samples, 1)
      norm_denom_map: {drug_id: float} where norm_denom_map[drug_id] is the
                      max quantity observed for that drug across the training data.

    For each (drug_id, series):
      - Compute drug_max = max(series quantities). If 0, use 1.0 to avoid div-by-zero.
      - Normalize each quantity by drug_max.
      - Build 7-timestep sequences.
      - For each timestep, build 32-dim feature:
          [0]      normalized consumption for THIS drug at this timestep
          [1:8]    day-of-week one-hot (7)
          [8:20]   month one-hot (12)
          [20]     7-day rolling avg (normalized)
          [21]     30-day rolling avg (normalized)
          [22:32]  drug one-hot (10 dims, index from drug_index_map)
      - Target y[t] = raw (UN-normalized) consumption at t+1

    Concatenate sequences from all drugs into one big X, y.
    """
    norm_denom_map: Dict[Any, float] = {}
    all_X: List[np.ndarray] = []
    all_y: List[np.ndarray] = []

    for drug_id, consumption_series in drug_series_list:
        if not consumption_series or len(consumption_series) <= seq_len:
            norm_denom_map[drug_id] = 1.0
            continue

        sorted_series = sorted(
            [(_parse_date(d), float(q)) for d, q in consumption_series],
            key=lambda item: item[0],
        )

        dates = [item[0] for item in sorted_series]
        quantities = np.array([max(0.0, item[1]) for item in sorted_series], dtype=np.float32)
        n = len(quantities)

        drug_max = float(np.max(quantities))
        denom = drug_max if drug_max > 0.0 else 1.0
        norm_denom_map[drug_id] = denom
        norm_q = quantities / denom

        roll_7 = np.zeros(n, dtype=np.float32)
        roll_30 = np.zeros(n, dtype=np.float32)

        for i in range(n):
            start_7 = max(0, i - 6)
            roll_7[i] = float(np.mean(quantities[start_7 : i + 1])) / denom

            start_30 = max(0, i - 29)
            roll_30[i] = float(np.mean(quantities[start_30 : i + 1])) / denom

        # Precompute timestep feature vectors: (n, 32)
        timesteps = np.zeros((n, 32), dtype=np.float32)
        drug_idx = drug_index_map.get(drug_id, 0)
        drug_idx = min(9, max(0, drug_idx))  # 10 dims: indices 22..31

        for i in range(n):
            d = dates[i]
            # [0] normalized consumption
            timesteps[i, 0] = norm_q[i]

            # [1:8] day-of-week one-hot (Monday=0 to Sunday=6)
            dow = d.weekday()
            timesteps[i, 1 + dow] = 1.0

            # [8:20] month one-hot (Jan=1 to Dec=12)
            month = d.month - 1
            timesteps[i, 8 + month] = 1.0

            # [20] 7-day rolling avg
            timesteps[i, 20] = roll_7[i]

            # [21] 30-day rolling avg
            timesteps[i, 21] = roll_30[i]

            # [22:32] drug one-hot
            timesteps[i, 22 + drug_idx] = 1.0

        n_samples = n - seq_len
        if n_samples <= 0:
            continue

        X_drug = np.zeros((n_samples, seq_len, 32), dtype=np.float32)
        y_drug = np.zeros((n_samples, 1), dtype=np.float32)

        for i in range(n_samples):
            X_drug[i] = timesteps[i : i + seq_len]
            y_drug[i, 0] = quantities[i + seq_len]

        all_X.append(X_drug)
        all_y.append(y_drug)

    if not all_X:
        return (
            torch.empty((0, seq_len, 32), dtype=torch.float32),
            torch.empty((0, 1), dtype=torch.float32),
            norm_denom_map,
        )

    X_cat = np.concatenate(all_X, axis=0)
    y_cat = np.concatenate(all_y, axis=0)
    return torch.from_numpy(X_cat), torch.from_numpy(y_cat), norm_denom_map


def build_inference_input(
    recent_history: list,
    drug_id: Any,
    drug_index_map: dict,
    norm_denom: float,
    seq_len: int = 7,
) -> torch.Tensor:
    """
    Returns (1, seq_len, 32).

    - Uses provided norm_denom (must match training's per-drug denom for this drug).
    - Sets drug_onehot for drug_id.
    - Same feature layout as training.
    """
    if not recent_history:
        today = date.today()
        recent_history = [(today, 0.0)]

    sorted_series = sorted(
        [(_parse_date(d), float(q)) for d, q in recent_history],
        key=lambda item: item[0],
    )

    if len(sorted_series) < seq_len:
        earliest_date = sorted_series[0][0]
        padding_needed = seq_len - len(sorted_series)
        pad = [(earliest_date, 0.0) for _ in range(padding_needed)]
        sorted_series = pad + sorted_series

    window = sorted_series[-seq_len:]
    dates = [item[0] for item in window]
    quantities = np.array([max(0.0, item[1]) for item in window], dtype=np.float32)

    denom = float(norm_denom) if norm_denom and norm_denom > 0 else 1.0
    norm_q = quantities / denom

    drug_idx = drug_index_map.get(drug_id, 0)
    drug_idx = min(9, max(0, drug_idx))

    X = np.zeros((1, seq_len, 32), dtype=np.float32)
    for i in range(seq_len):
        d = dates[i]
        X[0, i, 0] = norm_q[i]

        dow = d.weekday()
        X[0, i, 1 + dow] = 1.0

        month = d.month - 1
        X[0, i, 8 + month] = 1.0

        # rolling averages within window
        X[0, i, 20] = float(np.mean(quantities[: i + 1])) / denom
        X[0, i, 21] = float(np.mean(quantities[: i + 1])) / denom

        # drug one-hot
        X[0, i, 22 + drug_idx] = 1.0

    return torch.from_numpy(X)

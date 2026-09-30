"""Feature engineering for RegionalDemandNet using pure Python and numpy (no pandas)."""
from datetime import date, datetime
from typing import List, Tuple, Union
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


def build_feature_tensors(
    consumption_series: List[Tuple[Union[date, str], Union[int, float]]],
    seq_len: int = 7,
) -> Tuple[torch.Tensor, torch.Tensor]:
    """
    Input: [(date, quantity), ...] sorted or unsorted.
    Output: (X, y)
      X shape: (n_samples, seq_len, 22)
      y shape: (n_samples, 1)

    22 features per timestep:
      [0]     past consumption (normalized 0-1)
      [1:8]   day-of-week one-hot (7)
      [8:20]  month one-hot (12)
      [20]    7-day rolling avg (normalized)
      [21]    30-day rolling avg (normalized)
    """
    if not consumption_series or len(consumption_series) <= seq_len:
        return torch.empty((0, seq_len, 22), dtype=torch.float32), torch.empty((0, 1), dtype=torch.float32)

    # Sort chronological
    sorted_series = sorted(
        [(_parse_date(d), float(q)) for d, q in consumption_series],
        key=lambda item: item[0],
    )

    dates = [item[0] for item in sorted_series]
    quantities = np.array([max(0.0, item[1]) for item in sorted_series], dtype=np.float32)
    n = len(quantities)

    # Global normalization factor for stability
    max_q = float(np.max(quantities))
    denom = max_q if max_q > 0.0 else 1.0
    norm_q = quantities / denom

    # Precompute rolling averages
    roll_7 = np.zeros(n, dtype=np.float32)
    roll_30 = np.zeros(n, dtype=np.float32)

    for i in range(n):
        # 7-day rolling average of consumption up to i (inclusive)
        start_7 = max(0, i - 6)
        roll_7[i] = float(np.mean(quantities[start_7 : i + 1])) / denom

        # 30-day rolling average of consumption up to i (inclusive)
        start_30 = max(0, i - 29)
        roll_30[i] = float(np.mean(quantities[start_30 : i + 1])) / denom

    # Precompute timestep feature vectors
    # vector shape: (n, 22)
    timesteps = np.zeros((n, 22), dtype=np.float32)
    for i in range(n):
        d = dates[i]
        # [0] past consumption
        timesteps[i, 0] = norm_q[i]

        # [1:8] day-of-week one-hot (Monday=0 to Sunday=6)
        dow = d.weekday()  # 0 to 6
        timesteps[i, 1 + dow] = 1.0

        # [8:20] month one-hot (Jan=1 to Dec=12)
        month = d.month - 1  # 0 to 11
        timesteps[i, 8 + month] = 1.0

        # [20] 7-day rolling avg
        timesteps[i, 20] = roll_7[i]

        # [21] 30-day rolling avg
        timesteps[i, 21] = roll_30[i]

    # Generate sliding windows: target is quantity at index (i + seq_len)
    # y target is not normalized or normalized? The prompt states:
    # "y shape (n_samples, 1)"
    # We train predicting target quantity directly (float).
    n_samples = n - seq_len
    X = np.zeros((n_samples, seq_len, 22), dtype=np.float32)
    y = np.zeros((n_samples, 1), dtype=np.float32)

    for i in range(n_samples):
        X[i] = timesteps[i : i + seq_len]
        y[i, 0] = quantities[i + seq_len]

    return torch.from_numpy(X), torch.from_numpy(y)


def build_inference_input(
    recent_history: List[Tuple[Union[date, str], Union[int, float]]],
    seq_len: int = 7,
) -> torch.Tensor:
    """
    Return (1, seq_len, 22) tensor for prediction.
    If recent_history has fewer than seq_len items, pads with 0 consumption.
    Uses the last seq_len entries.
    """
    if not recent_history:
        # Default placeholder history
        today = date.today()
        recent_history = [(today, 0.0)]

    sorted_series = sorted(
        [(_parse_date(d), float(q)) for d, q in recent_history],
        key=lambda item: item[0],
    )

    # Ensure at least seq_len items
    if len(sorted_series) < seq_len:
        earliest_date = sorted_series[0][0]
        padding_needed = seq_len - len(sorted_series)
        pad = [
            (earliest_date, 0.0)
            for _ in range(padding_needed)
        ]
        sorted_series = pad + sorted_series

    # Take last seq_len items
    window = sorted_series[-seq_len:]
    dates = [item[0] for item in window]
    quantities = np.array([max(0.0, item[1]) for item in window], dtype=np.float32)

    # Max normalization based on recent history
    all_quantities = np.array([max(0.0, item[1]) for item in sorted_series], dtype=np.float32)
    max_q = float(np.max(all_quantities))
    denom = max_q if max_q > 0.0 else 1.0
    norm_q = quantities / denom

    X = np.zeros((1, seq_len, 22), dtype=np.float32)
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

    return torch.from_numpy(X)

"""Federated averaging aggregation algorithm (FedAvg)."""
from typing import List, Dict
import torch


def federated_average(
    state_dicts: List[Dict[str, torch.Tensor]],
    sample_counts: List[int],
) -> Dict[str, torch.Tensor]:
    """
    Weighted FedAvg across client/node state_dicts. Handles arbitrary tensor dimensions (e.g. 3D LSTM weights).
    Returns a new state_dict with the same keys and shapes as inputs.
    """
    if not state_dicts:
        raise ValueError("Cannot perform federated averaging on empty state_dicts list")

    if len(state_dicts) == 1:
        return {k: v.clone() for k, v in state_dicts[0].items()}

    # Calculate total weight
    total_samples = sum(sample_counts)
    if total_samples <= 0:
        # Uniform average if counts are all 0
        weights = [1.0 / len(state_dicts)] * len(state_dicts)
    else:
        weights = [c / total_samples for c in sample_counts]

    ref_keys = list(state_dicts[0].keys())
    averaged_state_dict: Dict[str, torch.Tensor] = {}

    for k in ref_keys:
        # Check dtype of parameter
        sample_tensor = state_dicts[0][k]
        if not sample_tensor.is_floating_point():
            # For non-floating point buffers (e.g. integer steps), take the first or rounded average
            averaged_state_dict[k] = sample_tensor.clone()
            continue

        accum = torch.zeros_like(sample_tensor, dtype=sample_tensor.dtype)
        for state_dict, weight in zip(state_dicts, weights):
            accum += state_dict[k] * weight
        averaged_state_dict[k] = accum

    return averaged_state_dict

"""Local node training routine for Federated Learning."""
from typing import Optional, Dict, Any, List, Tuple, Union
from datetime import date
import copy
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import TensorDataset, DataLoader
from app.ml.model import RegionalDemandNet
from app.ml.features import build_feature_tensors


def train_local_model(
    base_state_dict: Optional[Dict[str, torch.Tensor]],
    consumption_series: List[Tuple[Any, Union[int, float]]],
    epochs: int = 15,
    batch_size: int = 32,
    lr: float = 0.005,
) -> Tuple[Dict[str, torch.Tensor], Dict[str, Any]]:
    """
    Train local RegionalDemandNet model on node consumption series.
    base_state_dict: warm start state dict (None = random initialization)
    Returns: (updated_state_dict, metrics_dict)
    - 80/20 train/val split
    - Adam optimizer
    - Early stop if validation loss doesn't improve for 3 epochs
    """
    model = RegionalDemandNet()
    if base_state_dict is not None:
        model.load_state_dict(base_state_dict)

    X, y = build_feature_tensors(consumption_series, seq_len=7)
    n_samples = len(X)

    if n_samples < 4:
        # Too few samples to train meaningful split; return base or init model state
        return model.state_dict(), {
            "train_loss": 0.0,
            "val_loss": 0.0,
            "epochs_trained": 0,
            "sample_count": n_samples,
        }

    # 80/20 train/val split
    n_train = max(1, int(n_samples * 0.8))
    X_train, y_train = X[:n_train], y[:n_train]
    X_val, y_val = X[n_train:], y[n_train:]

    if len(X_val) == 0:
        X_val, y_val = X_train, y_train

    train_dataset = TensorDataset(X_train, y_train)
    val_dataset = TensorDataset(X_val, y_val)

    train_loader = DataLoader(train_dataset, batch_size=min(batch_size, len(train_dataset)), shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=min(batch_size, len(val_dataset)), shuffle=False)

    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=lr)

    best_val_loss = float("inf")
    best_state_dict = copy.deepcopy(model.state_dict())
    patience = 3
    patience_counter = 0
    actual_epochs = 0
    last_train_loss = 0.0

    for epoch in range(epochs):
        actual_epochs += 1
        model.train()
        total_train_loss = 0.0
        train_batches = 0

        for batch_x, batch_y in train_loader:
            optimizer.zero_grad()
            preds = model(batch_x)
            loss = criterion(preds, batch_y)
            loss.backward()
            optimizer.step()
            total_train_loss += loss.item()
            train_batches += 1

        last_train_loss = total_train_loss / max(1, train_batches)

        # Validation
        model.eval()
        total_val_loss = 0.0
        val_batches = 0
        with torch.no_grad():
            for val_x, val_y in val_loader:
                v_preds = model(val_x)
                v_loss = criterion(v_preds, val_y)
                total_val_loss += v_loss.item()
                val_batches += 1

        avg_val_loss = total_val_loss / max(1, val_batches)

        if avg_val_loss < best_val_loss:
            best_val_loss = avg_val_loss
            best_state_dict = copy.deepcopy(model.state_dict())
            patience_counter = 0
        else:
            patience_counter += 1
            if patience_counter >= patience:
                break

    metrics = {
        "train_loss": round(last_train_loss, 4),
        "val_loss": round(best_val_loss if best_val_loss != float("inf") else last_train_loss, 4),
        "epochs_trained": actual_epochs,
        "sample_count": n_samples,
    }

    return best_state_dict, metrics

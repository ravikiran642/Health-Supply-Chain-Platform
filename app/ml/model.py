"""Neural network architecture for Federated Learning regional demand forecasting."""
import hashlib
import torch
import torch.nn as nn


class RegionalDemandNet(nn.Module):
    def __init__(self, n_features: int = 32, hidden_dim: int = 64):
        super().__init__()
        self.lstm = nn.LSTM(
            input_size=n_features,
            hidden_size=hidden_dim,
            num_layers=2,
            batch_first=True,
            dropout=0.1,
        )
        self.head = nn.Sequential(
            nn.Linear(hidden_dim, 32),
            nn.ReLU(),
            nn.Linear(32, 1),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        out, _ = self.lstm(x)
        return self.head(out[:, -1, :])


ARCHITECTURE_HASH = hashlib.sha256(
    b"RegionalDemandNet|LSTM|in=32|h=64|l=2|out=1"
).hexdigest()

"""Leakage-aware splitting utilities."""
from __future__ import annotations

import pandas as pd


def temporal_split(
    frame: pd.DataFrame,
    train_fraction: float = 0.70,
    val_fraction: float = 0.15,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Split an already time-sorted frame into train/validation/test blocks."""
    if train_fraction <= 0 or val_fraction <= 0 or train_fraction + val_fraction >= 1:
        raise ValueError("Fractions must be positive and leave a non-empty test block")
    n = len(frame)
    train_end = int(n * train_fraction)
    val_end = int(n * (train_fraction + val_fraction))
    return (
        frame.iloc[:train_end].copy(),
        frame.iloc[train_end:val_end].copy(),
        frame.iloc[val_end:].copy(),
    )

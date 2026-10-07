"""Leakage-aware temporal and station holdout splitting utilities."""
from __future__ import annotations

import pandas as pd


def temporal_split(
    frame: pd.DataFrame,
    train_fraction: float = 0.70,
    val_fraction: float = 0.15,
    *,
    timestamp_col: str | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Split a time-ordered frame into non-empty train/validation/test blocks.

    If ``timestamp_col`` is supplied, monotonic ordering is enforced. P2/P3 will
    freeze whether a global timestamp cutoff or station-aware split is used.
    """
    if train_fraction <= 0 or val_fraction <= 0 or train_fraction + val_fraction >= 1:
        raise ValueError("Fractions must be positive and leave a non-empty test block")
    if len(frame) < 3:
        raise ValueError("At least three rows are required")
    if timestamp_col is not None:
        if timestamp_col not in frame.columns:
            raise KeyError(timestamp_col)
        ts = pd.to_datetime(frame[timestamp_col])
        if not ts.is_monotonic_increasing:
            raise ValueError("frame must be sorted by timestamp before splitting")
    n = len(frame)
    train_end = max(1, int(n * train_fraction))
    val_end = max(train_end + 1, int(n * (train_fraction + val_fraction)))
    val_end = min(val_end, n - 1)
    return (
        frame.iloc[:train_end].copy(),
        frame.iloc[train_end:val_end].copy(),
        frame.iloc[val_end:].copy(),
    )


def leave_one_station_out(
    frame: pd.DataFrame,
    station_col: str,
    held_out_station: str,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return development and held-out-site frames with strict station isolation."""
    if station_col not in frame.columns:
        raise KeyError(station_col)
    stations = set(frame[station_col].dropna().astype(str))
    if str(held_out_station) not in stations:
        raise ValueError(f"Unknown held-out station: {held_out_station}")
    station_as_str = frame[station_col].astype(str)
    dev = frame.loc[station_as_str != str(held_out_station)].copy()
    held = frame.loc[station_as_str == str(held_out_station)].copy()
    if dev.empty or held.empty:
        raise ValueError("Both development and held-out partitions must be non-empty")
    return dev, held

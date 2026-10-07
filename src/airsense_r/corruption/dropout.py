"""Observation-dropout utilities applied to chronological sensor streams."""
from __future__ import annotations

import numpy as np
import pandas as pd


def random_feature_dropout(
    frame: pd.DataFrame,
    columns: list[str],
    probability: float,
    seed: int = 42,
) -> pd.DataFrame:
    """Apply MCAR-style feature dropout to a stream before window construction."""
    if not 0 <= probability <= 1:
        raise ValueError("probability must be between 0 and 1")
    out = frame.copy()
    rng = np.random.default_rng(seed)
    mask = rng.random((len(out), len(columns))) < probability
    values = out[columns].to_numpy(copy=True, dtype=float)
    values[mask] = np.nan
    out.loc[:, columns] = values
    return out


def whole_variable_dropout(frame: pd.DataFrame, column: str) -> pd.DataFrame:
    """Return a copy with one complete sensor/channel unavailable."""
    out = frame.copy()
    out[column] = np.nan
    return out


def contiguous_outage(
    frame: pd.DataFrame,
    columns: list[str],
    start: int,
    length: int,
) -> pd.DataFrame:
    """Remove selected channels for one contiguous run of rows.

    The utility operates on the underlying timeline. Forecast targets should be
    stored separately or excluded from ``columns`` so they remain uncorrupted.
    """
    if start < 0 or length <= 0:
        raise ValueError("start must be non-negative and length must be positive")
    if start + length > len(frame):
        raise ValueError("outage extends beyond frame length")
    out = frame.copy()
    out.loc[out.index[start:start + length], columns] = np.nan
    return out

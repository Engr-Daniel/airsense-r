"""Observation-dropout utilities."""
from __future__ import annotations

import numpy as np
import pandas as pd


def random_feature_dropout(
    frame: pd.DataFrame,
    columns: list[str],
    probability: float,
    seed: int = 42,
) -> pd.DataFrame:
    """Return a copy with MCAR-style feature dropout applied to selected columns."""
    if not 0 <= probability <= 1:
        raise ValueError("probability must be between 0 and 1")
    out = frame.copy()
    rng = np.random.default_rng(seed)
    mask = rng.random((len(out), len(columns))) < probability
    values = out[columns].to_numpy(copy=True)
    values[mask] = np.nan
    out.loc[:, columns] = values
    return out


def whole_variable_dropout(frame: pd.DataFrame, column: str) -> pd.DataFrame:
    """Return a copy with one complete sensor/channel unavailable."""
    out = frame.copy()
    out[column] = np.nan
    return out

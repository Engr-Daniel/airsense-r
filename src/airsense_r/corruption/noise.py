"""Measurement-noise utilities."""
from __future__ import annotations

import numpy as np
import pandas as pd


def gaussian_relative_noise(
    frame: pd.DataFrame,
    columns: list[str],
    fraction_of_std: float,
    seed: int = 42,
) -> pd.DataFrame:
    """Add Gaussian noise scaled by each column's observed standard deviation."""
    if fraction_of_std < 0:
        raise ValueError("fraction_of_std must be non-negative")
    out = frame.copy()
    rng = np.random.default_rng(seed)
    for col in columns:
        sigma = float(out[col].std(skipna=True)) * fraction_of_std
        if sigma == 0 or np.isnan(sigma):
            continue
        noise = rng.normal(0.0, sigma, size=len(out))
        out[col] = out[col] + noise
    return out

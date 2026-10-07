"""Measurement-noise utilities with train-derived reference scales."""
from __future__ import annotations

from collections.abc import Mapping

import numpy as np
import pandas as pd


def fit_noise_scales(
    train_frame: pd.DataFrame,
    columns: list[str],
) -> dict[str, float]:
    """Estimate per-feature standard deviations using training data only.

    These scales are frozen and reused when corrupting validation/test streams so
    corruption severity never depends on held-out statistics.
    """
    missing = [c for c in columns if c not in train_frame.columns]
    if missing:
        raise KeyError(f"Columns missing from training frame: {missing}")
    scales: dict[str, float] = {}
    for col in columns:
        value = float(train_frame[col].std(skipna=True))
        scales[col] = 0.0 if np.isnan(value) else value
    return scales


def gaussian_relative_noise(
    frame: pd.DataFrame,
    columns: list[str],
    fraction_of_std: float,
    reference_scales: Mapping[str, float],
    seed: int = 42,
) -> pd.DataFrame:
    """Add zero-mean Gaussian noise using frozen training-derived scales."""
    if fraction_of_std < 0:
        raise ValueError("fraction_of_std must be non-negative")
    missing_scales = [c for c in columns if c not in reference_scales]
    if missing_scales:
        raise KeyError(f"Missing reference scales for: {missing_scales}")
    out = frame.copy()
    rng = np.random.default_rng(seed)
    for col in columns:
        sigma = float(reference_scales[col]) * fraction_of_std
        if sigma <= 0 or np.isnan(sigma):
            continue
        out[col] = out[col] + rng.normal(0.0, sigma, size=len(out))
    return out

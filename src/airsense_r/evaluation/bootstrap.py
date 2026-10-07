"""Dependence-aware paired uncertainty utilities for time-series errors."""
from __future__ import annotations

import numpy as np


def paired_block_bootstrap_mae_difference(
    y_true,
    pred_a,
    pred_b,
    *,
    block_length: int = 24,
    n_bootstrap: int = 1000,
    seed: int = 42,
    confidence: float = 0.95,
) -> dict[str, float]:
    """Estimate a CI for MAE(A)-MAE(B) using moving-block resampling.

    Positive values mean model A has larger MAE. Predictions must correspond to
    identical station-timestamp targets. This is a pragmatic dependence-aware
    analysis, not a claim that all temporal/cross-station dependence is removed.
    """
    y = np.asarray(y_true, dtype=float)
    a = np.asarray(pred_a, dtype=float)
    b = np.asarray(pred_b, dtype=float)
    if not (len(y) == len(a) == len(b)) or len(y) == 0:
        raise ValueError("Inputs must have the same non-zero length")
    if block_length <= 0 or block_length > len(y):
        raise ValueError("block_length must be within [1, n]")
    if n_bootstrap <= 0:
        raise ValueError("n_bootstrap must be positive")
    if not 0 < confidence < 1:
        raise ValueError("confidence must be between 0 and 1")

    err_diff = np.abs(y - a) - np.abs(y - b)
    point = float(err_diff.mean())
    rng = np.random.default_rng(seed)
    n = len(err_diff)
    starts = np.arange(0, n - block_length + 1)
    reps = np.empty(n_bootstrap, dtype=float)
    blocks_needed = int(np.ceil(n / block_length))
    for i in range(n_bootstrap):
        chosen = rng.choice(starts, size=blocks_needed, replace=True)
        sample = np.concatenate([err_diff[s:s + block_length] for s in chosen])[:n]
        reps[i] = sample.mean()
    alpha = 1.0 - confidence
    lo, hi = np.quantile(reps, [alpha / 2.0, 1.0 - alpha / 2.0])
    return {"difference": point, "ci_low": float(lo), "ci_high": float(hi)}

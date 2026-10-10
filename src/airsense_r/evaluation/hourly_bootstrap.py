"""Paired calendar-hour bootstrap preserving missing targets and shared time shocks."""
from __future__ import annotations

import numpy as np
import pandas as pd

from airsense_r.evaluation.selection import validate_predictions


def paired_hourly_intervals(predictions: pd.DataFrame, selected: str, *,
                            start: str, end: str, block_hours: int = 24,
                            n_bootstrap: int = 2000, seed: int = 424242,
                            confidence: float = 0.95) -> dict:
    """Bootstrap equal-station MAE differences and selected-family regret.

    All stations share each sampled calendar, retaining spatially shared shocks.
    Missing target hours remain NaN, not compressed into an observed-row timeline.
    Conditional on the fitted seed set; not a bootstrap of training uncertainty.
    """
    p = validate_predictions(predictions)
    if n_bootstrap < 1 or not 0 < confidence < 1:
        raise ValueError("Invalid bootstrap settings")
    calendar = pd.date_range(start, end, freq="h")
    if not 1 <= block_hours <= len(calendar):
        raise ValueError("Invalid calendar block length")
    if not p.target_timestamp.isin(calendar).all():
        raise ValueError("Prediction timestamps outside declared hourly calendar")
    models, stations = sorted(p.model.unique()), sorted(p.station.unique())
    if selected not in models:
        raise ValueError("Unknown selected model")
    p["absolute_error"] = np.abs(p.y_true - p.y_pred)
    mean_error = p.groupby(["model", "station", "target_timestamp"]).absolute_error.mean()
    errors = np.empty((len(models), len(stations), len(calendar)))
    for i, m in enumerate(models):
        for j, s in enumerate(stations):
            errors[i, j] = mean_error.loc[m, s].reindex(calendar).to_numpy()
    valid = np.isfinite(errors)
    values = np.nan_to_num(errors)
    if not valid.all(axis=0).any(axis=1).all():
        raise ValueError("Each station needs observed targets for every candidate")
    point = (values.sum(axis=2) / valid.sum(axis=2)).mean(axis=1)
    # Prefix sums make each replicate O(number of blocks), not O(all hourly rows).
    sums = np.concatenate([np.zeros((*values.shape[:2], 1)), values.cumsum(axis=2)], axis=2)
    counts = np.concatenate([np.zeros((*values.shape[:2], 1)), valid.cumsum(axis=2)], axis=2)
    lengths = np.full(int(np.ceil(len(calendar) / block_hours)), block_hours)
    lengths[-1] = len(calendar) - (len(lengths) - 1) * block_hours
    rng = np.random.default_rng(seed)
    reps = []
    for _ in range(n_bootstrap):
        starts = rng.integers(0, len(calendar) - block_hours + 1, size=len(lengths))
        stops = starts + lengths
        denominator = (counts[:, :, stops] - counts[:, :, starts]).sum(axis=2)
        if (denominator == 0).any():
            raise ValueError("Bootstrap replicate has a station with no observed targets")
        numerator = (sums[:, :, stops] - sums[:, :, starts]).sum(axis=2)
        reps.append((numerator / denominator).mean(axis=1))
    reps = np.asarray(reps)
    chosen = models.index(selected)
    alpha = (1 - confidence) / 2

    def interval(v: np.ndarray, estimate: float) -> dict:
        low, high = np.quantile(v, [alpha, 1-alpha])
        return {"estimate": float(estimate), "ci_low": float(low), "ci_high": float(high)}

    return {"method": "paired_calendar_moving_block_bootstrap", "block_hours": block_hours,
            "replicates": n_bootstrap, "seed": seed, "confidence": confidence,
            "selected_family": selected, "seed_uncertainty": "conditional_on_fitted_seed_set",
            "differences": {m: interval(reps[:, chosen]-reps[:, i], point[chosen]-point[i])
                            for i, m in enumerate(models)},
            "selection_regret": interval(reps[:, chosen]-reps.min(axis=1), point[chosen]-point.min())}

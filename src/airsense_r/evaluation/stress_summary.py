"""Paired stress comparisons with equal-realization/station aggregation."""
from __future__ import annotations

import json
import numpy as np
import pandas as pd


def rank_tau(left: np.ndarray, right: np.ndarray) -> float | None:
    """Kendall tau-b of numerical model scores; not a practical-equivalence test."""
    i, j = np.triu_indices(len(left), 1)
    a, b = np.sign(left[i]-left[j]), np.sign(right[i]-right[j])
    denominator = np.sqrt(np.count_nonzero(a)*np.count_nonzero(b))
    return float(np.sum(a*b)/denominator) if denominator else None


def stress_intervals(clean: np.ndarray, stress: np.ndarray, models: list[str], selected: str,
                     stations: list[str], config: dict) -> dict:
    """Bootstrap [realization, model, station, calendar-hour] mean seed errors.

    Masks may differ across corruption realizations (outage-affected windows),
    but clean/stress and all models must share each realization's target mask.
    Aggregate each realization's station error before averaging realizations.
    """
    if clean.shape != stress.shape or clean.ndim != 4:
        raise ValueError("Expected aligned realization/model/station/hour arrays")
    valid = np.isfinite(clean)
    if (not np.array_equal(valid, np.isfinite(stress))
            or not np.array_equal(valid, np.broadcast_to(valid[:, :1], valid.shape))
            or not valid.any(axis=-1).all()):
        raise ValueError("Missing/misaligned model targets or empty station realization")
    if clean.shape[1:3] != (len(models), len(stations)):
        raise ValueError("Model/station axis mismatch")
    settings = config["uncertainty"]
    block = settings["block_length_hours"]
    hours = clean.shape[-1]
    if not 1 <= block <= hours:
        raise ValueError("Invalid bootstrap block length")
    values = np.stack([np.nan_to_num(clean), np.nan_to_num(stress)])
    prefix = np.concatenate([np.zeros((*values.shape[:-1], 1)), values.cumsum(axis=-1)], axis=-1)
    counts = np.concatenate([np.zeros((*valid.shape[:-1], 1)), valid.cumsum(axis=-1)], axis=-1)
    point_station = (values.sum(axis=-1) / valid.sum(axis=-1)).mean(axis=1)
    point = point_station.mean(axis=-1)
    lengths = np.full(int(np.ceil(hours/block)), block)
    lengths[-1] = hours - (len(lengths)-1)*block
    rng = np.random.default_rng(config["seeds"]["bootstrap"])
    replicates = []
    for _ in range(settings["n_bootstrap"]):
        starts = rng.integers(0, hours-block+1, size=len(lengths))
        ends = starts+lengths
        denominator = (counts[..., ends]-counts[..., starts]).sum(axis=-1)
        if (denominator == 0).any():
            # Sparse affected-window estimands can produce empty block samples.
            # Do not silently redraw or change weights to force an interval.
            return {"available": False, "reason": "bootstrap replicate has empty affected station/realization",
                    "block_hours": block, "replicates": settings["n_bootstrap"]}
        numerator = (prefix[..., ends]-prefix[..., starts]).sum(axis=-1)
        replicates.append((numerator/denominator).mean(axis=1))
    reps_station = np.asarray(replicates)
    reps = reps_station.mean(axis=-1)
    chosen = models.index(selected)
    alpha = (1-settings["confidence"])/2
    def interval(samples, estimate):
        lo, hi = np.quantile(samples, [alpha, 1-alpha])
        return {"estimate": float(estimate), "ci_low": float(lo), "ci_high": float(hi)}
    return {"available": True, "method": "paired_calendar_moving_block_bootstrap",
        "block_hours": block, "replicates": settings["n_bootstrap"], "confidence": settings["confidence"],
        "seed": config["seeds"]["bootstrap"], "seed_uncertainty": "conditional_on_fitted_training_and_corruption_seed_sets",
        "selected_family": selected,
        "differences": {m: interval(reps[:, 1, chosen]-reps[:, 1, i], point[1, chosen]-point[1, i]) for i, m in enumerate(models)},
        "selection_regret": interval(reps[:, 1, chosen]-reps[:, 1].min(axis=1), point[1, chosen]-point[1].min()),
        "station_changes": {m: {s: interval(reps_station[:, 1, i, j]-reps_station[:, 0, i, j],
                    point_station[1, i, j]-point_station[0, i, j]) for j, s in enumerate(stations)} for i, m in enumerate(models)}}


def reliability_summary(rows: pd.DataFrame, selected: str, threshold: float) -> dict:
    """Equal training-seed, realization and station metrics with matched clean RPD."""
    columns = ["mae", "rmse", "r2", "clean_mae", "clean_rmse", "clean_r2"]
    # First training seeds, then corruption realizations, then stations.
    stations = rows.groupby(["model", "corruption_seed", "station"])[columns].mean().groupby(["model", "station"]).mean()
    aggregate = stations.groupby("model").mean().sort_index()
    models = aggregate.index.tolist()
    scores, clean = aggregate.mae.to_numpy(), aggregate.clean_mae.to_numpy()
    aggregate["rpd_percent"] = np.where(clean != 0, (scores-clean)/clean*100, np.nan)
    aggregate["clean_rank"] = aggregate.clean_mae.rank(method="average")
    aggregate["stress_rank"] = aggregate.mae.rank(method="average")
    aggregate["rank_change"] = aggregate.stress_rank-aggregate.clean_rank
    oracle = [models[i] for i in np.flatnonzero(scores == scores.min())]
    near = [models[i] for i in np.flatnonzero(scores <= scores.min()+threshold)]
    chosen = float(aggregate.loc[selected, "mae"])
    return {"selected_family": selected, "test_oracle_families": oracle,
        "selected_is_numerical_best": selected in oracle, "selected_within_practical_near_tie": selected in near,
        "near_ties": near, "threshold": threshold, "selection_regret": chosen-float(scores.min()),
        "kendall_tau_b": rank_tau(clean, scores),
        "metrics": json.loads(aggregate.reset_index().to_json(orient="records", double_precision=15))}

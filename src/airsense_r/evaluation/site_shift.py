"""Station-specific selection policies and paired LOSO uncertainty."""
from __future__ import annotations

import numpy as np
import pandas as pd

from airsense_r.evaluation.selection import metric_tables, validate_predictions


def rank_agreement(left: np.ndarray, right: np.ndarray) -> float | None:
    """Kendall tau-b of paired model scores; all-tied rankings are undefined."""
    i, j = np.triu_indices(len(left), 1)
    a, b = np.sign(left[i]-left[j]), np.sign(right[i]-right[j])
    denominator = np.sqrt(np.count_nonzero(a) * np.count_nonzero(b))
    return float(np.sum(a*b) / denominator) if denominator else None


def summarize_sites(predictions: pd.DataFrame, decisions: dict, config: dict) -> dict:
    """Compare each fold's fixed validation choice with held-out test evidence."""
    p = validate_predictions(predictions)
    if set(p.partition) != {"test"} or set(p.station) != set(decisions):
        raise ValueError("LOSO summary needs test predictions for every declared fold")
    models, stations = sorted(p.model.unique()), sorted(decisions)
    if set(models) != set(config["models"]["candidates"]):
        raise ValueError("Incomplete LOSO candidates")
    for model, group in p.groupby("model"):
        expected = {-1} if model == "persistence" else set(config["seeds"]["training"])
        if set(group.seed) != expected:
            raise ValueError("Incomplete LOSO training seeds")
    calendar = pd.date_range(config["data"]["test_target_start"], config["data"]["test_target_end"], freq="h")
    if not p.target_timestamp.isin(calendar).all():
        raise ValueError("LOSO targets outside frozen test calendar")
    p["absolute_error"] = np.abs(p.y_true - p.y_pred)
    errors = p.groupby(["station", "model", "target_timestamp"]).absolute_error.mean()
    values = np.array([[errors.loc[s, m].reindex(calendar).to_numpy() for m in models] for s in stations])
    valid = np.isfinite(values)
    if not valid.any(axis=2).all():
        raise ValueError("A LOSO station has no eligible targets")
    values = np.nan_to_num(values)
    chosen = np.array([models.index(decisions[s]["selected_family"]) for s in stations])
    rows = np.arange(len(stations))
    point = values.sum(axis=2) / valid.sum(axis=2)
    settings = config["uncertainty"]
    block = settings["block_length_hours"]
    if not 1 <= block <= len(calendar) or settings["n_bootstrap"] < 1:
        raise ValueError("Invalid LOSO bootstrap settings")
    sums = np.concatenate([np.zeros((*values.shape[:2], 1)), values.cumsum(axis=2)], axis=2)
    counts = np.concatenate([np.zeros((*values.shape[:2], 1)), valid.cumsum(axis=2)], axis=2)
    lengths = np.full(int(np.ceil(len(calendar) / block)), block)
    lengths[-1] = len(calendar) - (len(lengths) - 1) * block
    rng = np.random.default_rng(config["seeds"]["bootstrap"])
    replicates = []
    for _ in range(settings["n_bootstrap"]):
        starts = rng.integers(0, len(calendar) - block + 1, len(lengths))
        stops = starts + lengths
        denominator = (counts[:, :, stops] - counts[:, :, starts]).sum(axis=2)
        if (denominator == 0).any():
            raise ValueError("A bootstrap station has no observed targets")
        replicates.append((sums[:, :, stops] - sums[:, :, starts]).sum(axis=2) / denominator)
    reps = np.array(replicates)  # replicate, station, family
    alpha = (1 - settings["confidence"]) / 2

    def interval(estimate, samples):
        low, high = np.quantile(samples, [alpha, 1-alpha])
        return {"estimate": float(estimate), "ci_low": float(low), "ci_high": float(high)}

    selected_point = point[rows, chosen]
    selected_reps = reps[:, rows, chosen]
    regret_point = selected_point - point.min(axis=1)
    regret_reps = selected_reps - reps.min(axis=2)
    threshold = config["near_tie"]["absolute_threshold_ug_m3"]
    station_reports = {}
    for j, station in enumerate(stations):
        validation = pd.Series(decisions[station]["validation_mae"]).reindex(models)
        if validation.isna().any():
            raise ValueError("Incomplete fold validation scores")
        test_scores = pd.Series(point[j], index=models)
        # Average numerical ranks describe ties without imposing a test-time choice.
        station_reports[station] = {
            "selected_family": decisions[station]["selected_family"],
            "validation_mae": validation.to_dict(), "test_mae": test_scores.to_dict(),
            "validation_ranks": validation.rank().to_dict(), "test_ranks": test_scores.rank().to_dict(),
            "kendall_tau_b": rank_agreement(validation.to_numpy(), test_scores.to_numpy()),
            "numerical_winner_retained": bool(selected_point[j] == point[j].min()),
            "within_practical_near_tie": bool(regret_point[j] <= threshold),
            "selection_regret": interval(regret_point[j], regret_reps[:, j]),
            "differences": {m: interval(selected_point[j]-point[j, i], selected_reps[:, j]-reps[:, j, i])
                            for i, m in enumerate(models)}}
    _, aggregate = metric_tables(p)
    return {"phase": "P7", "estimand": "cross_site_generalization_not_causal_penalty",
        "stations": station_reports, "fixed_family_metrics": aggregate.to_dict(orient="records"),
        "selected_policy_mae": float(selected_point.mean()),
        "mean_station_selection_regret": interval(regret_point.mean(), regret_reps.mean(axis=1)),
        "policy_minus_fixed_family": {
            m: interval((selected_point-point[:, i]).mean(), (selected_reps-reps[:, :, i]).mean(axis=1))
            for i, m in enumerate(models)},
        "uncertainty": {"method": "paired_calendar_moving_block_bootstrap", "block_hours": block,
            "replicates": settings["n_bootstrap"], "confidence": settings["confidence"],
            "seed": config["seeds"]["bootstrap"], "conditional_on": "fitted_seeds_and_observed_stations"},
        "practical_threshold_ug_m3": threshold}

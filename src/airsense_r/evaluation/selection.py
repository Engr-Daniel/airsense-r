"""Aligned prediction validation and the frozen clean-validation selection rule."""
from __future__ import annotations

import numpy as np
import pandas as pd

from airsense_r.evaluation.metrics import regression_metrics

KEYS = ["station", "target_timestamp"]


def validate_predictions(predictions: pd.DataFrame) -> pd.DataFrame:
    """Reject unequal targets, duplicate keys, mixed partitions and invalid numbers."""
    required = {*KEYS, "model", "seed", "partition", "y_true", "y_pred"}
    if not required.issubset(predictions) or predictions.empty:
        raise ValueError("Missing prediction fields or empty predictions")
    p = predictions.copy()
    p["target_timestamp"] = pd.to_datetime(p.target_timestamp)
    if p[list(required)].isna().any().any() or p.partition.nunique() != 1:
        raise ValueError("Missing values or mixed partitions")
    if not np.isfinite(p[["y_true", "y_pred"]].to_numpy(dtype=float)).all():
        raise ValueError("Nonfinite predictions or targets")
    baseline = None
    for _, group in p.groupby(["model", "seed"], sort=True):
        if group.duplicated(KEYS).any():
            raise ValueError("Duplicate prediction target")
        target = group.sort_values(KEYS)[[*KEYS, "y_true"]].reset_index(drop=True)
        if baseline is None:
            baseline = target
        elif not baseline.equals(target):
            raise ValueError("Candidates/seeds must use identical target keys and labels")
    return p


def metric_tables(predictions: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Average metrics across seeds within each station, then weight stations equally."""
    p = validate_predictions(predictions)
    rows = []
    for (model, seed, station), g in p.groupby(["model", "seed", "station"], sort=True):
        values = regression_metrics(g.y_true, g.y_pred)
        rows.append({"model": model, "seed": int(seed), "station": station,
                     "n": len(g), **values})
    per_seed = pd.DataFrame(rows)
    station = per_seed.groupby(["model", "station"])[["mae", "rmse", "r2"]].mean()
    aggregate = station.groupby("model").mean().reset_index()
    return per_seed, aggregate


def select_family(predictions: pd.DataFrame, config: dict) -> dict:
    """Choose from validation only, enforcing complete candidates and frozen seeds."""
    p = validate_predictions(predictions)
    if set(p.partition) != {"validation"}:
        raise ValueError("Family selection accepts clean validation only")
    candidates = config["models"]["candidates"]
    if set(p.model) != set(candidates):
        raise ValueError("Missing or unexpected model family")
    for model, group in p.groupby("model"):
        expected = {-1} if model == "persistence" else set(config["seeds"]["training"])
        if set(group.seed) != expected:
            raise ValueError("Incomplete training seeds")
    start, end = (pd.Timestamp(config["data"][f"validation_target_{x}"]) for x in ("start", "end"))
    if not p.target_timestamp.between(start, end).all():
        raise ValueError("Selection targets outside validation period")
    _, aggregate = metric_tables(p)
    scores = dict(zip(aggregate.model, aggregate.mae.astype(float)))
    best = min(scores.values())
    threshold = config["near_tie"]["absolute_threshold_ug_m3"]
    tied = [m for m in config["models"]["near_tie_tiebreak_order"] if scores[m] <= best + threshold]
    return {"selected_family": tied[0], "validation_mae": scores,
            "near_ties": tied, "threshold": threshold, "partition": "validation",
            "rule": "mean_seed_metric_within_station_then_equal_station_mae"}

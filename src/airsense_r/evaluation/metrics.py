"""Evaluation metrics for AirSense-R."""
from __future__ import annotations

import numpy as np
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


def regression_metrics(y_true, y_pred) -> dict[str, float]:
    """Return core regression metrics."""
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)
    return {
        "mae": float(mean_absolute_error(y_true, y_pred)),
        "rmse": float(np.sqrt(mean_squared_error(y_true, y_pred))),
        "r2": float(r2_score(y_true, y_pred)),
    }


def relative_performance_degradation(clean_value: float, degraded_value: float) -> float:
    """Return percentage degradation for a lower-is-better metric."""
    if clean_value <= 0:
        raise ValueError("clean_value must be positive")
    return (degraded_value - clean_value) / clean_value * 100.0

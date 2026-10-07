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


def selection_regret(selected_value: float, oracle_best_value: float) -> float:
    """Extra error paid by the pre-selected model relative to the test oracle.

    ``selected_value`` is the stressed-test metric for the model chosen using
    clean validation data. ``oracle_best_value`` is the best stressed-test metric
    among all candidate models and is descriptive only.
    """
    if selected_value < 0 or oracle_best_value < 0:
        raise ValueError("metric values must be non-negative")
    regret = selected_value - oracle_best_value
    if regret < -1e-12:
        raise ValueError("oracle_best_value cannot exceed selected_value")
    return max(0.0, float(regret))


def winner_retained(clean_selected_model: str, stressed_best_model: str) -> bool:
    """Whether the validation-selected model remains the stressed-test winner."""
    return clean_selected_model == stressed_best_model

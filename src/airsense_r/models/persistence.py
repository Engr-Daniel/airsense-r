"""Persistence forecasting baseline."""
from __future__ import annotations

import numpy as np


def persistence_forecast(last_observed_pm25) -> np.ndarray:
    """Forecast next PM2.5 value as the most recent observed PM2.5."""
    return np.asarray(last_observed_pm25, dtype=float)

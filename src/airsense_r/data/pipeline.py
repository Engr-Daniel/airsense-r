"""Causal, station-isolated preprocessing and target-indexed forecasting windows."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import logging

import numpy as np
import pandas as pd

from airsense_r.data.audit import EXPECTED_STATIONS, NUMERIC_SENSOR_COLUMNS

LOG = logging.getLogger(__name__)
NUMERIC = tuple(NUMERIC_SENSOR_COLUMNS)
CHANNELS = (*NUMERIC, "wd")


def validate_stream(frame: pd.DataFrame) -> pd.DataFrame:
    """Return a canonical copy; reject ambiguous labels, timestamps and grids."""
    required = {"station", "timestamp", *CHANNELS}
    if missing := required - set(frame):
        raise ValueError(f"Missing columns: {sorted(missing)}")
    f = frame.copy()
    f["timestamp"] = pd.to_datetime(f["timestamp"], errors="raise")
    if f.empty or f[["station", "timestamp"]].isna().any().any():
        raise ValueError("Empty stream or missing station/timestamp")
    if f.timestamp.dt.tz is not None:
        raise ValueError("Dataset timestamps must be timezone-naive local times")
    if f.duplicated(["station", "timestamp"]).any():
        raise ValueError("Duplicate station-timestamp")
    f = f.sort_values(["station", "timestamp"], kind="stable").reset_index(drop=True)
    for _, group in f.groupby("station", sort=True):
        if not group.timestamp.diff().dropna().eq(pd.Timedelta(hours=1)).all():
            raise ValueError("Non-hourly station grid")
    for col in NUMERIC:
        f[col] = pd.to_numeric(f[col], errors="raise").astype(float)
        if np.isinf(f[col]).any():
            raise ValueError(f"Infinite reading in {col}")
    return f


def read_stations(root: Path, end: str | None = None) -> pd.DataFrame:
    """Load the verified station inventory, optionally exposing only development rows."""
    parts = []
    for path in sorted(root.rglob("PRSA_Data_*.csv")):
        f = pd.read_csv(path)
        f["timestamp"] = pd.to_datetime(f[["year", "month", "day", "hour"]])
        if end is not None:
            f = f.loc[f.timestamp <= pd.Timestamp(end)]
        parts.append(f)
    if not parts:
        raise ValueError("No station CSV files")
    labels = [p.station.dropna().unique().tolist() for p in parts]
    if any(len(x) != 1 for x in labels) or sorted(x[0] for x in labels) != sorted(EXPECTED_STATIONS):
        raise ValueError("Expected exactly one file for each of the 12 stations")
    return validate_stream(pd.concat(parts, ignore_index=True))


def target_partition(keys: pd.DataFrame, config: dict, partition: str) -> np.ndarray:
    """Select windows by frozen target timestamps, not row fractions."""
    if partition not in {"train", "validation", "test"}:
        raise ValueError("Unknown partition")
    d = config["data"]
    ts = pd.to_datetime(keys["target_timestamp"])
    return ts.between(d[f"{partition}_target_start"], d[f"{partition}_target_end"]).to_numpy()


def calendar_features(timestamps: pd.Series) -> np.ndarray:
    """Encode local target calendar using actual year length, including leap years."""
    ts = pd.to_datetime(timestamps)
    hour = ts.dt.hour.to_numpy() / 24
    day = (ts.dt.dayofyear.to_numpy() - 1) / np.where(ts.dt.is_leap_year, 366, 365)
    return np.column_stack([np.sin(2*np.pi*hour), np.cos(2*np.pi*hour),
                            np.sin(2*np.pi*day), np.cos(2*np.pi*day)]).astype("float32")


class CausalPreprocessor:
    """Fit only permitted stations/times; transform with station-local causal history."""

    def __init__(self, forward_fill_hours: int = 6):
        if forward_fill_hours not in (0, 6):
            raise ValueError("Frozen policies support forward fill of 0 or 6 hours")
        self.limit = forward_fill_hours
        self.state: dict | None = None

    def _impute(self, f: pd.DataFrame) -> pd.DataFrame:
        out = f.copy()
        if self.limit:
            out[list(CHANNELS)] = out.groupby("station", sort=False)[list(CHANNELS)].ffill(limit=self.limit)
        for col in NUMERIC:
            out[col] = out[col].fillna(self.state["medians"][col])
        out["wd"] = out.wd.fillna("MISSING").astype(str)
        return out

    def fit(self, frame: pd.DataFrame, fit_end: str, held_out_station: str | None = None) -> "CausalPreprocessor":
        """Estimate medians, vocabulary and numeric scaling before a cutoff only."""
        f = validate_stream(frame)
        f = f.loc[(f.timestamp <= pd.Timestamp(fit_end)) & (f.station != held_out_station)].copy()
        if f.empty:
            raise ValueError("No eligible fitting rows")
        medians = f[list(NUMERIC)].median()
        if medians.isna().any():
            raise ValueError("A training channel is entirely missing")
        categories = sorted(set(f.wd.dropna().astype(str)) - {"MISSING", "OTHER"}) + ["MISSING", "OTHER"]
        self.state = {"schema": 1, "fit_end": str(pd.Timestamp(fit_end)),
                      "fit_stations": sorted(f.station.unique().tolist()),
                      "held_out_station": held_out_station, "forward_fill_hours": self.limit,
                      "medians": medians.to_dict(), "categories": categories}
        imputed = self._impute(f)
        self.state["means"] = imputed[list(NUMERIC)].mean().to_dict()
        self.state["stds"] = imputed[list(NUMERIC)].std(ddof=0).replace(0, 1).to_dict()
        self.state["feature_names"] = [*NUMERIC, *[f"missing_{c}" for c in CHANNELS], *[f"wd_{c}" for c in categories]]
        LOG.info("Fit preprocessing through %s on %s stations", fit_end, len(self.state["fit_stations"]))
        return self

    def transform(self, frame: pd.DataFrame, scaled: bool = False) -> tuple[pd.DataFrame, np.ndarray, np.ndarray]:
        """Return keys/raw targets, feature matrix and imputed PM2.5 for persistence."""
        if self.state is None:
            raise ValueError("Preprocessor is not fitted")
        f = validate_stream(frame)
        missing = f[list(CHANNELS)].isna().to_numpy(dtype="float32")
        imputed = self._impute(f)
        numeric = imputed[list(NUMERIC)].copy()
        persistence = numeric["PM2.5"].to_numpy(dtype="float32")
        if scaled:
            numeric = (numeric - pd.Series(self.state["means"])) / pd.Series(self.state["stds"])
        categories = self.state["categories"]
        wd = imputed.wd.where(imputed.wd.isin(categories), "OTHER")
        onehot = np.column_stack([wd.eq(c).to_numpy() for c in categories])
        features = np.column_stack([numeric.to_numpy(), missing, onehot]).astype("float32")
        if not np.isfinite(features).all():
            raise ValueError("Nonfinite transformed features")
        return f[["station", "timestamp", "PM2.5"]], features, persistence

    @classmethod
    def from_state(cls, state: dict) -> "CausalPreprocessor":
        """Restore JSON-compatible fitted state from a provenance-verified artifact."""
        if state.get("schema") != 1:
            raise ValueError("Unsupported preprocessing schema")
        obj = cls(state["forward_fill_hours"])
        obj.state = state
        return obj


@dataclass
class WindowSet:
    """Compact indices and source features; materialize only requested batches."""

    keys: pd.DataFrame
    y: np.ndarray
    origins: np.ndarray
    features: np.ndarray
    persistence: np.ndarray
    calendar: np.ndarray
    lookback: int = 24

    def batch(self, indices: np.ndarray, tabular: bool = False) -> tuple[np.ndarray, np.ndarray]:
        """Return equivalent chronological sequences or flattened tabular histories."""
        indices = np.asarray(indices, dtype=int)
        rows = self.origins[indices, None] - np.arange(self.lookback-1, -1, -1)
        x = self.features[rows]
        cal = self.calendar[indices]
        return (np.column_stack([x.reshape(len(indices), -1), cal]) if tabular else x), cal


def build_windows(frame: pd.DataFrame, processor: CausalPreprocessor, *,
                  scaled: bool = False, targets: pd.DataFrame | None = None,
                  lookback: int = 24) -> WindowSet:
    """Build one-hour targets without crossing stations or replacing original labels."""
    if lookback != 24:
        raise ValueError("Frozen lookback is 24 hours")
    f, x, persistence = processor.transform(frame, scaled=scaled)
    original = validate_stream(targets if targets is not None else frame)
    if not original[["station", "timestamp"]].equals(f[["station", "timestamp"]]):
        raise ValueError("Target and observation keys differ")
    origins, target_indices = [], []
    for _, group in f.groupby("station", sort=False):
        idx = group.index.to_numpy()
        eligible = idx[lookback:]
        eligible = eligible[original.loc[eligible, "PM2.5"].notna().to_numpy()]
        target_indices.extend(eligible)
        origins.extend(eligible - 1)
    target_indices = np.asarray(target_indices, dtype=int)
    origins = np.asarray(origins, dtype=int)
    keys = f.loc[target_indices, ["station", "timestamp"]].rename(columns={"timestamp": "target_timestamp"}).reset_index(drop=True)
    return WindowSet(keys, original.loc[target_indices, "PM2.5"].to_numpy(), origins,
                     x, persistence[origins], calendar_features(keys.target_timestamp), lookback)

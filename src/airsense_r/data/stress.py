"""Frozen stream-level interventions, independent of windows and model family."""
from __future__ import annotations

from hashlib import sha256
import numpy as np
import pandas as pd

from airsense_r.corruption.dropout import random_feature_dropout, whole_variable_dropout
from airsense_r.corruption.noise import gaussian_relative_noise
from airsense_r.data.pipeline import validate_stream


def stress_stream(frame: pd.DataFrame, config: dict, condition: str, severity: float,
                  seed: int, scales: dict[str, float], channel: str | None = None) -> tuple[pd.DataFrame, list[dict]]:
    """Corrupt input copies during the test history interval; return outage events."""
    out = validate_stream(frame)
    c = config["corruptions"]
    start = pd.Timestamp(config["data"]["test_target_start"]) - pd.Timedelta(hours=24)
    end = pd.Timestamp(config["data"]["test_target_end"]) - pd.Timedelta(hours=1)
    events = []
    for station, group in out.groupby("station", sort=True):
        selected = group.loc[group.timestamp.between(start, end)].copy()
        if selected.empty:
            continue
        station_seed = int.from_bytes(sha256(f"{seed}:{station}".encode()).digest()[:4], "big")
        if condition == "random_dropout":
            if severity not in c["random_dropout_levels"]:
                raise ValueError("Unfrozen dropout severity")
            selected = random_feature_dropout(selected, c["random_dropout_channels"], severity, station_seed)
        elif condition == "noise":
            if severity not in c["noise_levels"]:
                raise ValueError("Unfrozen noise severity")
            selected = gaussian_relative_noise(selected, c["noise_channels"], severity, scales, station_seed)
        elif condition == "whole_variable":
            if channel not in c["whole_variable_dropout"]:
                raise ValueError("Unfrozen channel")
            selected = whole_variable_dropout(selected, channel)
        elif condition == "outage":
            if channel not in c["contiguous_outage_channels"] or severity not in c["contiguous_outage_hours"]:
                raise ValueError("Unfrozen outage")
            rng = np.random.default_rng(station_seed)
            test_start = pd.Timestamp(config["data"]["test_target_start"])
            eligible = selected.loc[selected.timestamp >= test_start]
            for month, part in eligible.groupby(eligible.timestamp.dt.to_period("M")):
                length = int(severity)
                if len(part) < length:
                    raise ValueError("Month lacks enough outage observations")
                offset = int(rng.integers(len(part) - length + 1))
                indices = part.index[offset:offset+length]
                selected.loc[indices, channel] = np.nan
                events.append({"station": station, "channel": channel, "start": str(part.loc[indices[0], "timestamp"]),
                               "end": str(part.loc[indices[-1], "timestamp"]), "seed": seed})
        else:
            raise ValueError("Unknown stress condition")
        for col in c["random_dropout_channels"]:
            out.loc[selected.index, col] = selected[col]
    return out, events

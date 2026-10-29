"""Post-results PM2.5 input sensitivity; original P6 protocol stays unchanged."""
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import logging

import numpy as np
import pandas as pd

from airsense_r.artifacts import RunStore, json_bytes
from airsense_r.p6_storage import PredictionBundles
from airsense_r.data.stress import stress_stream
from airsense_r.data.pipeline import validate_stream
from airsense_r.evaluation.p6_verify import (
    sampling_weights, independently_bootstrap, compare_numbers, affected_targets,
)
from airsense_r.evaluation.stress_summary import reliability_summary, stress_intervals
from airsense_r.p6 import (
    predict_case, score_rows, error_calendar, outage_affected, model_keys,
)

LOG = logging.getLogger(__name__)
RUN_ID = "p9-target-history-01"
SETTINGS = {
    "status": "post_results_extension", "policy": "primary", "channel": "PM2.5",
    "dropout_levels": [0.1, 0.3, 0.5], "outage_hours": [6, 12],
    "corruption_seeds": [101, 202, 303, 404, 505],
    "thresholds": [0.5, 1.0, 1.5, 2.0], "no_refitting": True,
}


def cases() -> list[dict]:
    """Return the complete bounded matrix, independent of observed outcomes."""
    return [
        {"id": f"pm25-dropout-{int(p*100)}", "kind": "random_dropout", "severity": p}
        for p in SETTINGS["dropout_levels"]
    ] + [
        {"id": f"pm25-outage-{h}", "kind": "outage", "severity": h}
        for h in SETTINGS["outage_hours"]
    ]


def corrupt_history(frame: pd.DataFrame, config: dict, spec: dict, seed: int) -> tuple[pd.DataFrame, list[dict], dict]:
    """Reuse stream scheduling with an explicit, isolated target-channel override."""
    if spec not in cases() or seed not in SETTINGS["corruption_seeds"]:
        raise ValueError("Condition or seed outside declared target-history extension")
    frame = validate_stream(frame)
    extension = deepcopy(config)
    extension["corruptions"]["random_dropout_channels"] = ["PM2.5"]
    extension["corruptions"]["contiguous_outage_channels"] = ["PM2.5"]
    stressed, events = stress_stream(frame, extension, spec["kind"], spec["severity"], seed, {}, "PM2.5")
    # Raw labels stay in frame; only the separate observation copy is changed.
    pd.testing.assert_frame_equal(frame.drop(columns="PM2.5"), stressed.drop(columns="PM2.5"))
    changed = ~(frame["PM2.5"].eq(stressed["PM2.5"]) | (frame["PM2.5"].isna() & stressed["PM2.5"].isna()))
    audit = {"condition": spec, "seed": seed, "outage_events": events,
             "changed_pm25_cells": int(changed.sum()), "labels_source": "separate_original_stream",
             "observation_sha256": sha256(stressed[["station", "timestamp", "PM2.5"]].to_csv(
                 index=False, float_format="%.17g").encode()).hexdigest()}
    return stressed, events, audit


def evaluate(frame: pd.DataFrame, parent: RunStore, store: RunStore,
             bundles: PredictionBundles, models: dict, config: dict, plan: dict) -> None:
    """Checkpoint each prediction, and independently verify each condition interval."""
    state = parent.load_json("preprocessing.json")
    selected = parent.load_json("selection.json")["selected_family"]
    expected = bundles.load("targets")
    clean = predict_case(frame, frame, state, "primary", "clean", models, bundles, config, expected, plan)
    full = np.ones(len(expected["y"]), dtype=bool)
    stations = sorted(set(expected["station"]))
    weights = None
    for spec in cases():
        name = f"summary-{spec['id']}.json"
        if store.has(name):
            for seed in SETTINGS["corruption_seeds"]:
                unit = f"{spec['id']}-c{seed}"
                store.load_json(f"realization-{unit}.json")
                if not store.has(f"metrics-{unit}.csv"):
                    raise ValueError("Completed condition is missing metrics")
                for family, training_seed in model_keys(config):
                    pred = bundles.load(f"pred-primary-{unit}-{family}-{training_seed}")["prediction"]
                    if pred.shape != expected["y"].shape or not np.isfinite(pred).all():
                        raise ValueError("Invalid resumed prediction")
            LOG.info("Verified completed target-history condition: %s", spec["id"])
            continue
        parts, clean_errors, stressed_errors = [], {}, {}
        for seed in SETTINGS["corruption_seeds"]:
            unit = f"{spec['id']}-c{seed}"
            LOG.info("Target-history condition %s / corruption seed %s", spec["id"], seed)
            stressed, events, audit = corrupt_history(frame, config, spec, seed)
            store.save(f"realization-{unit}.json", json_bytes(audit))
            pred = predict_case(stressed, frame, state, "primary", unit, models, bundles, config, expected, plan)
            masks = {"full": full}
            if spec["kind"] == "outage":
                masks["affected"] = outage_affected(expected, events)
                np.testing.assert_array_equal(masks["affected"], affected_targets(
                    expected["station"], expected["time"], events, 24))
            rows = score_rows(pred, clean, expected, masks, seed)
            store.save(f"metrics-{unit}.csv", rows.to_csv(index=False, float_format="%.17g").encode())
            parts.append(rows)
            for scope, mask in masks.items():
                clean_errors.setdefault(scope, []).append(error_calendar(clean, expected, mask, config))
                stressed_errors.setdefault(scope, []).append(error_calendar(pred, expected, mask, config))
            del stressed, pred
        reports = {}
        combined = pd.concat(parts, ignore_index=True)
        for scope in clean_errors:
            c, s = np.stack(clean_errors[scope]), np.stack(stressed_errors[scope])
            report = reliability_summary(combined.loc[combined.scope == scope], selected, 1.0)
            intervals = stress_intervals(c, s, config["models"]["candidates"], selected, stations, config)
            if weights is None:
                weights = sampling_weights(c.shape[-1], config)
            independent = independently_bootstrap(c, s, weights, config["models"]["candidates"],
                                                  stations, selected, config["uncertainty"]["confidence"])
            compare_numbers(independent, intervals)
            if scope == "full" and not intervals["available"]:
                raise ValueError("Headline interval unavailable")
            if intervals["available"]:
                np.testing.assert_allclose(report["selection_regret"], independent["selection_regret"]["estimate"],
                                           atol=1e-8, rtol=1e-10)
            report["uncertainty"] = intervals
            report["independent_interval_check"] = True
            reports[scope] = report
        store.save(name, json_bytes({"condition": spec, "policy": "primary", "scopes": reports}))
        LOG.info("Target-history condition complete and checked: %s", spec["id"])
    store.save("dashboard-target-history.json", json_bytes({"settings": SETTINGS,
        "reports": [store.load_json(f"summary-{spec['id']}.json") for spec in cases()]}))
    store.save("complete.json", json_bytes({"execution_complete": True, "scientifically_accepted": False,
        "post_results_extension": True, "conditions": len(cases()), "refitting": False,
        "independent_intervals_checked": True, "selected_family": selected}))

"""Descriptive post-results tolerance audit; never replace the primary choice."""
from __future__ import annotations

import math
import pandas as pd

TOLERANCES = (0.5, 1.0, 1.5, 2.0)
ORDER = ("persistence", "xgboost", "mlp", "gru")


def select(validation: dict[str, float], tolerance: float) -> str:
    """Apply the original simplicity order to validation scores alone."""
    if set(validation) != set(ORDER) or not all(math.isfinite(x) for x in validation.values()):
        raise ValueError("Missing/nonfinite validation family scores")
    if tolerance not in TOLERANCES:
        raise ValueError("Undeclared sensitivity tolerance")
    best = min(validation.values())
    return next(m for m in ORDER if validation[m] <= best + tolerance)


def tables(p5_selection: dict, clean: dict, sites: dict, sensor_reports: list) -> tuple:
    """Separate fixed-selection interpretation from counterfactual selection."""
    observations = []
    original = p5_selection["selected_family"]
    observations.append(("P5", "primary", "clean", "full", p5_selection["validation_mae"], original,
                         {r["model"]: r["mae"] for r in clean["metrics"]}, clean["uncertainty"]["selection_regret"]))
    for report in sensor_reports:
        for scope, result in report["scopes"].items():
            if result["selected_family"] != original:
                raise ValueError("P6 selected family differs from accepted P5")
            ci = result["uncertainty"].get("selection_regret")
            observations.append(("P6", report["policy"], report["condition"]["id"], scope,
                p5_selection["validation_mae"], original, {r["model"]: r["mae"] for r in result["metrics"]}, ci))
    for station, result in sites["stations"].items():
        observations.append(("P7", "primary", station, "station", result["validation_mae"],
                             result["selected_family"], result["test_mae"], result["selection_regret"]))
    interpretation, counterfactual = [], []
    for phase, policy, condition, scope, validation, selected, scores, ci in observations:
        if set(scores) != set(ORDER) or not all(math.isfinite(x) for x in scores.values()):
            raise ValueError("Missing/nonfinite test family scores")
        if select(validation, 1.0) != selected:
            raise ValueError("Primary validation choice does not reproduce")
        oracle = min(scores.values())
        regret = scores[selected] - oracle
        if ci is not None and not math.isclose(regret, ci["estimate"], abs_tol=1e-8, rel_tol=1e-10):
            raise ValueError("Accepted regret disagrees with family metrics")
        for tolerance in TOLERANCES:
            key = {"phase": phase, "policy": policy, "condition": condition, "scope": scope,
                   "tolerance": tolerance, "primary_tolerance": tolerance == 1.0}
            relation = "unavailable" if ci is None else (
                "within" if ci["ci_high"] <= tolerance else "above" if ci["ci_low"] > tolerance else "crosses")
            interpretation.append({**key, "selected_family": selected, "selected_mae": scores[selected],
                "oracle_mae": oracle, "regret": regret, "point_within": regret <= tolerance,
                "ci_low": None if ci is None else ci["ci_low"], "ci_high": None if ci is None else ci["ci_high"],
                "interval_relative_to_tolerance": relation})
            chosen = select(validation, tolerance)
            counterfactual.append({**key, "selected_family": chosen, "original_family": selected,
                "selection_changed": chosen != selected, "validation_mae": validation[chosen],
                "test_mae": scores[chosen], "oracle_mae": oracle, "regret": scores[chosen]-oracle,
                "point_within": scores[chosen]-oracle <= tolerance, "uncertainty": "not_recomputed_descriptive_only"})
    return pd.DataFrame(interpretation), pd.DataFrame(counterfactual)

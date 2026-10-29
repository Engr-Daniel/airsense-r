"""Generate two distinct tolerance audits from exact accepted P5/P8 evidence."""
from hashlib import sha256
import argparse
import io
import json
from pathlib import Path

import numpy as np
import pandas as pd

from airsense_r.artifacts import json_bytes, source_hash
from airsense_r.evaluation.p6_verify import Snapshot
from airsense_r.evaluation.threshold_sensitivity import tables

P5_MANIFEST = "0ffba65635246114d283c954ae65256662344e1c1513d434e9cb58c2e91f5cf4"


def run(root: Path, p5_directory: Path, p8_directory: Path, output: Path) -> None:
    """Fail closed on input identity; emit derived, explicitly post-results tables."""
    receipt = json.loads((root / "results/p8/final_acceptance.json").read_bytes())
    clean_path = root / "results/p5/corrected_acceptance.json"
    clean = json.loads(clean_path.read_bytes())
    if receipt["status"] != "P7_and_P8_accepted" or not clean["accepted"]:
        raise ValueError("Primary acceptance missing")
    for directory, expected in [(p5_directory, P5_MANIFEST), (p8_directory, receipt["manifest_sha256"])]:
        if sha256((directory / "manifest.json").read_bytes()).hexdigest() != expected:
            raise ValueError("Unaccepted input manifest")
    p5, p8 = Snapshot(p5_directory), Snapshot(p8_directory)
    if p5.json("test-uncertainty.json") != clean["uncertainty"]:
        raise ValueError("Clean acceptance uncertainty differs from pinned evidence")
    metrics = pd.read_csv(io.BytesIO(p5.blobs["metrics-test-aggregate.csv"]), float_precision="round_trip")
    accepted = pd.DataFrame(clean["metrics"])
    for column in ["mae", "rmse", "r2"]:
        np.testing.assert_allclose(metrics.set_index("model").sort_index()[column],
                                   accepted.set_index("model").sort_index()[column], atol=1e-8, rtol=1e-10)
    selection = p5.json("selection.json")
    interpretation, counterfactual = tables(selection, clean, p8.json("p7-independent-report.json"),
                                           p8.json("sensor-accepted-uncertainty.json")["reports"])
    output.mkdir(parents=True, exist_ok=True)
    for name, frame in [("interpretation", interpretation), ("counterfactual-selection", counterfactual)]:
        (output / f"{name}.csv").write_bytes(frame.to_csv(index=False, float_format="%.17g").encode())
    aggregate = []
    for tolerance, rows in counterfactual.loc[counterfactual.phase == "P7"].groupby("tolerance"):
        aggregate.append({"tolerance": tolerance, "mean_station_regret": float(rows.regret.mean()),
            "mean_selected_mae": float(rows.test_mae.mean()), "stations_within": int(rows.point_within.sum()),
            "changed_selections": int(rows.selection_changed.sum()), "stations": len(rows)})
    (output / "summary.json").write_bytes(json_bytes({"post_results_descriptive": True,
        "primary_rule_unchanged": True, "counterfactual_uncertainty_recomputed": False,
        "source_hash": source_hash(root), "p5_manifest_sha256": P5_MANIFEST,
        "p8_manifest_sha256": receipt["manifest_sha256"], "p8_commit": receipt["result_commit"],
        "p5_commit": clean["result_commit"], "clean_receipt_sha256": sha256(clean_path.read_bytes()).hexdigest(),
        "plan_sha256": sha256((root / "research/P9_CHECKPOINT_PLAN.md").read_bytes().replace(b"\r\n", b"\n")).hexdigest(),
        "interpretation_rows": len(interpretation), "counterfactual_rows": len(counterfactual),
        "loso_counterfactual": aggregate,
        "artifacts": {p.name: sha256(p.read_bytes()).hexdigest() for p in sorted(output.glob("*.csv"))}}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--p5-directory", type=Path, required=True)
    parser.add_argument("--p8-directory", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("results/p9-threshold-sensitivity"))
    args = parser.parse_args()
    run(Path(__file__).resolve().parents[1], args.p5_directory, args.p8_directory, args.output)

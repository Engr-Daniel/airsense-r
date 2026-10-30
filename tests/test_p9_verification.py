"""Saved target-history review: changed persistence, recovery and corruption."""
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys

import numpy as np
import pandas as pd
import pytest

from airsense_r.artifacts import RunStore, json_bytes
from airsense_r.evaluation.p6_verify import Snapshot, verify_saved_run, affected_targets
from airsense_r.evaluation.stress_summary import reliability_summary, stress_intervals
from airsense_r.p6 import score_rows, error_calendar
from airsense_r.p6_storage import PredictionBundles
from scripts.build_target_history_review_notebook import build


def fixture(tmp_path):
    config = {"uncertainty": {"n_bootstrap": 25, "block_length_hours": 7, "confidence": .95},
        "seeds": {"bootstrap": 424242, "training": [42, 31415]},
        "models": {"candidates": ["persistence", "xgboost", "mlp", "gru"]},
        "data": {"test_target_start": "2016-01-01 00:00", "test_target_end": "2016-01-03 01:00", "lookback_hours": 24}}
    parent = RunStore(tmp_path / "parent", {"config": config})
    bundles = PredictionBundles(tmp_path / "drive", parent)
    target = {"station": np.repeat(["A", "B"], 50),
        "time": np.tile(pd.date_range("2016-01-01", periods=50, freq="h").asi8, 2),
        "y": np.tile([74.3, 81.8, 60.2, 42.7, 30.5], 20)}
    bundles.save("targets", target)
    parent.save("lineage.json", json_bytes({"selection": {"selected_family": "persistence"}}))
    rng = np.random.default_rng(8)
    clean = {(m, s): target["y"] + rng.normal(size=100)
        for m in config["models"]["candidates"]
        for s in ([-1] if m == "persistence" else config["seeds"]["training"])}
    for (m, s), pred in clean.items():
        bundles.save(f"pred-primary-clean-{m}-{s}", {"prediction": pred})
    reports = []
    for case in ["pm25-dropout-10", "pm25-dropout-30", "pm25-dropout-50", "pm25-outage-6", "pm25-outage-12"]:
        masks = {"full": np.ones(100, dtype=bool)}
        events = [{"station": st, "start": "2016-01-01 04:00", "end": "2016-01-01 15:00"} for st in ["A", "B"]]
        if "outage" in case:
            masks["affected"] = affected_targets(target["station"], target["time"], events, 24)
        rows, pairs = [], {scope: ([], []) for scope in masks}
        for seed in [101, 202, 303, 404, 505]:
            unit = f"{case}-c{seed}"
            pred = {key: values + rng.normal(size=100) + 2 for key, values in clean.items()}
            for (m, s), values in pred.items():
                bundles.save(f"pred-primary-{unit}-{m}-{s}", {"prediction": values})
            metric = score_rows(pred, clean, target, masks, seed)
            parent.save(f"metrics-{unit}.csv", metric.to_csv(index=False, float_format="%.17g").encode())
            parent.save(f"realization-{unit}.json", json_bytes({"outage_events": events}))
            rows.append(metric)
            for scope, mask in masks.items():
                pairs[scope][0].append(error_calendar(clean, target, mask, config))
                pairs[scope][1].append(error_calendar(pred, target, mask, config))
        combined = pd.concat(rows)
        scopes = {}
        for scope, (a, b) in pairs.items():
            scopes[scope] = reliability_summary(combined[combined.scope == scope], "persistence", 1)
            scopes[scope]["uncertainty"] = stress_intervals(np.array(a), np.array(b), config["models"]["candidates"], "persistence", ["A", "B"], config)
        reports.append({"policy": "primary", "condition": {"id": case}, "scopes": scopes})
    parent.save("dashboard-target-history.json", json_bytes({"reports": reports}))
    parent.save("complete.json", json_bytes({"execution_complete": True}))
    return parent


def test_review_fresh_process_resume_and_tamper(tmp_path):
    parent = fixture(tmp_path)
    before = {p: sha256(p.read_bytes()).hexdigest() for folder in [parent.directory, tmp_path / "drive"] for p in folder.iterdir() if p.is_file()}
    output = RunStore(tmp_path / "review", {"fixture": True})
    def interrupt(message):
        if message.startswith("Saved and synchronized review 1/"):
            raise InterruptedError()
    with pytest.raises(InterruptedError):
        verify_saved_run(Snapshot(parent.directory), tmp_path / "drive", output, interrupt, target_history=True)
    script = '''from pathlib import Path
import sys
from airsense_r.artifacts import RunStore
from airsense_r.evaluation.p6_verify import Snapshot, verify_saved_run
p=Path(sys.argv[1])
verify_saved_run(Snapshot(p/'parent'),p/'drive',RunStore(p/'review',{'fixture':True}),target_history=True)
'''
    subprocess.run([sys.executable, "-c", script, str(tmp_path)], check=True, env={**os.environ, "PYTHONPATH": str(Path(__file__).resolve().parents[1] / "src")})
    assert RunStore(tmp_path / "review", {"fixture": True}).load_json("complete.json")["passed"]
    assert before == {p: sha256(p.read_bytes()).hexdigest() for p in before}
    path = next((tmp_path / "drive").glob("pred-*.npz"))
    path.write_bytes(path.read_bytes() + b"altered")
    with pytest.raises(ValueError, match="differs"):
        verify_saved_run(Snapshot(parent.directory), tmp_path / "drive", RunStore(tmp_path / "review", {"fixture": True}), target_history=True)


def test_changed_interval_and_missing_condition_rejected(tmp_path):
    parent = fixture(tmp_path)
    report = parent.load_json("dashboard-target-history.json")
    report["reports"][0]["scopes"]["full"]["uncertainty"]["selection_regret"]["ci_high"] += .1
    snapshot = Snapshot(parent.directory)
    snapshot.blobs["dashboard-target-history.json"] = json_bytes(report)
    with pytest.raises(AssertionError):
        verify_saved_run(snapshot, tmp_path / "drive", RunStore(tmp_path / "review", {}), target_history=True)
    report["reports"].pop()
    snapshot.blobs["dashboard-target-history.json"] = json_bytes(report)
    with pytest.raises(ValueError, match="matrix"):
        verify_saved_run(snapshot, tmp_path / "drive", RunStore(tmp_path / "review2", {}), target_history=True)


def test_review_notebook_is_read_only_and_pinned():
    import nbformat
    notebook = build("a" * 40)
    nbformat.validate(nbformat.from_dict(notebook))
    cells = [c["source"] for c in notebook["cells"] if c["cell_type"] == "code"]
    assert len(cells) == 4 and 'CODE_REVISION = "' + 'a' * 40 + '"' in cells[0]
    assert 'scripts/verify_target_history.py' in cells[2]
    assert 'run_target_history.py' not in ''.join(cells)
    assert '[train,notebooks]' not in cells[0]
    for source in cells:
        compile(source, '<notebook>', 'exec')


def test_review_notebook_fresh_process_and_rerun(tmp_path):
    root = Path(__file__).resolve().parents[1]
    cells = [c["source"] for c in build("a" * 40)["cells"] if c["cell_type"] == "code"]
    run_id = "p9-review-fixture-" + sha256(str(tmp_path).encode()).hexdigest()[:12]
    (tmp_path / "storage.json").write_text('{}')
    output = root / ".tmp/checkpoint-checkouts" / run_id / "results" / run_id
    child = (
        "from pathlib import Path; from airsense_r.artifacts import RunStore,json_bytes,source_hash; "
        f"s=RunStore(Path({str(output)!r}),{{'verifier_source_hash':source_hash(Path({str(root)!r}))}}); "
        "s.save('complete.json',json_bytes({'passed':True}))"
    )
    env = {**os.environ, "AIRSENSE_NOTEBOOK_TEST_MODE": "1", "AIRSENSE_NOTEBOOK_TEST_ROOT": str(root),
        "AIRSENSE_P9_REVIEW_TEST_MODELS": str(tmp_path), "AIRSENSE_P9_REVIEW_TEST_RUN": run_id,
        "AIRSENSE_P9_REVIEW_TEST_COMMAND": json.dumps([sys.executable, "-c", child])}
    for _ in range(2):
        result = subprocess.run([sys.executable, "-c", "from IPython.display import display\n" + "\n".join(cells)],
            env=env, capture_output=True, text=True, timeout=90)
        assert result.returncode == 0, result.stdout + result.stderr
        assert "VERIFICATION COMPLETE" in result.stdout

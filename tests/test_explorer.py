"""Reliability explorer export: verified inputs, threshold logic and published data."""
from hashlib import sha256
import json
from pathlib import Path
import subprocess

import pandas as pd
import pytest

from airsense_r.explorer import (GitSnapshot, MODELS, PREDICTION_WINDOWS, build_payload, prediction_windows,
                                 regret_status, _dump)

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "docs/data"


@pytest.mark.parametrize("estimate, ci, threshold, expected", [
    (0.0, [0.0, 0.0], 1.0, "within"),
    (1.0, [0.5, 1.0], 1.0, "within"),
    (0.795, [0.476, 1.048], 1.0, "within_ci_crosses"),
    (1.050, [0.742, 1.311], 1.0, "above_ci_crosses"),
    (2.282, [1.696, 2.910], 1.0, "above"),
    (0.569, [0.340, 0.763], 0.5, "above_ci_crosses"),
    (0.3, None, 1.0, "within"),
    (1.3, None, 1.0, "above"),
])
def test_regret_status_uses_point_estimate_then_interval(estimate, ci, threshold, expected):
    assert regret_status(estimate, *(ci or [None, None]), threshold=threshold) == expected


def _git(cwd: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()


def _snapshot_repo(tmp_path: Path, manifest_sha: str | None = None) -> tuple[Path, str]:
    directory = tmp_path / "results/run"
    directory.mkdir(parents=True)
    payload = b"model,mae\npersistence,74.3\n"
    (directory / "metrics.csv").write_bytes(payload)
    sha = manifest_sha or sha256(payload).hexdigest()
    (directory / "manifest.json").write_text(json.dumps({"artifacts": {"metrics.csv": {"sha256": sha}}}))
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "add", ".")
    _git(tmp_path, "-c", "user.name=t", "-c", "user.email=t@example.invalid", "commit", "-qm", "fixture")
    return tmp_path, _git(tmp_path, "rev-parse", "HEAD")


def test_git_snapshot_reads_only_checksum_verified_committed_bytes(tmp_path):
    root, commit = _snapshot_repo(tmp_path)
    raw = (root / "results/run/manifest.json").read_bytes()
    snapshot = GitSnapshot(root, commit, "results/run", sha256(raw).hexdigest())
    assert snapshot.csv("metrics.csv")["mae"].tolist() == [74.3]
    # The working tree is irrelevant: only committed bytes are read.
    (root / "results/run/metrics.csv").write_text("model,mae\npersistence,0\n")
    assert snapshot.csv("metrics.csv")["mae"].tolist() == [74.3]
    with pytest.raises(ValueError, match="not the accepted manifest"):
        GitSnapshot(root, commit, "results/run", "0" * 64)
    with pytest.raises(ValueError, match="not listed"):
        snapshot.bytes("other.csv")
    with pytest.raises(ValueError, match="not listed|Unsafe"):
        snapshot.bytes("../manifest.json")


def test_git_snapshot_rejects_artifact_that_does_not_match_manifest(tmp_path):
    root, commit = _snapshot_repo(tmp_path, manifest_sha="f" * 64)
    with pytest.raises(ValueError, match="Checksum mismatch"):
        GitSnapshot(root, commit, "results/run").bytes("metrics.csv")


def _predictions(conflicting_truth: bool = False) -> pd.DataFrame:
    _, start, end = PREDICTION_WINDOWS[0]
    hours = pd.date_range(start, end, freq="h").strftime("%Y-%m-%d %H:%M:%S")
    rows = []
    for i, ts in enumerate(hours):
        if i == 5:  # an hour without an observed target stays missing, not zero
            continue
        truth = 74.3 if i % 2 else 81.8
        for model in MODELS:
            for seed in ([-1] if model == "persistence" else [42, 31415, 27182]):
                y_true = truth + (1 if conflicting_truth and model == "gru" and i == 3 else 0)
                rows.append({"station": "A", "target_timestamp": ts, "y_true": y_true,
                             "y_pred": truth + seed / 1e5, "model": model, "seed": seed})
    return pd.DataFrame(rows)


def test_prediction_windows_keep_seeds_separate_and_preserve_decimals_and_gaps():
    windows = prediction_windows(_predictions())
    first = windows[PREDICTION_WINDOWS[0][0]]["stations"]["A"]
    assert len(first["actual"]) == 168 and first["actual"][5] is None
    assert first["actual"][:2] == [81.8, 74.3]
    assert isinstance(first["persistence"], list)
    for model in ("xgboost", "mlp", "gru"):
        assert sorted(first[model]) == ["27182", "31415", "42"]
        assert first[model]["31415"][0] != first[model]["42"][0]
    restored = json.loads(_dump(windows, indent=None))
    assert restored == json.loads(json.dumps(windows))


def test_prediction_windows_reject_inconsistent_observed_targets():
    with pytest.raises(ValueError, match="Inconsistent observed targets"):
        prediction_windows(_predictions(conflicting_truth=True))


@pytest.fixture(scope="module")
def published():
    return json.loads((DATA / "explorer.json").read_bytes())


def test_published_explorer_matches_accepted_receipts(published):
    clean = json.loads((ROOT / "results/p5/corrected_acceptance.json").read_bytes())
    receipt_mae = {m["model"]: m["mae"] for m in clean["metrics"]}
    assert {m["model"]: m["mae"] for m in published["clean"]["test"]} == receipt_mae
    assert published["provenance"]["p5"]["recomputed_mae"] == pytest.approx(receipt_mae, abs=1e-9)
    assert published["clean"]["selection_regret"] == clean["uncertainty"]["selection_regret"]["estimate"]
    assert published["provenance"]["p5"]["receipt_sha256"] == sha256(
        (ROOT / "results/p5/corrected_acceptance.json").read_bytes()).hexdigest()

    target = json.loads((ROOT / "results/p9-target-history/final_acceptance.json").read_bytes())
    exported = {(t["id"], t["scope"]): t for t in published["target_history"]}
    assert len(exported) == len(target["summaries"])
    for summary in target["summaries"]:
        row = exported[(summary["condition"], summary["scope"])]
        interval = summary["uncertainty"]["selection_regret"]
        assert row["selection_regret"] == summary["selection_regret"]
        assert row["regret_ci"] == [interval["ci_low"], interval["ci_high"]]
    worst = exported[("pm25-outage-12", "affected")]
    assert round(worst["selection_regret"], 3) == 2.282 and worst["status"] == "above"

    p8 = json.loads((ROOT / "results/p8/final_acceptance.json").read_bytes())
    site = published["site_shift"]
    assert site["mean_selection_regret"]["estimate"] == p8["mean_station_selection_regret"]["estimate"]
    assert site["within_threshold"] == p8["stations_within_practical_near_tie"] == 11
    assert published["provenance"]["p8"]["manifest_sha256"] == p8["manifest_sha256"]


def test_published_statuses_follow_frozen_threshold(published):
    scopes = [(published["clean"]["selection_regret"], published["clean"]["regret_ci"], published["clean"]["status"])]
    scopes += [(v["selection_regret"], v["regret_ci"], v["status"]) for s in published["sensors"] for v in s["scopes"].values()]
    scopes += [(t["selection_regret"], t["regret_ci"], t["status"]) for t in published["target_history"]]
    scopes += [(s["selection_regret"], s["regret_ci"], s["status"]) for s in published["site_shift"]["stations"]]
    assert len(scopes) == 1 + 42 + 7 + 12
    for estimate, ci, status in scopes:
        assert regret_status(estimate, *(ci or [None, None]), threshold=1.0) == status


def test_prediction_window_file_matches_recorded_checksum(published):
    raw = (DATA / published["prediction_windows"]["file"]).read_bytes()
    assert sha256(raw).hexdigest() == published["prediction_windows"]["sha256"]
    windows = json.loads(raw)
    assert list(windows) == [w[0] for w in PREDICTION_WINDOWS]
    assert all(len(w["stations"]) == 12 for w in windows.values())


def _commit_available(commit: str) -> bool:
    return subprocess.run(["git", "cat-file", "-e", f"{commit}^{{commit}}"], cwd=ROOT,
                          capture_output=True).returncode == 0


def test_published_data_is_reproducible_from_accepted_commits(published):
    commits = [published["provenance"]["p5"]["result_commit"], published["provenance"]["p8"]["result_commit"]]
    if not all(_commit_available(c) for c in commits):
        pytest.skip("Accepted result branches are not fetched in this checkout")
    payload, windows = build_payload(ROOT)
    assert json.loads(_dump(payload)) == published
    assert _dump(windows, indent=None) == (DATA / "clean-prediction-windows.json").read_bytes()

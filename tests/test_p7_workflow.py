"""Native all-family LOSO, actual process interruption and bare-Git recovery."""
from hashlib import sha256
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from importlib.util import find_spec

import nbformat
import pytest

from airsense_r.artifacts import RunStore
from airsense_r.training.fold_store import FoldStore
from airsense_r.p5 import read_predictions

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.skipif(not find_spec("tensorflow") or not find_spec("xgboost"), reason="Training dependencies required")
def test_fresh_process_loso_interruption_restore_and_completion(tmp_path):
    remote = tmp_path / "remote.git"
    subprocess.run(["git", "init", "--bare", str(remote)], check=True, capture_output=True)
    work = tmp_path / "work"
    command = [sys.executable, str(ROOT / "tests/p7_fixture_runner.py"), str(ROOT), str(work), str(remote)]
    first = subprocess.run([*command, "interrupt"], capture_output=True, text=True, timeout=240)
    assert first.returncode != 0 and "Fixture interruption" in first.stderr, first.stdout+first.stderr
    assert not list(work.rglob("all-selections-frozen.json"))
    # Remove only the disposable checkout to simulate a replaced Colab runtime.
    # Drive remains, and the new checkout must recover solely from pushed evidence.
    checkout_root = (work / ".tmp/checkpoint-checkouts").resolve()
    assert checkout_root.is_relative_to(work.resolve())
    shutil.rmtree(checkout_root, onerror=lambda f, p, _: (os.chmod(p, 0o700), f(p)))
    evaluation = subprocess.run([*command, "evaluate-interrupt"], capture_output=True, text=True, timeout=600)
    assert evaluation.returncode != 0 and "Fixture interruption" in evaluation.stderr, evaluation.stdout+evaluation.stderr
    frozen_models = {p: p.read_bytes() for p in (work / "drive").glob("p7-sites-01/*/refit-*/progress.json")}
    assert len(frozen_models) == 6
    resumed = subprocess.run([*command, "evaluation-resume"], capture_output=True, text=True, timeout=300)
    assert resumed.returncode == 0, resumed.stdout+resumed.stderr
    assert all(p.read_bytes() == data for p, data in frozen_models.items())
    directory = work / ".tmp/checkpoint-checkouts/p7-sites-01/results/p7-sites-01"
    manifest = json.loads((directory / "manifest.json").read_bytes())
    store = RunStore(directory, manifest["provenance"])
    assert store.load_json("complete.json")["scientifically_accepted"] is False
    for station in ["A", "B"]:
        fold = FoldStore(store, station, work / "drive/p7-sites-01/predictions")
        assert set(read_predictions(fold, "validation").station) == ({"A", "B"}-{station})
        pred = read_predictions(fold, "test", round_trip=True)
        assert set(pred.station) == {station}
        assert {74.3, 81.8}.issubset(set(pred.y_true))
        assert set(pred.model) == {"persistence", "xgboost", "mlp", "gru"}
    before = {p: sha256(p.read_bytes()).hexdigest() for p in (work / "drive").rglob("*") if p.is_file()}
    final = subprocess.run([*command, "completed"], capture_output=True, text=True, timeout=60)
    assert final.returncode == 0, final.stdout+final.stderr
    assert all(sha256(p.read_bytes()).hexdigest() == digest for p, digest in before.items())
    assert len(subprocess.check_output(["git", "--git-dir", str(remote), "for-each-ref", "--format=%(refname)", "refs/heads"], text=True).splitlines()) == 1


def test_p7_four_cells_fresh_process(tmp_path):
    notebook = nbformat.read(ROOT / "notebooks/06_p7_site_shift_analysis.ipynb", as_version=4)
    nbformat.validate(notebook)
    cells = [cell.source for cell in notebook.cells if cell.cell_type == "code"]
    assert len(cells) == 4 and all("input(" not in cell for cell in cells)
    run = "p7-notebook-fixture-"+sha256(str(tmp_path).encode()).hexdigest()[:12]
    output = ROOT / ".tmp/checkpoint-checkouts" / run / "results" / run
    storage_id = "f"*32
    (tmp_path / "storage.json").write_text(json.dumps({"storage_id": storage_id}))
    parameters = {"phase": "P7", "run_id": run, "model_storage_id": storage_id, "synthetic_only": True}
    child = f"from pathlib import Path; from airsense_r.artifacts import RunStore,json_bytes,provenance; s=RunStore(Path({str(output)!r}),provenance(Path({str(ROOT)!r}),{parameters!r})); s.save('complete.json',json_bytes({{'execution_complete':True}})); s.save('site-shift-report.json',json_bytes({{'synthetic_only':True}}))"
    env = {**os.environ, "AIRSENSE_NOTEBOOK_TEST_MODE": "1", "AIRSENSE_NOTEBOOK_TEST_ROOT": str(ROOT),
        "AIRSENSE_P7_TEST_MODELS": str(tmp_path), "AIRSENSE_P7_TEST_RUN": run,
        "AIRSENSE_P7_TEST_COMMAND": json.dumps([sys.executable, "-c", child])}
    for _ in range(2):
        result = subprocess.run([sys.executable, "-c", "from IPython.display import display\n"+"\n\n".join(cells)],
            env=env, capture_output=True, text=True, timeout=45)
        assert result.returncode == 0, result.stdout+result.stderr
        assert "P7 EXECUTION COMPLETE" in result.stdout
    manifest_path = output / "manifest.json"
    changed = json.loads(manifest_path.read_bytes())
    changed["provenance"]["source_hash"] = "0"*64
    manifest_path.write_text(json.dumps(changed))
    rejected = subprocess.run([sys.executable, "-c", "from IPython.display import display\n"+"\n\n".join(cells)],
        env=env, capture_output=True, text=True, timeout=45)
    assert rejected.returncode != 0 and "incompatible source_hash" in rejected.stderr

"""Fresh-process notebook execution with real models, synthetic data and bare Git."""
from hashlib import sha256
from importlib.util import find_spec
import json
import os
from pathlib import Path
import subprocess
import sys

import numpy as np
import pandas as pd
import pytest
import yaml

if not find_spec("tensorflow") or not find_spec("xgboost"):
    pytest.skip("P6 uses P5 model dependencies", allow_module_level=True)

from airsense_r.artifacts import RunStore, json_bytes
from airsense_r.p4 import synthetic_stream
from airsense_r.p5 import tune_and_select, evaluate_test
from airsense_r.p5_recovery import PARENT_RUN
from airsense_r.training.settings import configure_cpu, load_plan

ROOT = Path(__file__).resolve().parents[1]


def test_p6_notebook_preflight_interrupted_evaluation_and_resume(tmp_path):
    """Exercise all corruption kinds/policies with actual saved XGB/MLP/GRU models."""
    configure_cpu()
    config = yaml.safe_load((ROOT / "configs/experiment.yaml").read_text())
    config["data"].update(train_target_start="2014-01-02 00:00", train_target_end="2014-01-03 23:00",
        validation_target_start="2014-01-04 00:00", validation_target_end="2014-01-04 23:00",
        test_target_start="2014-01-05 00:00", test_target_end="2014-01-08 23:00")
    config["models"]["internal_folds"] = [{"fit_end": "2014-01-02 23:00",
        "validation_start": "2014-01-03 00:00", "validation_end": "2014-01-03 23:00"}]
    config["corruptions"].update(random_dropout_levels=[0.3], noise_levels=[0.1],
        whole_variable_dropout=["NO2"], contiguous_outage_channels=["CO"], contiguous_outage_hours=[6])
    config["seeds"]["corruption"] = [101, 202]
    config["uncertainty"]["n_bootstrap"] = 12
    plan = load_plan(ROOT)
    for family in plan["families"]:
        plan["families"][family] = [{**plan["families"][family][0], "epochs": 1, "rounds": 2}]
    parts = []
    for _, g in synthetic_stream().groupby("station"):
        f = g.iloc[np.arange(192) % len(g)].copy().reset_index(drop=True)
        f["timestamp"] = pd.date_range("2014-01-01", periods=192, freq="h")
        parts.append(f)
    frame = pd.concat(parts, ignore_index=True)
    frame.loc[frame.timestamp == "2014-01-04 12:00", "PM2.5"] = 74.3
    frame.loc[frame.timestamp == "2014-01-04 13:00", "PM2.5"] = 81.8
    frame.to_csv(tmp_path / "frame.csv", index=False, float_format="%.17g")
    # Fit on exactly the same losslessly parsed fixture used by subprocesses.
    frame = pd.read_csv(tmp_path / "frame.csv", float_precision="round_trip", parse_dates=["timestamp"])
    prov = {"config": config, "training_plan": plan, "synthetic_fixture_only": True,
        "parameters": {"model_storage_id": "fixture-storage"},
        **{key: "fixture" for key in ("config_hash", "protocol_hash", "dataset_sha256", "training_plan_hash")}}
    parent = RunStore(tmp_path / "parent", prov)
    model_root = tmp_path / "models"
    (model_root / PARENT_RUN).mkdir(parents=True)
    (model_root / "storage.json").write_bytes(json_bytes({"storage_id": "fixture-storage"}))
    development = frame.loc[frame.timestamp <= config["data"]["validation_target_end"]]
    decision = tune_and_select(development, parent, model_root / PARENT_RUN)
    evaluate_test(frame, parent, model_root / PARENT_RUN, decision)
    parent.save("validation-replay-complete.json", json_bytes({"passed": True}))
    parent_before = parent.manifest_path.read_bytes()
    pointers = {p: p.read_bytes() for p in model_root.glob("*/**/progress.json")}
    remote = tmp_path / "remote.git"
    subprocess.run(["git", "init", "--bare", str(remote)], check=True, capture_output=True)
    run_id = "p6-fixture-"+sha256(str(tmp_path).encode()).hexdigest()[:16]
    env = {**os.environ, "AIRSENSE_NOTEBOOK_TEST_MODE": "1", "AIRSENSE_NOTEBOOK_TEST_ROOT": str(ROOT),
        "AIRSENSE_NOTEBOOK_TEST_RUN": run_id, "AIRSENSE_NOTEBOOK_TEST_REMOTE": str(remote)}
    import nbformat
    notebook = nbformat.read(ROOT / "notebooks/05_p6_sensor_degradation_analysis.ipynb", as_version=4)
    nbformat.validate(notebook)
    cells = "\n\n".join(c.source for c in notebook.cells if c.cell_type == "code")
    fixture = '''
from pathlib import Path
from contextlib import contextmanager
import json, builtins, subprocess
import pandas as pd
from IPython.display import display
from airsense_r.artifacts import RunStore
from airsense_r.training.settings import configure_cpu
import airsense_r.p6 as p6
configure_cpu()
fixture_root = Path(FIXTURE_ROOT)
manifest = json.loads((fixture_root / "parent/manifest.json").read_text())
parent = RunStore(fixture_root / "parent", manifest["provenance"])
p6.accepted_clean = lambda *args: parent
p6.training_provenance = lambda root, params: {**manifest["provenance"], "parameters": params}
@contextmanager
def acquire():
    yield fixture_root, {}
p6.temporary_uci_dataset = acquire
p6.load_receipt = lambda *args: {}
p6.assert_same_acquisition = lambda *args: None
def read(root, end):
    data = pd.read_csv(fixture_root / "frame.csv", float_precision="round_trip", parse_dates=["timestamp"])
    return data.loc[data.timestamp <= pd.Timestamp(end)].copy()
p6.read_stations = read
def forbidden_fit(*args, **kwargs):
    raise AssertionError("P6 must never fit a model")
import airsense_r.models.learned as learned
import airsense_r.p5 as p5
learned.fit_model = p5.fit_model = forbidden_fit
original_predict = p6.predict_model
calls = 0
def predict(*args, **kwargs):
    global calls
    calls += 1
    if INTERRUPT and calls == 3:
        raise InterruptedError("Synthetic interruption during prediction")
    if FORBID_PREDICT:
        raise AssertionError("Completed predictions must be reused")
    return original_predict(*args, **kwargs)
p6.predict_model = predict
answers = iter([STAGE_TEST, str(fixture_root / "models")])
builtins.input = lambda prompt="": next(answers)
# Run the actual CLI in this fresh process with explicit fixture acquisition.
# Popen below is a fixture only; real Colab uses a separate streamed child process.
original_popen = subprocess.Popen
class FixtureProcess:
    def __init__(self, command, **kwargs):
        from scripts.run_sensor_degradation import main
        import sys
        previous = sys.argv
        try:
            sys.argv = command[1:]
            main()
        finally:
            sys.argv = previous
        self.stdout = iter([])
    def __enter__(self): return self
    def __exit__(self, *args): return False
    def wait(self): return 0
    def terminate(self): pass
def fixture_popen(command, **kwargs):
    if len(command) > 1 and str(command[1]).endswith("run_sensor_degradation.py"):
        return FixtureProcess(command, **kwargs)
    return original_popen(command, **kwargs)
subprocess.Popen = fixture_popen
'''
    def execute(stage, interrupt=False, forbid=False):
        program = f"FIXTURE_ROOT={str(tmp_path)!r}\nSTAGE_TEST={stage!r}\nINTERRUPT={interrupt!r}\nFORBID_PREDICT={forbid!r}\n"+fixture+cells
        # Hundreds of real bare-Git checkpoint subprocesses are slower on Windows.
        return subprocess.run([sys.executable, "-c", program], env=env, capture_output=True, text=True, timeout=600)
    first = execute("preflight")
    assert first.returncode == 0, first.stdout+first.stderr
    failure = execute("evaluate", interrupt=True)
    assert failure.returncode != 0 and "Synthetic interruption" in failure.stderr
    saved = model_root / "p6-artifacts" / run_id
    completed = {p: p.read_bytes() for p in saved.glob("pred-primary-random_dropout*.npz")}
    assert completed
    resumed = execute("evaluate")
    assert resumed.returncode == 0, resumed.stdout+resumed.stderr
    assert all(p.read_bytes() == b for p, b in completed.items())
    rerun = execute("evaluate", forbid=True)
    assert rerun.returncode == 0, rerun.stdout+rerun.stderr
    output = ROOT / ".tmp/checkpoint-checkouts" / run_id / "results" / run_id
    manifest = json.loads((output / "manifest.json").read_text())
    result = RunStore(output, manifest["provenance"])
    assert result.load_json("complete.json")["sensor_degradation_complete"]
    assert len(result.load_json("dashboard-p6.json")["reports"]) == 8
    assert parent.manifest_path.read_bytes() == parent_before
    assert all(p.read_bytes() == b for p, b in pointers.items())
    head = subprocess.check_output(["git", "--git-dir", str(remote), "rev-parse", f"refs/heads/results/{run_id}"], text=True).strip()
    local = subprocess.check_output(["git", "-C", str(output.parents[1]), "rev-parse", "HEAD"], text=True).strip()
    assert head == local

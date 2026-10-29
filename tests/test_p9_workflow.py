"""Actual native prediction reloads and fresh-process P9 notebook lifecycle."""
from hashlib import sha256
from importlib.util import find_spec
import json
import os
from pathlib import Path
import subprocess
import sys

import nbformat
import numpy as np
import pytest

from airsense_r.data.pipeline import CausalPreprocessor, build_windows
from airsense_r.p4 import synthetic_stream
from airsense_r.p5_recovery import local_writer_lock
from airsense_r.target_history import corrupt_history, cases
from scripts.build_target_history_notebook import build

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("family", ["xgboost", "mlp", "gru"])
@pytest.mark.skipif(not find_spec("tensorflow") or not find_spec("xgboost"), reason="Native training extras required")
def test_target_history_native_reload_in_fresh_process(tmp_path, family):
    import pandas as pd
    import yaml
    from airsense_r.artifacts import json_bytes
    from airsense_r.models.learned import fit_model, predict_model
    from airsense_r.training.settings import configure_cpu, load_plan
    from airsense_r.training.storage import ModelCheckpoint
    configure_cpu()
    frame = synthetic_stream()
    frame.loc[frame.timestamp == "2014-01-03 12:00", "PM2.5"] = 74.3
    frame.loc[frame.timestamp == "2014-01-03 13:00", "PM2.5"] = 81.8
    frame.to_csv(tmp_path / "frame.csv", index=False, float_format="%.17g")
    frame = pd.read_csv(tmp_path / "frame.csv", float_precision="round_trip", parse_dates=["timestamp"])
    prep = CausalPreprocessor().fit(frame, "2014-01-02 23:00")
    (tmp_path / "processor.json").write_bytes(json_bytes(prep.state))
    plan = load_plan(ROOT)
    candidate = {**plan["families"][family][0], "epochs": 1, "rounds": 2}
    checkpoint = ModelCheckpoint(tmp_path / "model", {"family": family})
    windows = build_windows(frame, prep, scaled=family != "xgboost")
    model = fit_model(family, candidate, 42, windows, np.arange(24), checkpoint, plan)
    config = yaml.safe_load((ROOT / "configs/experiment.yaml").read_text())
    config["data"].update(test_target_start="2014-01-03", test_target_end="2014-01-04 23:00")
    (tmp_path / "config.json").write_bytes(json_bytes(config))
    stressed, _, _ = corrupt_history(frame, config, cases()[-1], 101)
    score = build_windows(stressed, prep, targets=frame, scaled=family != "xgboost")
    expected = predict_model(family, model, score, np.arange(len(score.y)))
    program = '''
import json, sys
from pathlib import Path
import numpy as np, pandas as pd
from airsense_r.training.settings import configure_cpu
configure_cpu()
from airsense_r.models.learned import load_model, predict_model
from airsense_r.training.storage import ModelCheckpoint
from airsense_r.data.pipeline import CausalPreprocessor, build_windows
from airsense_r.target_history import corrupt_history, cases
p=Path(sys.argv[1]); family=sys.argv[2]
frame=pd.read_csv(p/'frame.csv',float_precision='round_trip',parse_dates=['timestamp'])
prep=CausalPreprocessor.from_state(json.loads((p/'processor.json').read_bytes()))
stressed,_,_=corrupt_history(frame,json.loads((p/'config.json').read_bytes()),cases()[-1],101)
w=build_windows(stressed,prep,targets=frame,scaled=family!='xgboost')
model=load_model(family,ModelCheckpoint(p/'model',{'family':family}))
np.savez(p/'reloaded.npz',prediction=predict_model(family,model,w,np.arange(len(w.y))),y=w.y,x=w.features)
'''
    result = subprocess.run([sys.executable, "-c", program, str(tmp_path), family], capture_output=True, text=True, timeout=120)
    assert result.returncode == 0, result.stdout + result.stderr
    with np.load(tmp_path / "reloaded.npz", allow_pickle=False) as actual:
        np.testing.assert_array_equal(actual["y"], score.y)
        np.testing.assert_array_equal(actual["x"], score.features)
        np.testing.assert_allclose(actual["prediction"], expected, atol=1e-5, rtol=1e-6)


def test_fresh_notebook_rerun_and_duplicate_writer(tmp_path):
    notebook = build("a" * 40)
    nbformat.validate(nbformat.from_dict(notebook))
    cells = [c["source"] for c in notebook["cells"] if c["cell_type"] == "code"]
    assert len(cells) == 4 and '[train,notebooks]' in cells[0] and 'input(' not in cells[0]
    run_id = "p9-fixture-" + sha256(str(tmp_path).encode()).hexdigest()[:12]
    (tmp_path / "storage.json").write_text('{}')
    output = ROOT / ".tmp/checkpoint-checkouts" / run_id / "results" / run_id
    child = (
        "from pathlib import Path; from airsense_r.artifacts import RunStore,json_bytes,source_hash; "
        f"s=RunStore(Path({str(output)!r}),{{'source_hash':source_hash(Path({str(ROOT)!r})),'parameters':{{'run_id':{run_id!r}}}}}); "
        "s.save('preflight-complete.json',json_bytes({'passed':True})); "
        "s.save('complete.json',json_bytes({'execution_complete':True})); "
        "s.save('dashboard-target-history.json',json_bytes({'synthetic_only':True}))"
    )
    env = {**os.environ, "AIRSENSE_NOTEBOOK_TEST_MODE": "1", "AIRSENSE_NOTEBOOK_TEST_ROOT": str(ROOT),
           "AIRSENSE_P9_TEST_MODELS": str(tmp_path), "AIRSENSE_P9_TEST_RUN": run_id,
           "AIRSENSE_P9_TEST_COMMAND": json.dumps([sys.executable, "-c", child])}
    for _ in range(2):
        result = subprocess.run([sys.executable, "-c", "from IPython.display import display\n" + "\n".join(cells)],
                                env=env, capture_output=True, text=True, timeout=90)
        assert result.returncode == 0, result.stdout + result.stderr
        assert "EXECUTION COMPLETE" in result.stdout
    lock = tmp_path / "writer.lock"
    command = [sys.executable, "-c", "from pathlib import Path; from airsense_r.p5_recovery import local_writer_lock; "
               f"\nwith local_writer_lock(Path({str(lock)!r})): print('locked')"]
    with local_writer_lock(lock):
        blocked = subprocess.run(command, capture_output=True, text=True, timeout=30)
        assert blocked.returncode != 0 and "already running" in blocked.stderr
    assert subprocess.run(command, capture_output=True, timeout=30).returncode == 0


@pytest.mark.skipif(not find_spec("tensorflow") or not find_spec("xgboost"), reason="Native training extras required")
def test_runner_replays_before_test_access_and_never_refits(tmp_path, monkeypatch):
    """Exercise the actual entry point with native models and isolated synthetic data."""
    from contextlib import contextmanager
    import pandas as pd
    import yaml
    from airsense_r.artifacts import RunStore, json_bytes
    from airsense_r.p5 import tune_and_select, evaluate_test
    from airsense_r.p5_recovery import PARENT_RUN
    from airsense_r.training.settings import configure_cpu, load_plan
    import airsense_r.target_history as extension
    import scripts.run_target_history as runner
    configure_cpu()
    config = yaml.safe_load((ROOT / "configs/experiment.yaml").read_text())
    config["data"].update(train_target_start="2014-01-02", train_target_end="2014-01-03 23:00",
        validation_target_start="2014-01-04", validation_target_end="2014-01-04 23:00",
        test_target_start="2014-01-05", test_target_end="2014-01-06 23:00")
    config["models"]["internal_folds"] = [{"fit_end": "2014-01-02 23:00",
        "validation_start": "2014-01-03", "validation_end": "2014-01-03 23:00"}]
    config["seeds"]["training"] = [42]
    config["uncertainty"]["n_bootstrap"] = 12
    plan = load_plan(ROOT)
    for family in plan["families"]:
        plan["families"][family] = [{**plan["families"][family][0], "epochs": 1, "rounds": 2}]
    parts = []
    for _, group in synthetic_stream().groupby("station"):
        f = group.iloc[np.arange(144) % len(group)].copy().reset_index(drop=True)
        f["timestamp"] = pd.date_range("2014-01-01", periods=144, freq="h")
        parts.append(f)
    frame = pd.concat(parts, ignore_index=True)
    frame.loc[frame.timestamp == "2014-01-04 12:00", "PM2.5"] = 74.3
    frame.loc[frame.timestamp == "2014-01-04 13:00", "PM2.5"] = 81.8
    prov = {"config": config, "training_plan": plan, "synthetic_only": True,
            "parameters": {"model_storage_id": "fixture"},
            **{k: "fixture" for k in ("config_hash", "protocol_hash", "dataset_sha256", "training_plan_hash")}}
    parent = RunStore(tmp_path / "parent", prov)
    storage = tmp_path / "storage"
    storage.mkdir()
    (storage / "storage.json").write_bytes(json_bytes({"storage_id": "fixture"}))
    development = frame.loc[frame.timestamp <= config["data"]["validation_target_end"]]
    selection = tune_and_select(development, parent, storage / PARENT_RUN)
    evaluate_test(frame, parent, storage / PARENT_RUN, selection)
    before = {p: sha256(p.read_bytes()).hexdigest() for p in (storage / PARENT_RUN).rglob("*") if p.is_file()}
    parent_before = parent.manifest_path.read_bytes()
    output = RunStore(tmp_path / "extension", {**prov, "extension": True})
    monkeypatch.setattr(runner, "accepted_clean", lambda *a: parent)
    monkeypatch.setattr(runner, "training_provenance", lambda *a: prov)
    monkeypatch.setattr(runner, "open_run", lambda *a: output)
    @contextmanager
    def acquire():
        yield tmp_path, {}
    monkeypatch.setattr(runner, "temporary_uci_dataset", acquire)
    monkeypatch.setattr(runner, "assert_same_acquisition", lambda *a: None)
    monkeypatch.setattr(runner, "load_receipt", lambda *a: {})
    replayed = []
    verify = runner.verify_validation
    def replay(*args):
        verify(*args)
        replayed.append(True)
    monkeypatch.setattr(runner, "verify_validation", replay)
    def read(root, end):
        if end == config["data"]["test_target_end"]:
            assert replayed, "Test accessed before native development replay"
        return frame.loc[frame.timestamp <= end].copy()
    monkeypatch.setattr(runner, "read_stations", read)
    def forbidden(*args, **kwargs):
        raise AssertionError("Extension must not fit")
    monkeypatch.setattr("airsense_r.models.learned.fit_model", forbidden)
    monkeypatch.setattr("airsense_r.p5.fit_model", forbidden)
    small_cases = [cases()[1], cases()[-1]]
    monkeypatch.setattr(extension, "cases", lambda: small_cases)
    # Synthetic fixture only; the production matrix remains five seeds/cases.
    monkeypatch.setitem(extension.SETTINGS, "corruption_seeds", [101])
    runner.run(ROOT, storage, "fixture")
    runner.run(ROOT, storage, "fixture")
    assert len(replayed) == 2 and output.load_json("complete.json")["execution_complete"]
    assert parent.manifest_path.read_bytes() == parent_before
    assert all(sha256(p.read_bytes()).hexdigest() == digest for p, digest in before.items())

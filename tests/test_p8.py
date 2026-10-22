"""Read-only diagnostics, immutable evidence, notebook resume and packaging."""
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys
import tomllib

import nbformat
import numpy as np
import pandas as pd
import pytest
import yaml

from airsense_r.artifacts import RunStore, source_hash
from airsense_r.evaluation.failure_analysis import seed_average, diagnostics
from airsense_r.evaluation.p6_verify import Snapshot
from airsense_r.p8 import sensor_analysis

ROOT = Path(__file__).resolve().parents[1]


def settings():
    return yaml.safe_load((ROOT / "configs/p8_analysis.yaml").read_text())


def test_errors_are_averaged_not_ensemble_predictions():
    p = pd.DataFrame({"station": ["A"]*4, "model": ["mlp"]*4,
        "target_timestamp": ["2016-03-01"]*2+["2016-12-01"]*2,
        "y_true": [74.3]*2+[200.]*2, "y_pred": [64.3, 84.3, 180., 220.]})
    points = seed_average(p)
    np.testing.assert_allclose(points.absolute_error, [10, 20])
    np.testing.assert_allclose(points.bias, [0, 0])
    tables = diagnostics(points, settings())
    assert set(tables["concentration_band"].concentration_band) == {"50 to <100", ">=200"}
    assert set(tables["season"].season) == {"MAM", "DJF"}
    assert tables["worst-cases"].absolute_error.tolist() == [20., 10.]
    # Equal station weighting, even when target counts differ.
    other = points.iloc[[0]].assign(station="B", absolute_error=30.)
    extra = points.iloc[[0]].assign(target_timestamp=pd.Timestamp('2016-03-02'))
    table = diagnostics(pd.concat([points, extra, other]), settings())["concentration_band"]
    row = table.loc[table.concentration_band == "50 to <100"].iloc[0]
    assert row.mae == 20 and row.stations == 2 and row.targets == 3
    with pytest.raises(ValueError, match="duplicate"):
        diagnostics(pd.concat([points, points]), settings())


def test_sensor_diagnostics_interrupt_resume_reverify_and_preserve(tmp_path):
    from test_p6_verification import fixture
    parent, drive = fixture(tmp_path)
    original = {p: p.read_bytes() for folder in [drive, parent.directory] for p in folder.rglob('*') if p.is_file()}
    output = RunStore(tmp_path / "analysis", {"fixture": True})
    def interrupt(message):
        if "random_dropout" in message:
            raise InterruptedError("fixture interruption")
    with pytest.raises(InterruptedError):
        sensor_analysis(Snapshot(parent.directory), drive, output, settings(), interrupt)
    saved = {n: output._path(n).read_bytes() for n in output.manifest["artifacts"]}
    assert saved and any(n.endswith(".png") for n in saved)
    sensor_analysis(Snapshot(parent.directory), drive, output, settings(), lambda _: None)
    assert output.load_json("p6-files-verified.json")["bundle_files"] == 43
    assert all(output._path(n).read_bytes() == b for n,b in saved.items())
    assert all(p.read_bytes() == b for p,b in original.items())
    path = drive / "pred-primary-clean-xgboost-42.npz"
    path.write_bytes(path.read_bytes()+b"tampered")
    with pytest.raises(ValueError, match="Drive file differs"):
        sensor_analysis(Snapshot(parent.directory), drive, output, settings(), lambda _: None)


def test_four_p8_cells_fresh_process_resume_and_provenance(tmp_path):
    from scripts.build_p8_notebook import build
    notebook = nbformat.reads(json.dumps(build('a'*40)), as_version=4); nbformat.validate(notebook)
    cells = [c.source for c in notebook.cells if c.cell_type == 'code']
    assert len(cells) == 4 and all('input(' not in c for c in cells)
    run = 'p8-fixture-'+sha256(str(tmp_path).encode()).hexdigest()[:12]
    output = ROOT / '.tmp/checkpoint-checkouts' / run / 'results' / run
    (tmp_path / 'storage.json').write_text('{}')
    provenance = {'source_hash': source_hash(ROOT), 'run_id': run}
    child = f"from pathlib import Path; from airsense_r.artifacts import RunStore,json_bytes; s=RunStore(Path({str(output)!r}),{provenance!r}); s.save('p7-verification.json',json_bytes({{'passed':True}})); s.save('complete.json',json_bytes({{'execution_complete':True}})); s.save('dashboard-p8.json',json_bytes({{'synthetic_only':True}}))"
    env = {**os.environ, 'AIRSENSE_NOTEBOOK_TEST_MODE':'1', 'AIRSENSE_NOTEBOOK_TEST_ROOT':str(ROOT),
        'AIRSENSE_P8_TEST_MODELS':str(tmp_path), 'AIRSENSE_P8_TEST_RUN':run,
        'AIRSENSE_P8_TEST_COMMAND':json.dumps([sys.executable,'-c',child])}
    program = 'from IPython.display import display\n'+'\n\n'.join(cells)
    for _ in range(2):
        result = subprocess.run([sys.executable,'-c',program],env=env,capture_output=True,text=True,timeout=60)
        assert result.returncode == 0, result.stdout+result.stderr
        assert 'P8 EXECUTION COMPLETE' in result.stdout
    manifest = json.loads((output/'manifest.json').read_bytes())
    manifest['provenance']['source_hash'] = '0'*64
    (output/'manifest.json').write_text(json.dumps(manifest))
    result = subprocess.run([sys.executable,'-c',program],env=env,capture_output=True,text=True,timeout=60)
    assert result.returncode != 0 and 'provenance mismatch' in result.stderr


def test_one_dependency_definition_and_executed_notebook_preservation():
    config = tomllib.loads((ROOT/'pyproject.toml').read_text())['project']
    assert set(config['optional-dependencies']) == {'train','notebooks','dev'}
    assert (ROOT/'requirements.txt').read_text().splitlines()[-1] == '-e .[train,notebooks,dev]'
    assert len(list(ROOT.glob('requirements*.txt'))) == 1
    index = json.loads((ROOT/'notebooks/executed/index.json').read_bytes())
    for item in index.values():
        assert sha256((ROOT/item['path']).read_bytes()).hexdigest() == item['sha256']


def test_pinned_snapshot_refuses_local_edits(tmp_path):
    from scripts.run_failure_analysis import snapshot
    remote = tmp_path/'remote'
    remote.mkdir()
    def git(*args):
        return subprocess.check_output(['git','-C',str(remote),*args],text=True,stderr=subprocess.DEVNULL).strip()
    git('init'); git('config','user.name','Fixture'); git('config','user.email','fixture@example.invalid')
    git('checkout','-b','results/input')
    store=RunStore(remote/'results/input',{'fixture':True})
    store.save('complete.json',b'{"passed":true}\n')
    git('add','.');git('commit','-m','Synthetic input')
    commit=git('rev-parse','HEAD')
    result=snapshot(tmp_path/'workspace',str(remote),'input',commit)
    assert result.json('complete.json')['passed']
    checkout=tmp_path/'workspace/.tmp/p8-inputs/input'
    (checkout/'untracked.txt').write_text('preserve me')
    with pytest.raises(ValueError,match='snapshot differs'):
        snapshot(tmp_path/'workspace',str(remote),'input',commit)
    assert (checkout/'untracked.txt').read_text()=='preserve me'


def test_analysis_assembly_keeps_acceptance_pending(tmp_path, monkeypatch):
    from test_p6_verification import fixture
    from airsense_r.artifacts import json_bytes
    import airsense_r.p8 as module
    parent, drive = fixture(tmp_path/'storage/p6-artifacts')
    drive.rename(drive.parent/'p6-sensors-01')
    output = RunStore(tmp_path/'output', {'synthetic_only':True})
    interval = {'estimate':0.2,'ci_low':0.1,'ci_high':0.4}
    site = {'selected_family':'persistence','kendall_tau_b':1.,
            'within_practical_near_tie':True,'selection_regret':interval}
    # Native verification has its own full integration test. Here isolate the
    # assembly boundary and exercise every downstream table/figure/output gate.
    def verified(*args):
        output.save('p7-independent-report.json',json_bytes({'stations':{'A':site},
            'practical_threshold_ug_m3':1.,'mean_station_selection_regret':interval}))
        return pd.DataFrame({'station':['A'],'model':['persistence'],'seed':[-1],
            'target_timestamp':['2016-03-01'],'y_true':[74.3],'y_pred':[81.8]})
    monkeypatch.setattr(module,'verify_run',verified)
    result = module.run_analysis(None,Snapshot(parent.directory),tmp_path/'storage',output,settings(),lambda _:None)
    assert result['execution_complete'] and not result['scientifically_accepted']
    assert result['no_models_fitted_or_predicted']
    assert output._path('site-selection-regret.png').read_bytes().startswith(b'\x89PNG')
    assert output.load_json('dashboard-p8.json')['status']=='awaiting_independent_review'
    with pytest.raises(ValueError,match='tolerances differ'):
        module.run_analysis(None,None,tmp_path,output,{**settings(),'comparison_atol':1.},lambda _:None)

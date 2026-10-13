"""Independent arithmetic, immutable file verification and review recovery."""
from hashlib import sha256
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from airsense_r.artifacts import RunStore, json_bytes
from airsense_r.evaluation.p6_verify import (Snapshot, read_bundle, sampling_weights,
    independently_bootstrap, compare_numbers, verify_saved_run, affected_targets)
from airsense_r.evaluation.stress_summary import stress_intervals, reliability_summary
from airsense_r.p6 import score_rows, error_calendar
from airsense_r.p6_storage import PredictionBundles


def settings():
    return {"uncertainty": {"n_bootstrap": 25, "block_length_hours": 7, "confidence": .95},
            "seeds": {"bootstrap": 424242, "training": [42, 31415]},
            "models": {"candidates": ["persistence", "xgboost", "mlp", "gru"]},
            "data": {"test_target_start": "2016-01-01 00:00", "test_target_end": "2016-01-03 01:00", "lookback_hours": 24}}


def test_independent_bootstrap_partial_last_block_masks_and_oracle():
    c = settings(); rng = np.random.default_rng(123)
    models = ['persistence', 'xgboost', 'mlp', 'gru']
    clean = rng.uniform(1, 5, (2, 4, 2, 50)); stress = clean + rng.uniform(-1, 1, clean.shape)
    clean[0, :, :, 3] = np.nan; stress[0, :, :, 3] = np.nan
    clean[1, :, :, 10] = np.nan; stress[1, :, :, 10] = np.nan
    weights = sampling_weights(50, c)
    assert np.all(weights.sum(axis=1) == 50)
    actual = independently_bootstrap(clean, stress, weights, models, ["A", "B"], "persistence", .95)
    expected = stress_intervals(clean, stress, models, "persistence", ["A", "B"], c)
    compare_numbers(actual, expected)
    # A changed bound must be detected, not merely a successful function call.
    expected["selection_regret"]["ci_high"] += .1
    with pytest.raises(AssertionError):
        compare_numbers(actual, expected)
    sparse = np.full((1, 2, 2, 50), np.nan); sparse[..., 0] = 2
    assert not independently_bootstrap(sparse, sparse, weights, ["persistence", "xgboost"], ["A", "B"], "persistence", .95)["available"]


def test_outage_target_intersection_boundaries_and_station_isolation():
    time = pd.date_range('2016-01-01',periods=50,freq='h').to_numpy().astype('int64')
    events=[{'station':'A','start':'2016-01-01 04:00','end':'2016-01-01 09:00'}]
    mask=affected_targets(np.repeat(['A','B'],50),np.tile(time,2),events,24)
    assert np.flatnonzero(mask).tolist()==list(range(5,34))


def fixture(tmp_path: Path):
    c = settings(); parent = RunStore(tmp_path / "parent", {"config": c})
    bundles = PredictionBundles(tmp_path / "drive", parent)
    target = {"station": np.repeat(["A", "B"], 50),
        "time": np.tile(pd.date_range(c["data"]["test_target_start"], periods=50, freq="h").to_numpy().astype('int64'), 2),
        "y": np.tile(np.array([74.3, 81.8, 60.2, 42.7, 30.5]), 20)}
    bundles.save("targets", target)
    parent.save("lineage.json", json_bytes({"selection": {"selected_family": "persistence"}}))
    rng = np.random.default_rng(8); reports = []
    for policy in ['primary', 'no_ffill']:
        clean = {(m, s): target['y'] + rng.normal(size=100)
                 for m in c['models']['candidates']
                 for s in ([-1] if m == 'persistence' else c['seeds']['training'])}
        for (m, s), values in clean.items(): bundles.save(f'pred-{policy}-clean-{m}-{s}', {'prediction': values})
        spec = {'id': 'random_dropout-10', 'kind': 'random_dropout', 'seeds': [101, 202]}
        rows=[]; a=[]; b=[]
        for seed in spec['seeds']:
            unit=f"random_dropout-10-c{seed}"
            pred={key: values + (0 if key[0]=='persistence' else rng.normal(size=100)) for key,values in clean.items()}
            for (m,s), values in pred.items(): bundles.save(f'pred-{policy}-{unit}-{m}-{s}', {'prediction':values})
            mask=np.ones(100,dtype=bool)
            metric=score_rows(pred,clean,target,{'full':mask},seed)
            parent.save(f'metrics-{policy}-{unit}.csv',metric.to_csv(index=False).encode())
            rows.append(metric); a.append(error_calendar(clean,target,mask,c)); b.append(error_calendar(pred,target,mask,c))
        summary=reliability_summary(pd.concat(rows),'persistence',1)
        summary['uncertainty']=stress_intervals(np.array(a),np.array(b),c['models']['candidates'],'persistence',['A','B'],c)
        reports.append({'policy':policy,'condition':spec,'scopes':{'full':summary}})
    parent.save('dashboard-p6.json',json_bytes({'reports':reports}))
    parent.save('complete.json',json_bytes({'sensor_degradation_complete':True,'conditions_per_policy':1}))
    return parent, tmp_path/'drive'


def test_saved_file_review_interrupt_resume_and_tamper(tmp_path, monkeypatch):
    parent, drive = fixture(tmp_path)
    before = parent.manifest_path.read_bytes()
    snapshot = Snapshot(parent.directory)
    output = RunStore(tmp_path/'review', {'input':sha256(before).hexdigest()})
    def interrupt(message):
        if message.startswith('Saved and synchronized review 1/'):
            raise InterruptedError('fixture interruption')
    with pytest.raises(InterruptedError):
        verify_saved_run(snapshot, drive, output, interrupt)
    assert output.has('review-primary-random_dropout-10.json') and not output.has('complete.json')
    result=verify_saved_run(snapshot,drive,output,lambda _: None)
    assert result['passed'] and result['prediction_files']==43
    assert parent.manifest_path.read_bytes()==before
    import airsense_r.evaluation.p6_verify as module
    monkeypatch.setattr(module,'independently_bootstrap',lambda *a: (_ for _ in ()).throw(AssertionError('must reuse review')))
    assert verify_saved_run(snapshot,drive,output,lambda _:None)['passed']
    # Even completed reruns reverify Drive files before reusing reviews.
    path=drive/'pred-primary-clean-xgboost-42.npz'; path.write_bytes(path.read_bytes()+b'corrupt')
    with pytest.raises(ValueError, match='Drive file differs'):
        verify_saved_run(snapshot,drive,output,lambda _:None)


def test_reference_tampering_and_identity_mismatch(tmp_path):
    parent,drive=fixture(tmp_path); snap=Snapshot(parent.directory)
    (drive/'identity.json').write_text('{}')
    with pytest.raises(ValueError,match='identity'):
        verify_saved_run(snap,drive,RunStore(tmp_path/'review',{}))
    (parent.directory/'complete.json').write_text('{}')
    with pytest.raises(ValueError,match='Corrupt Git'):
        Snapshot(parent.directory)
    snap.blobs['bundle-targets.json']=json_bytes({'file':'../targets.npz'})
    with pytest.raises(ValueError,match='filename'):
        read_bundle(drive,'targets',snap)

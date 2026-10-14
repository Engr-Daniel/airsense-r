"""Actual fresh worker processes, reconnect, failure and stale-lock recovery."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time

import pytest

from airsense_r.artifacts import atomic_write, json_bytes
from airsense_r.notebook_job import start_or_attach, status, lock


def wait(directory):
    for _ in range(200):
        state=status(directory)
        if state['state']!='running': return state
        time.sleep(.1)
    pytest.fail('Fixture worker did not finish')


def test_attach_runs_command_once_and_reuses_completion(tmp_path):
    count=tmp_path/'count.txt'; job=tmp_path/'job'
    command=[sys.executable,'-c',f"from pathlib import Path; import time; p=Path({str(count)!r}); p.write_text(p.read_text()+'x' if p.exists() else 'x'); print('progress',flush=True); time.sleep(2)"]
    assert start_or_attach(command,job,Path.cwd())['state']=='running'
    assert start_or_attach(command,job,Path.cwd())['state']=='running'
    assert wait(job)['state']=='complete'
    assert start_or_attach(command,job,Path.cwd())['state']=='complete'
    assert count.read_text()=='x'
    with pytest.raises(ValueError,match='different'):
        start_or_attach([sys.executable,'-c','pass'],job,Path.cwd())
    assert (job/'worker.lock').exists()


def test_failed_job_resumes_and_stale_lock_is_not_deleted(tmp_path):
    flag=tmp_path/'first'; job=tmp_path/'job'
    command=[sys.executable,'-c',f"from pathlib import Path; import sys; p=Path({str(flag)!r}); failed=not p.exists(); p.write_text('saved'); sys.exit(3 if failed else 0)"]
    start_or_attach(command,job,Path.cwd()); assert wait(job)['state']=='failed'
    atomic_write(job/'status.json',json_bytes({'state':'running'}))
    assert status(job)['state']=='interrupted'
    start_or_attach(command,job,Path.cwd()); assert wait(job)['state']=='complete'
    assert (job/'worker.lock').exists()


def test_job_lock_blocks_fresh_process(tmp_path):
    path=tmp_path/'shared.lock'
    with lock(path) as held:
        assert held
        program=f"from pathlib import Path; from airsense_r.notebook_job import lock\nwith lock(Path({str(path)!r})) as held:\n assert not held\n"
        result=subprocess.run([sys.executable,'-c',program],capture_output=True,text=True,timeout=20)
        assert result.returncode==0,result.stderr


def test_four_review_notebook_cells_in_fresh_process(tmp_path, monkeypatch):
    import nbformat
    from hashlib import sha256
    root=Path(__file__).resolve().parents[1]
    path=root/'notebooks/05b_p6_saved_result_verification.ipynb'
    n=nbformat.read(path,as_version=4); nbformat.validate(n)
    # The published review is pinned to historical P6 source; preserve it.
    # Exercise the current generator/worker together without rewriting that file.
    from scripts import build_p6_review_notebook as builder
    generated = {}
    original_write = Path.write_text
    def capture(path, text, *args, **kwargs):
        if path.name == '05b_p6_saved_result_verification.ipynb':
            generated['notebook'] = text
            return len(text)
        return original_write(path, text, *args, **kwargs)
    with monkeypatch.context() as patch:
        patch.setattr(Path, 'write_text', capture)
        patch.setattr(sys, 'argv', ['builder', '--revision', 'a'*40])
        builder.main()
    n = nbformat.reads(generated['notebook'], as_version=4)
    nbformat.validate(n)
    cells=[c.source for c in n.cells if c.cell_type=='code']
    assert len(cells)==4 and all('input(' not in c for c in cells)
    run='review-fixture-'+sha256(str(tmp_path).encode()).hexdigest()[:12]
    output=root/'.tmp/checkpoint-checkouts'/run/'results'/run
    # The real notebook/worker lifecycle is tested here; scientific fixture lives
    # in test_p6_verification and exercises all serialized review calculations.
    child=f"from pathlib import Path; from airsense_r.artifacts import RunStore,json_bytes; s=RunStore(Path({str(output)!r}),{{'fixture':True}}); s.save('complete.json',json_bytes({{'passed':True}})); print('fixture saved',flush=True)"
    env={**os.environ,'AIRSENSE_NOTEBOOK_TEST_MODE':'1','AIRSENSE_NOTEBOOK_TEST_ROOT':str(root),
         'AIRSENSE_REVIEW_TEST_MODELS':str(tmp_path),'AIRSENSE_REVIEW_TEST_RUN':run,
         'AIRSENSE_REVIEW_TEST_COMMAND':json.dumps([sys.executable,'-c',child])}
    program='from IPython.display import display\n'+'\n\n'.join(cells)
    for _ in range(2):
        result=subprocess.run([sys.executable,'-c',program],env=env,capture_output=True,text=True,timeout=45)
        assert result.returncode==0,result.stdout+result.stderr
        assert 'VERIFICATION COMPLETE' in result.stdout

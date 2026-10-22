"""Verify completed P7 evidence, then analyze saved P6/P7 failures without fitting."""
from hashlib import sha256
from importlib.metadata import version
import argparse
import json
import logging
from pathlib import Path
import platform
import subprocess

import yaml

from airsense_r.artifacts import source_hash, json_bytes
from airsense_r.checkpoints import open_run
from airsense_r.evaluation.p6_verify import Snapshot
from airsense_r.p5_recovery import local_writer_lock
from airsense_r.p8 import run_analysis


def git(*args: str) -> str:
    """Run a read-only evidence Git operation without exposing credential output."""
    result=subprocess.run(['git',*args],capture_output=True,text=True)
    if result.returncode:raise RuntimeError('Cannot read pinned result evidence; preserve existing checkout')
    return result.stdout.strip()


def snapshot(root: Path, remote: str, run: str, commit: str) -> Snapshot:
    """Read an exact result snapshot; refuse modified or mismatched checkouts."""
    checkout=root/'.tmp/p8-inputs'/run
    if not checkout.exists():
        checkout.parent.mkdir(parents=True,exist_ok=True)
        git('clone','--no-checkout','--single-branch','--branch','results/'+run,
            '--config','core.autocrlf=false',remote,str(checkout))
        git('-C',str(checkout),'checkout','--detach',commit)
    if (git('-C',str(checkout),'rev-parse','HEAD')!=commit
        or git('-C',str(checkout),'remote','get-url','origin')!=remote
        or git('-C',str(checkout),'status','--porcelain')):
        raise ValueError('Pinned result snapshot differs; do not overwrite it')
    return Snapshot(checkout/'results'/run)


def main() -> None:
    """Run one resumable analysis branch with immutable upstream lineage."""
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model-directory',type=Path,required=True)
    parser.add_argument('--remote',required=True)
    args=parser.parse_args(); root=Path(__file__).resolve().parents[1]
    logging.basicConfig(level=logging.INFO)
    settings=yaml.safe_load((root/'configs/p8_analysis.yaml').read_text())
    p7_receipt=json.loads((root/'results/p7/execution_review.json').read_bytes())
    p6_receipt=json.loads((root/'results/p6/final_acceptance.json').read_bytes())
    with local_writer_lock(root/'.tmp/p8-writer.lock'):
        print('Loading pinned P7/P6 snapshots and checking all Git artifact bytes...',flush=True)
        p7=snapshot(root,args.remote,'p7-sites-01',p7_receipt['result_commit'])
        p6=snapshot(root,args.remote,'p6-sensors-01',p6_receipt['result_commit'])
        for evidence,receipt,key in [(p7,p7_receipt,'manifest_sha256'),(p6,p6_receipt,'result_manifest_sha256')]:
            if sha256(evidence.raw_manifest).hexdigest()!=receipt[key]:raise ValueError('Pinned manifest differs from local review receipt')
        if p7.manifest['provenance']['code_commit']!=p7_receipt['source_commit']:
            raise ValueError('Original P7 source differs')
        if p6_receipt['status']!='P6_accepted':raise ValueError('P6 independent acceptance is missing')
        review=snapshot(root,args.remote,p6_receipt['verification_run'],p6_receipt['verification_result_commit'])
        if (sha256(review.raw_manifest).hexdigest()!=p6_receipt['verification_manifest_sha256']
                or not review.json('complete.json')['passed']):raise ValueError('Accepted P6 verification differs')
        for key in ['config_hash','protocol_hash','dataset_sha256']:
            if p6.manifest['provenance'][key]!=p7.manifest['provenance'][key]:raise ValueError('Incompatible P6/P7 protocol or dataset')
        provenance={'phase':'P8','run_id':settings['run_id'],'source_hash':source_hash(root),
            'code_commit':git('-C',str(root),'rev-parse','HEAD'),'settings':settings,
            'input_commits':{'p7':p7_receipt['result_commit'],'p6':p6_receipt['result_commit'],
                'p6_review':p6_receipt['verification_result_commit']},
            'input_manifests':{'p7':sha256(p7.raw_manifest).hexdigest(),'p6':sha256(p6.raw_manifest).hexdigest()},
            'environment':{'python':platform.python_version(),'packages':{n:version(n) for n in
                ['numpy','pandas','scipy','matplotlib','threadpoolctl','PyYAML']}},
            'no_fitting_or_inference':True}
        output=open_run(root,settings['run_id'],provenance,args.remote)
        output.save('analysis-config.json',json_bytes(settings))
        run_analysis(p7,p6,args.model_directory.resolve(),output,settings,lambda s:print(s,flush=True))
        # Derived exports never modify the upstream evidence or Drive files.
        for name in output.manifest['artifacts']:
            destination=None
            if name.endswith('.png'):destination=root/'figures/p8-runs'/settings['run_id']/name
            if name=='dashboard-p8.json':destination=root/'docs/data/p8-runs'/settings['run_id']/name
            if destination:
                destination.parent.mkdir(parents=True,exist_ok=True)
                destination.write_bytes(output._path(name).read_bytes())


if __name__=='__main__':main()

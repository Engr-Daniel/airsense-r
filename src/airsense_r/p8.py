"""Read-only P7 acceptance checks and P8 diagnostics from pinned saved evidence."""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path

import numpy as np
import pandas as pd

from airsense_r.artifacts import json_bytes
from airsense_r.evaluation.p6_verify import Snapshot, read_bundle
from airsense_r.evaluation.p7_verify import verify_run
from airsense_r.evaluation.failure_analysis import seed_average, diagnostics, png_plot, regret_plot
from airsense_r.evaluation.p7_verify import ATOL, RTOL


def save_diagnostics(output, prefix: str, points: pd.DataFrame, settings: dict, figures=False) -> None:
    """Checkpoint compact tables and optional figures after each diagnostic unit."""
    tables=diagnostics(points,settings)
    for name,frame in tables.items():
        output.save(f'{prefix}-{name}.csv',frame.to_csv(index=False,float_format='%.17g').encode())
    if figures:
        for dimension in ['concentration_band','season']:
            output.save(f'{prefix}-{dimension}.png',png_plot(tables[dimension],dimension,f'{prefix}: descriptive error analysis'))
    output.save(prefix+'-complete.json',json_bytes({'complete':True,'exploratory':True,'model_refitting':False}))


def sensor_analysis(snapshot: Snapshot, directory: Path, output, settings: dict, progress=print) -> None:
    """Read checksum-verified P6 predictions, retaining seed-averaged error semantics."""
    provenance=snapshot.manifest['provenance']; config=provenance['config']
    if json.loads((directory/'identity.json').read_bytes()) != {'provenance_hash':sha256(json_bytes(provenance)).hexdigest()}:
        raise ValueError('P6 Drive identity differs')
    checked=set()
    def load(name):
        value=read_bundle(directory,name,snapshot);checked.add(name);return value
    target=load('targets'); y=target['y']; stations=target['station']; times=pd.to_datetime(target['time'])
    if not np.isfinite(y).all() or pd.MultiIndex.from_arrays([stations,times]).has_duplicates:
        raise ValueError('Invalid P6 targets')
    if not times.isin(pd.date_range(config['data']['test_target_start'],config['data']['test_target_end'],freq='h')).all():
        raise ValueError('P6 targets outside test calendar')
    reports=snapshot.json('dashboard-p6.json')['reports']
    rank_rows=[]
    for policy in sorted({r['policy'] for r in reports}):
        specifications=[{'id':'clean','seeds':[None]}]+[r['condition'] for r in reports if r['policy']==policy]
        for spec in specifications:
            progress(f"P8 sensor diagnostics: {policy} / {spec['id']}")
            parts=[]
            for model in config['models']['candidates']:
                error=np.zeros(len(y));bias=np.zeros(len(y));prediction=np.zeros(len(y));n=0
                for cseed in spec['seeds']:
                    unit='clean' if cseed is None else f"{spec['id']}-c{cseed}"
                    for seed in ([-1] if model=='persistence' else config['seeds']['training']):
                        pred=load(f'pred-{policy}-{unit}-{model}-{seed}')['prediction']
                        if pred.shape!=y.shape or not np.isfinite(pred).all():raise ValueError('Invalid P6 prediction')
                        error+=np.abs(pred-y);bias+=pred-y;prediction+=pred;n+=1
                parts.append(pd.DataFrame({'station':stations,'target_timestamp':times,'model':model,
                    'y_true':y,'y_pred':prediction/n,'absolute_error':error/n,'bias':bias/n}))
            points=pd.concat(parts,ignore_index=True)
            prefix=f"p6-{policy}-{spec['id']}"
            if not output.has(prefix+'-complete.json'):
                save_diagnostics(output,prefix,points,settings,figures=(spec['id']=='clean'))
            del points,parts
    # Reuse independently accepted P6 headline intervals; do not pretend they are
    # a new P8 bootstrap. They remain linked to their accepted result snapshot.
    for report in reports:
        for scope,summary in report['scopes'].items():
            for metric in summary['metrics']:
                rank_rows.append({'policy':report['policy'],'condition':report['condition']['id'],
                    'scope':scope,**metric,'selection_regret':summary['selection_regret'],
                    'kendall_tau_b':summary['kendall_tau_b'],
                    'selected_is_numerical_best':summary['selected_is_numerical_best'],
                    'selected_within_practical_near_tie':summary['selected_within_practical_near_tie']})
    expected={n[7:-5] for n in snapshot.blobs if n.startswith('bundle-')}
    if checked!=expected:raise ValueError('Unreviewed P6 prediction bundles remain')
    output.save('sensor-ranking-summary.csv',pd.DataFrame(rank_rows).to_csv(index=False,float_format='%.17g').encode())
    output.save('sensor-accepted-uncertainty.json',json_bytes({'source':'accepted_P6_snapshot','reports':reports}))
    output.save('p6-files-verified.json',json_bytes({'passed':True,'bundle_files':len(checked)}))


def run_analysis(p7: Snapshot, p6: Snapshot, storage: Path, output, settings: dict, progress=print) -> dict:
    """Gate failure analysis on prediction-level P7 verification, without training."""
    if settings['comparison_atol'] != ATOL or settings['comparison_rtol'] != RTOL:
        raise ValueError('Verification tolerances differ from reviewed implementation')
    predictions=verify_run(p7,storage,output,progress)
    progress('P8: site-shift concentration bands, seasons and worst errors')
    if not output.has('p7-site-shift-complete.json'):
        save_diagnostics(output,'p7-site-shift',seed_average(predictions),settings,figures=True)
    del predictions
    sensor_analysis(p6,storage/'p6-artifacts'/'p6-sensors-01',output,settings,progress)
    sites=output.load_json('p7-independent-report.json')
    rows=[]
    for station,report in sites['stations'].items():
        rows.append({'station':station,'selected_family':report['selected_family'],
            'kendall_tau_b':report['kendall_tau_b'],'within_practical_near_tie':report['within_practical_near_tie'],
            **report['selection_regret']})
    regret = pd.DataFrame(rows)
    output.save('site-selection-regret.csv',regret.to_csv(index=False,float_format='%.17g').encode())
    output.save('site-selection-regret.png',regret_plot(regret,sites['practical_threshold_ug_m3']))
    output.save('dashboard-p8.json',json_bytes({'status':'awaiting_independent_review',
        'exploratory_diagnostics':settings,'site_selection':rows,
        'mean_station_selection_regret':sites['mean_station_selection_regret'],
        'limitations':['within-Beijing generalization only','synthetic non-target sensor interventions',
            'diagnostic bands and seasons are post-results descriptive analyses',
            'uncertainty conditional on fitted seeds and observed stations']}))
    report={'phase':'P8','execution_complete':True,'scientifically_accepted':False,
        'p7_prediction_verification_passed':True,'independent_p7_bootstrap':True,
        'no_models_fitted_or_predicted':True,'diagnostics':'post-results descriptive, no subgroup significance claims'}
    output.save('complete.json',json_bytes(report));progress('P8 EXECUTION COMPLETE. Save notebook outputs for review.')
    return report

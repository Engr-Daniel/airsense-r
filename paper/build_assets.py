"""Render manuscript tables/figures from the checksum-verified accepted P8 snapshot."""
from __future__ import annotations
import argparse
from hashlib import sha256
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def markdown(frame: pd.DataFrame) -> str:
    """Render without adding a table-formatting dependency."""
    rows = ['| '+' | '.join(map(str,frame.columns))+' |', '| '+' | '.join(['---']*len(frame.columns))+' |']
    for row in frame.itertuples(index=False,name=None):
        rows.append('| '+' | '.join(f'{v:.4f}' if isinstance(v,float) else str(v) for v in row)+' |')
    return '\n'.join(rows)


def main() -> None:
    """Verify input lineage before rendering; never refit or change the experiment."""
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--p8-directory',type=Path,required=True)
    parser.add_argument('--tables-only', action='store_true', help='Keep existing figures unchanged')
    args = parser.parse_args()
    directory=args.p8_directory.resolve()
    receipt=json.loads((ROOT/'results/p8/final_acceptance.json').read_bytes())
    raw=(directory/'manifest.json').read_bytes()
    if sha256(raw).hexdigest()!=receipt['manifest_sha256']:
        raise ValueError('Input is not the accepted P8 manifest')
    manifest=json.loads(raw)
    for name,record in manifest['artifacts'].items():
        path=directory/name
        if path.parent!=directory or sha256(path.read_bytes()).hexdigest()!=record['sha256']:
            raise ValueError(f'Invalid artifact: {name}')
    read=lambda name:json.loads((directory/name).read_bytes())
    clean=json.loads((ROOT/'results/p5/corrected_acceptance.json').read_bytes())
    sites=read('p7-independent-report.json')
    sensors=read('sensor-accepted-uncertainty.json')['reports']
    tables=[]
    for label,records in [('S1. Corrected clean test',clean['metrics']),('S2. LOSO fixed-family metrics',sites['fixed_family_metrics'])]:
        tables.append('## '+label+'\n\n'+markdown(pd.DataFrame(records)[['model','mae','rmse','r2']].sort_values('mae')))
    rows=[]; comparison_rows=[]
    for r in sensors:
        for scope,s in r['scopes'].items():
            ci=s['uncertainty']
            rows.append({'policy':r['policy'],'condition':r['condition']['id'],'scope':scope,
                'selected_MAE':next(v['mae'] for v in s['metrics'] if v['model']==s['selected_family']),
                'regret':s['selection_regret'],'CI_low':ci['selection_regret']['ci_low'] if ci['available'] else 'unavailable',
                'CI_high':ci['selection_regret']['ci_high'] if ci['available'] else 'unavailable',
                'tau_b':s['kendall_tau_b'],'within_near_tie':s['selected_within_practical_near_tie']})
            for metric in s['metrics']:
                difference=ci['differences'][metric['model']] if ci['available'] else None
                comparison_rows.append({'policy':r['policy'],'condition':r['condition']['id'],'scope':scope,
                    'model':metric['model'],'MAE':metric['mae'],'clean_MAE':metric['clean_mae'],
                    'RPD_percent':metric['rpd_percent'],'clean_rank':metric['clean_rank'],'stress_rank':metric['stress_rank'],
                    'selected_minus_model':difference['estimate'] if difference else 'unavailable',
                    'CI_low':difference['ci_low'] if difference else 'unavailable',
                    'CI_high':difference['ci_high'] if difference else 'unavailable'})
    sensor_table=pd.DataFrame(rows)
    tables.append('## S3. All sensor conditions and scopes\n\n'+markdown(sensor_table))
    station=pd.read_csv(directory/'site-selection-regret.csv',float_precision='round_trip')
    tables.append('## S4. Station-specific selection regret\n\n'+markdown(station))
    bands=pd.read_csv(directory/'p7-site-shift-concentration_band.csv',float_precision='round_trip')
    tables.append('## S5. Exploratory concentration bands\n\n'+markdown(bands))
    tables.append('## S6. All sensor model comparisons\n\nPaired differences are selected-family minus comparator MAE; positive values favor the comparator. Clean metrics are matched to each scope.\n\n'+markdown(pd.DataFrame(comparison_rows)))
    target_raw = (ROOT/'results/p9-target-history/final_acceptance.json').read_bytes()
    target = json.loads(target_raw)
    if target['status'] != 'P9_target_history_accepted' or not target['independent_bootstrap']:
        raise ValueError('Target-history evidence has not been accepted')
    target_rows = []
    for summary in target['summaries']:
        interval = summary['uncertainty']['selection_regret']
        for metric in summary['metrics']:
            target_rows.append({'condition': summary['condition'], 'scope': summary['scope'],
                'model': metric['model'], 'MAE': metric['mae'], 'RMSE': metric['rmse'],
                'R2': metric['r2'], 'matched_clean_MAE': metric['clean_mae'],
                'RPD_percent': metric['rpd_percent'], 'selected_regret': summary['selection_regret'],
                'regret_CI_low': interval['ci_low'], 'regret_CI_high': interval['ci_high'],
                'tau_b': summary['kendall_tau_b']})
    tables.append('## S7. Post-results PM2.5 target-history extension\n\n'
        'Primary imputation only; original selected family is persistence. Regret and its interval '
        'refer to that selected family and repeat across comparator rows. This extension was '
        'declared after primary results; it does not replace the confirmatory experiment.\n\n'
        +markdown(pd.DataFrame(target_rows)))
    (ROOT/'paper/tables.md').write_text('# Supplementary result tables\n\nGenerated from accepted artifacts. MAE/RMSE/regret are in µg/m³. Confidence intervals are pointwise, conditional paired 24-hour block-bootstrap intervals; subgroup bands have no confidence intervals.\n\n'+'\n\n'.join(tables)+'\n',encoding='utf-8')
    figures=ROOT/'figures/paper';figures.mkdir(parents=True,exist_ok=True)
    if not args.tables_only:
        plt.rcParams.update({'font.size':10,'pdf.fonttype':42})
        fig,ax=plt.subplots(figsize=(8.5,5.5)); y=np.arange(len(station))
        ax.hlines(y,station.ci_low,station.ci_high,color='#33658a',linewidth=2)
        ax.scatter(station.estimate,y,color='#17324d',zorder=3,label='Point regret; lines: 95% CI')
        ax.axvline(1,color='#a64b00',ls='--',label='Predefined practical threshold')
        ax.set(yticks=y,yticklabels=station.station,xlabel='Selection regret (µg/m³)')
        ax.legend(loc='lower center',bbox_to_anchor=(.5,1.02),frameon=False,ncol=1)
        fig.tight_layout()
        for ext in ['png','pdf']:fig.savefig(figures/f'01_site_regret.{ext}',dpi=300,bbox_inches='tight',metadata={'Creator':'AirSense-R'} if ext=='pdf' else {'Software':'AirSense-R'})
        plt.close(fig)
        fig,axes=plt.subplots(1,2,figsize=(11,5),sharex=True,sharey=True)
        order=[r['condition']['id'] for r in sensors if r['policy']=='primary']
        for ax,policy,label in zip(axes,['primary','no_ffill'],['Primary imputation','No-forward-fill sensitivity']):
            subset=sensor_table.loc[(sensor_table.policy==policy)&(sensor_table.scope=='full')].set_index('condition').loc[order]
            y=np.arange(len(subset));ax.hlines(y,subset.CI_low,subset.CI_high,color='#33658a',linewidth=2)
            ax.scatter(subset.regret,y,color='#17324d',s=22,zorder=3)
            ax.axvline(1,color='#a64b00',ls='--');ax.set(title=label,yticks=y,yticklabels=order,xlabel='Selection regret (µg/m³)',xlim=(-.04,1.06))
        fig.tight_layout()
        for ext in ['png','pdf']:fig.savefig(figures/f'02_sensor_regret.{ext}',dpi=300,bbox_inches='tight',metadata={'Creator':'AirSense-R'} if ext=='pdf' else {'Software':'AirSense-R'})
        plt.close(fig)
    evidence={'input_result_commit':receipt['result_commit'],'input_manifest_sha256':receipt['manifest_sha256'],
        'target_history_acceptance_sha256':sha256(target_raw).hexdigest(),
        'target_history_result_commit':target['result_commit'],
        'target_history_review_commit':target['review_commit'],
        'clean_acceptance_sha256':sha256((ROOT/'results/p5/corrected_acceptance.json').read_bytes()).hexdigest(),
        'builder_sha256':sha256(Path(__file__).read_bytes().replace(b'\r\n',b'\n')).hexdigest(),
        'generated_files':[p.relative_to(ROOT).as_posix() for p in sorted(figures.glob('*'))]+['paper/tables.md'],
        'note':'Presentation only: no fitting, selection changes or new inference. PDF creation timestamps may differ on rerender.'}
    (ROOT/'paper/evidence.json').write_text(json.dumps(evidence,indent=2)+'\n',encoding='utf-8')
    print(f'Rendered {len(sensor_table)} sensor scope rows and {len(station)} station rows from 226 verified artifacts.')


if __name__=='__main__':main()

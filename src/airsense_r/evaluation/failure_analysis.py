"""Descriptive, post-results diagnostics; never select or refit models."""
from __future__ import annotations

import io
import numpy as np
import pandas as pd


def seed_average(predictions: pd.DataFrame) -> pd.DataFrame:
    """Average errors across seeds, rather than score an ensemble prediction."""
    p = predictions.copy()
    p['absolute_error'] = np.abs(p.y_pred-p.y_true)
    p['bias'] = p.y_pred-p.y_true
    return p.groupby(['station','target_timestamp','model'],sort=True).agg(
        y_true=('y_true','first'), y_pred=('y_pred','mean'),
        absolute_error=('absolute_error','mean'), bias=('bias','mean')).reset_index()


def diagnostics(points: pd.DataFrame, settings: dict) -> dict[str, pd.DataFrame]:
    """Report concentration bands, seasons, and largest seed-averaged errors."""
    p = points.copy()
    if p.empty or p.duplicated(['station','target_timestamp','model']).any():
        raise ValueError('Empty or duplicate diagnostic targets')
    if not np.isfinite(p[['y_true', 'y_pred', 'absolute_error', 'bias']]).all().all():
        raise ValueError('Nonfinite diagnostic values')
    p['target_timestamp'] = pd.to_datetime(p.target_timestamp)
    edges = settings['pollution_boundaries_ug_m3']
    if not edges or edges != sorted(set(edges)) or not np.isfinite(edges).all():
        raise ValueError('Concentration boundaries must strictly increase')
    labels = [f'<{edges[0]:g}'] + [f'{a:g} to <{b:g}' for a,b in zip(edges,edges[1:])] + [f'>={edges[-1]:g}']
    p['concentration_band'] = np.array(labels)[np.digitize(p.y_true, edges)]
    p['season'] = p.target_timestamp.dt.month.map({12:'DJF',1:'DJF',2:'DJF',3:'MAM',4:'MAM',5:'MAM',6:'JJA',7:'JJA',8:'JJA',9:'SON',10:'SON',11:'SON'})
    result = {}
    for dimension in ['concentration_band','season']:
        station = p.groupby(['station','model',dimension],sort=True).agg(
            mae=('absolute_error','mean'),bias=('bias','mean'),n=('y_true','size')).reset_index()
        aggregate = station.groupby(['model',dimension],sort=True).agg(
            mae=('mae','mean'),bias=('bias','mean'),stations=('station','nunique'),targets=('n','sum')).reset_index()
        result[dimension+'-station'] = station
        result[dimension] = aggregate
    result['worst-cases'] = p.sort_values(
        ['absolute_error','station','target_timestamp','model'],ascending=[False,True,True,True]
    ).groupby(['station','model'],sort=True).head(settings['worst_cases_per_station_model']).reset_index(drop=True)
    return result


def png_plot(table: pd.DataFrame, dimension: str, title: str) -> bytes:
    """Render a reusable figure from the exported diagnostic table."""
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    pivot=table.pivot(index=dimension,columns='model',values='mae')
    order = (['DJF', 'MAM', 'JJA', 'SON'] if dimension == 'season' else
             sorted(pivot.index, key=lambda value: float('-inf') if value.startswith('<') else
                    float(value.removeprefix('>=').split()[0])))
    pivot = pivot.reindex([value for value in order if value in pivot.index])
    fig,ax=plt.subplots(figsize=(8,4))
    pivot.plot.bar(ax=ax)
    ax.set(title=title,ylabel='MAE (µg/m³)',xlabel=dimension.replace('_',' '))
    fig.tight_layout(); buffer=io.BytesIO()
    fig.savefig(buffer,format='png',dpi=160,metadata={'Software':'AirSense-R'})
    plt.close(fig)
    return buffer.getvalue()


def regret_plot(table: pd.DataFrame, threshold: float) -> bytes:
    """Plot independently verified station regret and paired percentile intervals."""
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(9, 5))
    positions = np.arange(len(table))
    # Draw intervals directly: percentile intervals need not enclose the estimate.
    ax.hlines(positions, table.ci_low, table.ci_high, color='steelblue')
    ax.scatter(table.estimate, positions, color='navy', label='Selection regret')
    ax.axvline(threshold, linestyle='--', color='darkorange', label='Practical near-tie threshold')
    ax.set(yticks=positions, yticklabels=table.station,
           xlabel='MAE regret (micrograms/m3)', title='Within-Beijing held-out station selection regret')
    ax.legend(); fig.tight_layout()
    buffer = io.BytesIO()
    fig.savefig(buffer, format='png', dpi=160, metadata={'Software':'AirSense-R'})
    plt.close(fig)
    return buffer.getvalue()

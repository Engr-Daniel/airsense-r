# IEEE Overleaf figure assets

This folder contains reader-facing figure assets for the AirSense-R manuscript.

## Included assets

- `ormedian_logo.png` — supplied Ormedian Research Group logo. Retained as a project asset but not inserted into the IEEE paper body.
- `sensor_regret.pdf` — accepted publication figure copied from `figures/paper/02_sensor_regret.pdf`.
- `site_regret.pdf` — accepted publication figure copied from `figures/paper/01_site_regret.pdf`.

## Figures drawn directly in `main.tex`

The following figures are native TikZ/PGFPlots vector graphics, so they remain sharp at any scale:

- AirSense-R study flow;
- exact four-family model architecture diagram (Persistence, XGBoost, MLP, GRU);
- frozen validation-selection flowchart;
- target-history full-period vs affected-window regret with asymmetric 95% confidence intervals.

The conceptual device sketch and redundant clean-MAE bar chart were removed during technical review. The clean results remain in the main table. The study uses archived reference-station data and does not claim validation of a physical AirSense-R device.

Target-history point estimates and interval endpoints come from
`results/p9-target-history/final_acceptance.json`. PGFPlots receives each point
and separate upper/lower error lengths; these are not symmetric approximations.
The axis includes the full 12-hour affected-window upper bound (2.9097).

Prefer PDF/vector output for any additional publication figures. Raster figures should be at least 300 dpi at final print size.

## Additional evidence figures (31 October 2026)

| Asset | Purpose | Placement |
| --- | --- | --- |
| `rank_and_regret.pdf` | All four families' numerical ranks beside selected-family regret and intervals for all 15 primary stress conditions | Replaces the sensor-regret-only plot in the main paper; original asset retained |
| `target_history_accuracy.pdf` | Absolute MAE for all families under PM2.5 dropout and outages, separating full-period and affected-history scopes | Main paper, alongside the outage regret/uncertainty figure |
| `descriptive_error_regimes.pdf` | Accepted LOSO error summaries by observed concentration and season, including subgroup counts | `supplement.tex`; explicitly descriptive, with no subgroup intervals |

Reproduce from the repository root:

```sh
python paper/build_diagnostic_figures.py --p8-directory PATH_TO_ACCEPTED_P8_RESULTS
```

The builder verifies the accepted P8 manifest and every registered artifact,
checks the clean and target-history acceptance receipts, and records input hashes,
all plotted values and PDF checksums in `paper/diagnostic_figure_evidence.json`.
It does not train, predict, alter accepted artifacts or add dependencies.
Use `--preview-directory .tmp/diagnostic-figures` for optional PNG previews.

No new uncertainty is estimated. Only the regret panel has accepted intervals;
absolute-MAE and subgroup panels show descriptive point estimates. Line segments
connect tested levels or categories; they are not fitted response curves. The
affected-history masks vary by outage condition. Concentration bands are not
health/AQI categories. The selected figure set covers every declared primary
condition and every target-history condition, not a favorable subset.

Checks: all 60 ranks, 30 regret intervals, 32 target-history MAEs and 32 subgroup
rows agree with accepted inputs. Standalone figures were visually inspected.
The updated main paper and supplement still need an Overleaf layout review.

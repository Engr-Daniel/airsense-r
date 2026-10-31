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

# Dataset Card

## Planned source

UCI Beijing Multi-Site Air Quality dataset.

## Why this dataset

- Public and quickly accessible
- Multi-station structure supports site-shift evaluation
- Hourly temporal resolution
- Includes multiple pollutants and meteorological covariates
- Suitable for reproducible forecasting experiments

## Expected fields

Timestamp components, station, PM2.5, PM10, SO2, NO2, CO, O3, TEMP, PRES, DEWP, RAIN, wind direction, wind speed.

## Data governance

Do not commit the downloaded raw dataset unless its license and repository strategy explicitly permit redistribution. Keep acquisition reproducible via `scripts/download_data.py` and document the source/license.

## Audit checklist

- [ ] Files/stations present
- [ ] Row counts
- [ ] Date coverage
- [ ] Duplicate timestamps
- [ ] Missingness by variable/station/time
- [ ] Physical plausibility checks
- [ ] Distribution plots
- [ ] Target autocorrelation / persistence strength
- [ ] Cross-station differences

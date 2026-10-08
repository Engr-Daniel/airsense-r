# Dataset Card — Beijing Multi-Site Air Quality

## Identity

- **Dataset:** Beijing Multi-Site Air Quality
- **Repository:** UCI Machine Learning Repository
- **UCI ID:** 501
- **DOI:** `10.24432/C5RK5G`
- **License:** CC BY 4.0
- **Canonical page:** <https://archive.ics.uci.edu/dataset/501/beijing+multi+site+air+quality+data>
- **Runtime archive URL:** <https://archive.ics.uci.edu/static/public/501/beijing+multi+site+air+quality+data.zip>

The official UCI description reports **420,768 hourly observations from 12 nationally-controlled air-quality monitoring stations** between **2013-03-01 and 2017-02-28**. Air-quality measurements originate from the Beijing Municipal Environmental Monitoring Center; meteorological values are matched from nearby China Meteorological Administration stations. Missing observations are encoded as `NA`.

## Default AirSense-R access policy

AirSense-R uses **remote-only, temporary acquisition**. The raw dataset is not expected to be stored permanently on the user's machine and is never committed to the repository.

`python scripts/run_data_audit.py` performs the following:

1. streams the authoritative UCI archive into an OS temporary directory;
2. computes SHA-256 and byte count for the exact downloaded archive;
3. recursively extracts the archive in temporary storage;
4. discovers and audits all `PRSA_Data_*.csv` station files;
5. writes only compact audit outputs into `audit/`;
6. deletes the raw archive and extracted CSVs when the process exits.

This design satisfies reproducibility without forcing a permanent ~dataset-sized local footprint.

## Stations

Expected station inventory:

1. Aotizhongxin
2. Changping
3. Dingling
4. Dongsi
5. Guanyuan
6. Gucheng
7. Huairou
8. Nongzhanguan
9. Shunyi
10. Tiantan
11. Wanliu
12. Wanshouxigong

The official total implies 35,064 hourly rows per station when the complete four-year timestamp grid is represented (`420,768 / 12 = 35,064`). P2 does not assume that all sensor values are observed at every timestamp; missing sensor values are expected.

## Raw schema

| Field | Meaning | Unit / type |
|---|---|---|
| `No` | row number | integer |
| `year`, `month`, `day`, `hour` | timestamp components | integer |
| `PM2.5` | particulate matter <=2.5 μm | μg/m³ |
| `PM10` | particulate matter <=10 μm | μg/m³ |
| `SO2` | sulfur dioxide | μg/m³ |
| `NO2` | nitrogen dioxide | μg/m³ |
| `CO` | carbon monoxide | μg/m³ |
| `O3` | ozone | μg/m³ |
| `TEMP` | temperature | °C |
| `PRES` | atmospheric pressure | hPa |
| `DEWP` | dew-point temperature | °C |
| `RAIN` | precipitation | mm |
| `wd` | wind direction | categorical |
| `WSPM` | wind speed | m/s |
| `station` | monitoring-site name | categorical |

## Primary AirSense-R target

- **Outcome:** `PM2.5`
- **Forecast horizon:** one hour ahead (provisional until P3 freeze)
- **History window:** 24 hours (provisional until P3 freeze)

## P2 structural audit scope

The audit is deliberately separated into two layers.

### Layer A — full-data structural checks

Allowed across the entire raw dataset because they do not compare modeling relationships or tune model choices:

- source identity, DOI, license and runtime URL;
- exact archive SHA-256 at execution time;
- station/file inventory;
- row counts and date coverage;
- duplicate timestamps and non-hourly gaps;
- missingness counts/percentages;
- maximum contiguous missing runs by station-variable;
- target-observation coverage;
- diagnostic counts of complete 24-hour windows.

### Layer B — development-only exploratory analysis

Distribution shapes, autocorrelation, persistence strength, feature relationships and any analysis that can influence modeling choices must be performed **only after P3 defines a development/test boundary**. P2 therefore does not use final-test distributions to choose architectures, thresholds, imputers or corruption levels.

## External cross-checks used during P2

Because the repository is intentionally remote-only, the static dataset card records published cross-checks but treats a runtime audit of the UCI bytes as authoritative.

- UCI reports 420,768 instances, 12 stations, hourly measurements, the 2013-03-01 to 2017-02-28 interval and missing values.
- A 2025 Scientific Reports study using the same UCI station files reports station-variable missing-value counts for ten stations and confirms non-trivial missingness across pollutants and smaller missingness in meteorological channels.
- A separate Gucheng study reports missing counts for that station; these literature values are useful consistency checks, not replacements for our runtime audit.

## Data-quality interpretation

A missing value is not automatically evidence of a faulty low-cost sensor. These are regulatory/reference monitoring data. AirSense-R uses missingness and later synthetic degradation as controlled **observation-availability interventions**, not as claims about a particular embedded device's physical failure modes.

Likewise, extreme pollutant readings must not be removed merely because they look unusual. P2 flags suspicious values for later development-only review; it does not label genuine pollution episodes as errors without independent evidence.

## Reproducibility outputs

A network-enabled audit produces:

- `audit/acquisition_receipt.json`
- `audit/structural_audit.json`
- `audit/station_summary.csv`
- `audit/missingness_by_station_variable.csv`
- `audit/aggregate_missingness.csv`

These small artifacts may be committed; raw station CSVs should not be.

## P3 implications

P2 supports the following decisions for protocol freezing:

- retain PM2.5 as the primary target;
- retain all 12 stations as the default cross-site candidate set, subject to runtime usable-window checks;
- use timestamp-based splits rather than row-fraction-only splitting;
- estimate all imputation/scaling/noise parameters from training data only;
- define the primary imputation policy only after development boundaries are fixed;
- keep a 24-hour lookback and 1-hour horizon as provisional defaults until the runtime audit confirms sufficient station-level usable-window coverage.

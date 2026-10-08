# P2 Dataset Acquisition and Audit — Completion Report

**Checkpoint:** P2  
**Date:** 2026-10-08  
**Status:** **COMPLETE — AUTHORITATIVE UCI ACQUISITION AND STRUCTURAL VERIFICATION PASSED**

## Objective

Establish a scientifically defensible, storage-light acquisition and structural-audit workflow for UCI dataset 501, verify the authoritative archive itself, and retain compact evidence sufficient to support P3 protocol decisions without permanently storing the raw dataset.

## Authoritative acquisition verified

The GitHub Actions workflow `p2-authoritative-audit` completed successfully under Python 3.11 and fetched the authoritative UCI archive directly.

Verified acquisition evidence:

- source: UCI Beijing Multi-Site Air Quality dataset (ID 501)
- DOI: `10.24432/C5RK5G`
- archive bytes: **8,192,212**
- SHA-256: `b04da438b2f331ac0ffd45aebdfec0d20d2367feb5f6948c4b1f7ce1191e33c4`
- station CSV inventory: **12 files**
- checksum baseline state: **first authoritative baseline created and frozen**

The raw ZIP and extracted CSVs were held only in temporary storage. They were not committed or retained after the audit.

## Structural verification results

The authoritative audit found:

- **420,768 rows total**;
- **12/12 expected station identities** with no missing, unexpected, or repeated station labels;
- **35,064 rows per station**;
- coverage from **2013-03-01 00:00** through **2017-02-28 23:00** at every station;
- **0 duplicate timestamps**;
- **0 original-order backward steps**;
- **0 original-order zero steps**;
- **0 sorted non-hourly steps**;
- **0 forward gaps greater than one hour**.

Therefore the source files form a complete hourly timestamp grid. Longest missing runs reported in hours are consequently interpretable as consecutive hourly observation gaps.

## Missingness evidence

Aggregate missingness across all 420,768 rows:

| Variable | Missing count | Missing % |
|---|---:|---:|
| CO | 20,701 | 4.920% |
| O3 | 13,277 | 3.155% |
| NO2 | 12,116 | 2.879% |
| SO2 | 9,021 | 2.144% |
| PM2.5 | 8,739 | 2.077% |
| PM10 | 6,449 | 1.533% |
| wd | 1,822 | 0.433% |
| DEWP | 403 | 0.096% |
| TEMP | 398 | 0.095% |
| PRES | 393 | 0.093% |
| RAIN | 390 | 0.093% |
| WSPM | 318 | 0.076% |

PM2.5 missingness varies materially by station, from approximately **1.09% at Wanliu** to **2.72% at Huairou**. Some pollutant channels also contain long contiguous outages, including CO gaps exceeding 1,000 hours at some stations. This supports treating missingness/degradation as a substantive reliability condition rather than a cosmetic perturbation.

## Provisional 24 h -> 1 h window coverage

The structural audit confirms sufficient PM2.5-history coverage for the proposed 24-hour lookback and 1-hour forecast horizon. PM2.5-complete history-window counts range from **28,900 at Shunyi** to **31,172 at Wanliu**, with all stations retaining tens of thousands of candidate windows.

All-numeric-complete windows are lower because other pollutant channels contain longer gaps. This directly supports the P3 requirement to freeze an explicit imputation policy rather than restrict the study to only fully complete multivariate windows.

## Baseline immutability rule

The first successful authoritative receipt is the frozen acquisition baseline. Both:

- `scripts/run_data_audit.py`, and
- `scripts/download_data.py`

must compare later acquisitions with the existing receipt and fail if either the archive SHA-256 or station-file inventory changes. The standalone downloader must never overwrite an existing baseline silently.

## Test and environment verification

- the latest repository test workflow completed successfully under **Python 3.11**;
- the authoritative UCI audit workflow completed successfully;
- the audit evidence files were committed to `audit/`.

## P2 deliverables

- `audit/acquisition_receipt.json`
- `audit/structural_audit.json`
- `audit/station_summary.csv`
- `audit/missingness_by_station_variable.csv`
- `audit/aggregate_missingness.csv`
- `research/DATASET.md`
- `research/P2_COMPLETION_REPORT.md`
- hardened remote acquisition/audit utilities and tests

## Exit decision

**P2 is CLOSED.**

P3 may now use the verified structural evidence to freeze timestamp boundaries, station eligibility, imputation, feature policy, lookback, corruption settings, and uncertainty procedures. Distributional or relationship-based analyses that could inform model choices must still be restricted to the development portion after P3 defines the temporal boundary.

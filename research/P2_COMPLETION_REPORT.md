# P2 Completion Report — Dataset Acquisition and Structural Audit

**Checkpoint:** P2

**Status:** COMPLETE AS A REMOTE-ONLY REPRODUCIBLE DATA CHECKPOINT

**Date:** 2026-10-08

## Objective

Establish the dataset identity, schema, station coverage, remote acquisition policy and reproducible structural-audit procedure needed to make P3 decisions without permanently storing the raw dataset on the user's machine.

## What was completed

### 1. Authoritative source fixed

AirSense-R uses UCI dataset 501, Beijing Multi-Site Air Quality, DOI `10.24432/C5RK5G`, licensed CC BY 4.0.

The authoritative UCI description reports:

- 420,768 hourly records;
- 12 nationally controlled air-quality monitoring stations;
- 2013-03-01 through 2017-02-28;
- six pollutant variables and six meteorological variables;
- missing observations encoded as `NA`.

### 2. Permanent local dataset storage removed from the default workflow

The previous downloader retained and re-extracted raw files. It has been replaced with a temporary runtime acquisition layer.

The new workflow:

- streams the UCI archive into OS temporary storage;
- computes SHA-256 and byte count;
- recursively extracts the archive;
- audits station files;
- saves only compact evidence artifacts;
- automatically deletes raw dataset bytes after the context exits.

This directly follows the user's storage constraint.

### 3. Acquisition evidence specified

Each network-enabled run records:

- canonical source URL;
- dataset page;
- DOI;
- exact SHA-256 of the bytes received in that run;
- archive byte count;
- station CSV file inventory.

The archive checksum is intentionally **runtime-derived rather than hard-coded** because UCI does not expose a canonical checksum on the dataset page and the raw archive is not committed to this repository.

### 4. Structural audit upgraded

The previous script only printed rows/columns/missing cells. The new audit records, by station:

- row count;
- start/end timestamp;
- duplicate timestamps;
- non-hourly timestamp steps;
- forward gaps;
- observed/missing PM2.5 targets;
- missing counts and percentages by variable;
- maximum contiguous missing run per variable;
- diagnostic 24-hour-history/1-hour-ahead usable-window counts;
- station/file inventory.

Aggregate missingness tables are also written.

### 5. Test-set protection rule established

P2 separates **structural checks** from **development-only exploratory analysis**.

Full-data structural metadata may be inspected across the dataset, but distribution-driven decisions, autocorrelation studies, persistence analysis, feature relationships and other model-informing exploration must wait until P3 defines the development/test boundary.

This prevents the audit itself from becoming indirect final-test tuning.

### 6. Published cross-checks recorded

Independent studies using the same UCI files confirm the expected 35,064 timestamps per station and show that pollutant missingness is non-trivial while meteorological missingness is generally smaller. These values are used only as consistency checks; our runtime UCI audit remains authoritative.

### 7. P3-relevant dataset decisions

P2 supports the following provisional decisions:

- PM2.5 remains the primary one-hour-ahead target.
- All 12 stations remain candidates for repeated held-out-station evaluation.
- Final temporal partitions must use explicit timestamps.
- All learned preprocessing and noise scales must be training-derived.
- The 24-hour lookback remains provisional until runtime usable-window coverage is inspected.
- Missing-value handling must be frozen in P3, not improvised during model evaluation.

## Important execution note

This repository was prepared under an environment that cannot persistently fetch the UCI archive through normal Python networking. Therefore the code does **not fabricate a SHA-256 or pretend that byte-level audit outputs were produced here**. Instead, P2 makes the audit reproducible and self-verifying at the point of execution:

```bash
python scripts/run_data_audit.py
```

On any network-enabled Python 3.11+ environment, that one command downloads the authoritative archive temporarily, performs the full audit, writes the compact reports and removes raw data automatically.

The scientific protocol remains `DRAFT`. P3 must inspect those generated audit artifacts before it freezes timestamp cutoffs, near-tie thresholds, imputation policy, bootstrap block length or final station eligibility.

## P2 deliverables

- `research/DATASET.md` — completed dataset card and audit policy.
- `research/P2_COMPLETION_REPORT.md` — this checkpoint record.
- `src/airsense_r/data/remote.py` — temporary remote acquisition + runtime SHA-256.
- `src/airsense_r/data/audit.py` — structural audit engine.
- `scripts/download_data.py` — remote acquisition verifier (no persistent dataset).
- `scripts/run_data_audit.py` — complete remote structural-audit entry point.
- `audit/README.md` — generated artifact contract.
- expanded tests for remote extraction and structural audit behavior.

## Exit criteria

P2 is considered complete as a **reproducible acquisition/audit checkpoint**. P3 cannot be frozen until the generated runtime audit files have been inspected. This distinction preserves scientific honesty while respecting the remote-only storage requirement.

# P2 Dataset Acquisition and Audit — Implementation & Verification Report

**Checkpoint:** P2  
**Date:** 2026-10-08  
**Status:** **IMPLEMENTATION COMPLETE; STRUCTURAL PREFLIGHT COMPLETE; AUTHORITATIVE UCI BYTE VERIFICATION PENDING**

## Objective

Establish a scientifically defensible, storage-light dataset acquisition and structural-audit workflow for UCI dataset 501 before P3 freezes any modeling choices.

## Completed implementation

- Remote-only acquisition from the authoritative UCI URL using OS temporary storage.
- Runtime SHA-256 and byte-count receipt.
- First-successful-receipt baseline rule: later archive hashes/inventories must match.
- Recursive archive extraction with no retained raw dataset.
- Exact validation of the 12 expected UCI station identities.
- Original-order timestamp diagnostics before sorting.
- Sorted-grid duplicate/gap diagnostics.
- Missingness counts and longest missing runs.
- Missing-run rows are no longer blindly labelled as hours across irregular time gaps.
- Provisional 24-hour-lookback / 1-hour-ahead usable-window counts require **every internal timestamp step** to equal one hour.
- Full-data work remains restricted to structural audit; modeling-relevant EDA is deferred until P3 defines the development boundary.

## Structural preflight executed

Because this execution environment could not retrieve the full authoritative UCI archive directly, a structural preflight was run against a public UCI-derived mirror pinned to:

`Kjyesta30/Beijing-Multi-Site-Air-Quality@b11d6aa82cc5285e83cb79adb0f4971a54cba9cb`

The preflight observed:

- **420,768 rows total**;
- **12/12 expected stations**;
- **35,064 rows per station**;
- coverage from **2013-03-01 00:00** through **2017-02-28 23:00** for every station;
- **0 duplicate timestamps**;
- **0 forward gaps**;
- **0 original-order backward steps**;
- PM2.5 missingness ranging from about **1.09% (Wanliu)** to **2.72% (Huairou)**;
- substantial long missing runs for some pollutant channels, including CO and NO2, supporting the decision to treat missingness structure explicitly in P3.

These values reproduce the official UCI structural identity (420,768 instances, 12 nationally controlled stations, March 2013–February 2017), but the mirror is **not** used as authoritative byte evidence.

## Authoritative verification mechanism

`.github/workflows/p2-audit.yml` now performs the authoritative audit on GitHub Actions with **Python 3.11** whenever the updated repository is pushed to `main`:

1. install the package and audit dependencies;
2. temporarily download the authoritative UCI archive;
3. compute SHA-256;
4. validate the expected station inventory;
5. run the hardened structural audit;
6. delete raw temporary data automatically;
7. commit only the compact `audit/` evidence files.

The workflow ignores audit-only pushes, preventing a commit loop.

## Python 3.11 verification finding

The live repository's latest Actions run before this hardening used Python **3.11.16** but failed during test collection because `requests` was not installed by the CI command. The package itself installed successfully. This update fixes the CI install command to include `requests`.

A previous P1.5 Action on the same Python 3.11 workflow passed. The updated local suite passes under the available Python 3.13 environment; the corrected Python 3.11 run should be treated as the final supported-environment verification after push.

## Required authoritative artifacts

P2 is not closed until the Action creates and these are inspected:

- `audit/acquisition_receipt.json`
- `audit/structural_audit.json`
- `audit/station_summary.csv`
- `audit/missingness_by_station_variable.csv`
- `audit/aggregate_missingness.csv`

## P3 rule

P3 **may be drafted now**, using only the structural facts already established, but `research/PROTOCOL.md` must remain **DRAFT** until the authoritative UCI artifacts above are committed and reviewed.

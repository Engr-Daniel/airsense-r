# P2 Verification Status

**Status: CLOSED — AUTHORITATIVE UCI BYTE AND STRUCTURAL VERIFICATION COMPLETE**

## Authoritative verification

The authoritative UCI acquisition/audit completed successfully on 2026-10-08 under Python 3.11.

Frozen archive identity:

- SHA-256: `b04da438b2f331ac0ffd45aebdfec0d20d2367feb5f6948c4b1f7ce1191e33c4`
- bytes: 8,192,212
- source: authoritative UCI archive

Verified structure:

- 420,768 total rows;
- 12/12 expected stations;
- 35,064 hourly rows per station;
- 2013-03-01 00:00 through 2017-02-28 23:00;
- zero duplicate timestamps;
- zero forward hourly gaps;
- zero original-order backward or zero-time steps.

Target/missingness evidence:

- aggregate PM2.5 missingness: 8,739 rows (2.077%);
- PM2.5-complete provisional 24-hour-history/1-hour-ahead windows: 28,900–31,172 per station.

The authoritative compact evidence is stored in `audit/acquisition_receipt.json`, `audit/structural_audit.json`, `audit/station_summary.csv`, `audit/missingness_by_station_variable.csv`, and `audit/aggregate_missingness.csv`.

## Baseline enforcement

The first authoritative SHA-256 is the frozen checksum baseline. Both acquisition entry points must compare subsequent downloads against that baseline and the canonical station inventory and fail on mismatch.

Raw data remain temporary/remote-only and are not retained by the repository workflow.

## Gate outcome

The former P2 gate is closed. P3 was therefore permitted to freeze the temporal split, features, imputation, site-holdout design, corruptions, seeds, near-tie rule, and uncertainty procedure without consulting final-test performance.

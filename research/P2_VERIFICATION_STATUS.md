# P2 Verification Status

**Status: IMPLEMENTATION COMPLETE; STRUCTURAL PREFLIGHT COMPLETE; AUTHORITATIVE UCI BYTE VERIFICATION PENDING**

## What is verified now

A full 12-station structural preflight was executed against a public UCI-derived mirror pinned to commit `b11d6aa82cc5285e83cb79adb0f4971a54cba9cb`.

The preflight reproduces the official UCI structural identity:

- 420,768 total rows;
- 12 expected station identities;
- 35,064 hourly rows per station;
- 2013-03-01 00:00 through 2017-02-28 23:00;
- zero duplicate timestamps;
- zero forward timestamp gaps;
- zero original-order backwards steps.

It also generated station-level PM2.5 missingness and provisional 24-hour-history coverage results in `audit/preflight_station_summary.csv` and aggregate missingness in `audit/preflight_aggregate_missingness.csv`.

## What is not yet claimed

The mirror is **not** treated as authoritative byte evidence. The current execution environment could not retrieve the 7.8 MB UCI archive directly, so no UCI archive SHA-256 is fabricated or inferred from the mirror.

## How the authoritative verification closes automatically

The repository now includes `.github/workflows/p2-audit.yml`. On the next push to `main`, GitHub Actions uses Python 3.11, downloads the authoritative UCI archive into temporary storage, computes its SHA-256, runs the hardened structural audit, discards raw bytes, and commits only the compact evidence files under `audit/`.

The first successful `audit/acquisition_receipt.json` becomes the baseline checksum. Later runs fail if the UCI archive SHA-256 or canonical station-file inventory changes.

## Freeze rule

P3 may be drafted now, but `research/PROTOCOL.md` must remain `DRAFT` until the authoritative Action has successfully produced and committed the required audit evidence and those outputs have been inspected.

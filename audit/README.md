# Audit Evidence

This directory stores **compact evidence only**. Raw UCI files are never committed.

## Authoritative outputs

After `.github/workflows/p2-audit.yml` succeeds against the UCI archive, the following files are committed automatically:

- `acquisition_receipt.json` — authoritative URL, DOI, SHA-256, byte count, and station-file inventory.
- `structural_audit.json` — complete structural audit.
- `station_summary.csv` — station-level timestamp, target, and provisional usable-window checks.
- `missingness_by_station_variable.csv` — missingness/run diagnostics by station and channel.
- `aggregate_missingness.csv` — dataset-level missingness totals.

The first successful acquisition receipt becomes the checksum baseline. Subsequent audit runs must match its SHA-256 and file inventory.

## Preflight files

Files prefixed `preflight_` are independent structural cross-checks performed against a pinned public UCI-derived mirror. They are useful evidence, but **do not replace** the authoritative UCI archive checksum.

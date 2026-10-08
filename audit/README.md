# Audit artifacts

This folder stores compact, reproducible outputs of the remote-only P2 data audit.
Raw UCI CSV files are never committed or retained by the default workflow.

A network-enabled run of `python scripts/run_data_audit.py` creates:

- `acquisition_receipt.json` — authoritative URL, DOI, SHA-256, bytes, file inventory
- `structural_audit.json` — machine-readable full structural audit
- `station_summary.csv` — station coverage/timestamp/window diagnostics
- `missingness_by_station_variable.csv` — missing counts, percentages, run lengths and basic negative-value flags
- `aggregate_missingness.csv` — aggregate missingness by variable

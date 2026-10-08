# Scripts

## Remote acquisition check

```bash
python scripts/download_data.py
```

This verifies the authoritative UCI archive, writes `audit/acquisition_receipt.json`,
and retains no raw dataset.

## P2 structural audit

```bash
python scripts/run_data_audit.py
```

The script downloads into OS temporary storage only, performs station/timestamp/
missingness/window-coverage checks, saves compact reports under `audit/`, and removes
the raw archive when finished.

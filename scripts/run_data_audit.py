"""Minimal first-pass audit of downloaded station CSV files."""
from __future__ import annotations

from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "beijing_multisite_air_quality"


def main() -> None:
    files = sorted(RAW.rglob("*.csv"))
    if not files:
        raise SystemExit("No CSV files found. Run scripts/download_data.py first.")

    rows = []
    for path in files:
        df = pd.read_csv(path)
        rows.append({
            "file": path.name,
            "rows": len(df),
            "columns": len(df.columns),
            "missing_cells": int(df.isna().sum().sum()),
        })

    summary = pd.DataFrame(rows)
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()

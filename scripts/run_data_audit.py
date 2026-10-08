"""Run a full structural P2 audit directly from the remote UCI archive.

No raw dataset is retained. Only compact JSON/CSV/Markdown audit artifacts are saved.
"""
from __future__ import annotations

from pathlib import Path
import json

import pandas as pd

from airsense_r.data.audit import run_structural_audit, save_audit
from airsense_r.data.remote import save_receipt, temporary_uci_dataset

ROOT = Path(__file__).resolve().parents[1]
AUDIT_DIR = ROOT / "audit"


def _write_tables(audit: dict[str, object]) -> None:
    station_df = pd.DataFrame(audit["stations"])
    missing_df = pd.DataFrame(audit["missingness_by_station_variable"])
    aggregate_df = pd.DataFrame(audit["aggregate_missingness"])
    station_df.to_csv(AUDIT_DIR / "station_summary.csv", index=False)
    missing_df.to_csv(AUDIT_DIR / "missingness_by_station_variable.csv", index=False)
    aggregate_df.to_csv(AUDIT_DIR / "aggregate_missingness.csv", index=False)


def main() -> None:
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    with temporary_uci_dataset() as (root, receipt):
        save_receipt(receipt, AUDIT_DIR / "acquisition_receipt.json")
        audit = run_structural_audit(root, lookback_hours=24, horizon_hours=1)
        audit["acquisition"] = receipt.as_dict()
        save_audit(audit, AUDIT_DIR / "structural_audit.json")
        _write_tables(audit)
    print(json.dumps({
        "rows_total": audit["rows_total"],
        "station_count": audit["station_count"],
        "outputs": str(AUDIT_DIR),
        "raw_data_retained": False,
    }, indent=2))


if __name__ == "__main__":
    main()

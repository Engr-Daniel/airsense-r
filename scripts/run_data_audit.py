"""Run the full structural P2 audit directly from the remote UCI archive.

No raw dataset is retained. Only compact JSON/CSV audit artifacts are saved.
The first successful acquisition receipt becomes the checksum baseline; subsequent
runs must match it unless the baseline file is deliberately removed after review.
"""
from __future__ import annotations

from pathlib import Path
import json

import pandas as pd

from airsense_r.data.audit import run_structural_audit, save_audit
from airsense_r.data.remote import (
    assert_same_acquisition,
    load_receipt,
    save_receipt,
    temporary_uci_dataset,
)

ROOT = Path(__file__).resolve().parents[1]
AUDIT_DIR = ROOT / "audit"
RECEIPT_PATH = AUDIT_DIR / "acquisition_receipt.json"


def _write_tables(audit: dict[str, object]) -> None:
    pd.DataFrame(audit["stations"]).to_csv(AUDIT_DIR / "station_summary.csv", index=False)
    pd.DataFrame(audit["missingness_by_station_variable"]).to_csv(
        AUDIT_DIR / "missingness_by_station_variable.csv", index=False
    )
    pd.DataFrame(audit["aggregate_missingness"]).to_csv(
        AUDIT_DIR / "aggregate_missingness.csv", index=False
    )


def main() -> None:
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    baseline = load_receipt(RECEIPT_PATH) if RECEIPT_PATH.exists() else None

    with temporary_uci_dataset() as (root, receipt):
        if baseline is not None:
            assert_same_acquisition(receipt, baseline)
        audit = run_structural_audit(root, lookback_hours=24, horizon_hours=1)
        audit["acquisition"] = receipt.as_dict()
        audit["checksum_baseline_status"] = (
            "matched_existing_baseline" if baseline is not None else "created_first_baseline"
        )
        save_audit(audit, AUDIT_DIR / "structural_audit.json")
        _write_tables(audit)
        if baseline is None:
            save_receipt(receipt, RECEIPT_PATH)

    print(json.dumps({
        "rows_total": audit["rows_total"],
        "station_count": audit["station_count"],
        "station_inventory_valid": audit["station_inventory_valid"],
        "sha256": receipt.sha256,
        "checksum_baseline_status": audit["checksum_baseline_status"],
        "outputs": str(AUDIT_DIR),
        "raw_data_retained": False,
    }, indent=2))


if __name__ == "__main__":
    main()

"""Verify remote UCI acquisition without retaining raw data.

This project intentionally does not keep the dataset on disk. The command streams the
UCI archive into a temporary directory, verifies that station CSVs are present, records
SHA-256 + file inventory, and deletes raw bytes automatically on exit.

Run from repository root:
    python scripts/download_data.py
"""
from __future__ import annotations

from pathlib import Path

from airsense_r.data.remote import save_receipt, temporary_uci_dataset

ROOT = Path(__file__).resolve().parents[1]
RECEIPT = ROOT / "audit" / "acquisition_receipt.json"


def main() -> None:
    with temporary_uci_dataset() as (_, receipt):
        save_receipt(receipt, RECEIPT)
        print(f"Verified remote archive: {receipt.bytes_downloaded:,} bytes")
        print(f"SHA-256: {receipt.sha256}")
        print(f"Station CSVs discovered: {len(receipt.csv_files)}")
        for name in receipt.csv_files:
            print(f"  - {name}")
    print(f"Saved compact receipt to {RECEIPT}")
    print("Raw archive and extracted CSV files were deleted from temporary storage.")


if __name__ == "__main__":
    main()

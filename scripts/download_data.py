"""Verify remote UCI acquisition without retaining raw data.

The first successful authoritative acquisition receipt is immutable evidence. If a
baseline receipt already exists, this command verifies that the newly downloaded
archive has the same SHA-256 and station-file inventory and refuses to overwrite the
baseline on mismatch.

Run from repository root:
    python scripts/download_data.py
"""
from __future__ import annotations

from pathlib import Path

from airsense_r.data.remote import (
    assert_same_acquisition,
    load_receipt,
    save_receipt,
    temporary_uci_dataset,
)

ROOT = Path(__file__).resolve().parents[1]
RECEIPT = ROOT / "audit" / "acquisition_receipt.json"


def main() -> None:
    baseline = load_receipt(RECEIPT) if RECEIPT.exists() else None

    with temporary_uci_dataset() as (_, receipt):
        if baseline is not None:
            assert_same_acquisition(receipt, baseline)
            status = "matched frozen baseline"
        else:
            save_receipt(receipt, RECEIPT)
            status = "created first frozen baseline"

        print(f"Verified remote archive: {receipt.bytes_downloaded:,} bytes")
        print(f"SHA-256: {receipt.sha256}")
        print(f"Checksum status: {status}")
        print(f"Station CSVs discovered: {len(receipt.csv_files)}")
        for name in receipt.csv_files:
            print(f"  - {name}")

    if baseline is None:
        print(f"Saved compact baseline receipt to {RECEIPT}")
    else:
        print(f"Preserved existing baseline receipt at {RECEIPT}")
    print("Raw archive and extracted CSV files were deleted from temporary storage.")


if __name__ == "__main__":
    main()

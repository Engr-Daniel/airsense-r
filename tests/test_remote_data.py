from pathlib import Path
import zipfile

import pytest

from airsense_r.data.remote import (
    _extract_recursive,
    AcquisitionReceipt,
    assert_same_acquisition,
    load_receipt,
    save_receipt,
)


def _receipt(sha: str = "abc") -> AcquisitionReceipt:
    return AcquisitionReceipt(
        source_url="https://example.test/data.zip",
        dataset_page="https://example.test",
        doi="10.test/demo",
        sha256=sha,
        bytes_downloaded=123,
        csv_files=("a.csv", "b.csv"),
    )


def test_recursive_zip_extraction_finds_nested_station_csv(tmp_path: Path):
    inner = tmp_path / "inner.zip"
    with zipfile.ZipFile(inner, "w") as zf:
        zf.writestr("PRSA_Data_Test.csv", "No,year,month,day,hour,station\n1,2020,1,1,0,Test\n")
    outer = tmp_path / "outer.zip"
    with zipfile.ZipFile(outer, "w") as zf:
        zf.write(inner, arcname="PRSA2017_Data.zip")
    destination = tmp_path / "out"
    destination.mkdir()
    _extract_recursive(outer, destination)
    assert list(destination.rglob("PRSA_Data_Test.csv"))


def test_receipt_round_trip(tmp_path: Path):
    path = tmp_path / "receipt.json"
    save_receipt(_receipt(), path)
    loaded = load_receipt(path)
    assert loaded.sha256 == "abc"
    assert loaded.csv_files == ("a.csv", "b.csv")


def test_later_acquisition_must_match_baseline():
    assert_same_acquisition(_receipt("abc"), _receipt("abc"))
    with pytest.raises(RuntimeError, match="SHA-256 changed"):
        assert_same_acquisition(_receipt("xyz"), _receipt("abc"))

from pathlib import Path
import zipfile

from airsense_r.data.remote import _extract_recursive, AcquisitionReceipt, save_receipt


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


def test_receipt_is_compact_and_serializable(tmp_path: Path):
    receipt = AcquisitionReceipt(
        source_url="https://example.test/data.zip",
        dataset_page="https://example.test",
        doi="10.test/demo",
        sha256="abc",
        bytes_downloaded=123,
        csv_files=("a.csv", "b.csv"),
    )
    path = tmp_path / "receipt.json"
    save_receipt(receipt, path)
    text = path.read_text()
    assert '"sha256": "abc"' in text
    assert '"bytes_downloaded": 123' in text

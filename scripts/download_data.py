"""Download and extract the planned UCI dataset.

Run from the repository root:
    python scripts/download_data.py
"""
from __future__ import annotations

from pathlib import Path
from urllib.request import urlretrieve
import zipfile

URL = "https://archive.ics.uci.edu/static/public/501/beijing+multi+site+air+quality+data.zip"
ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
ZIP_PATH = RAW / "beijing_multisite_air_quality.zip"


def main() -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    if not ZIP_PATH.exists():
        print(f"Downloading dataset to {ZIP_PATH} ...")
        urlretrieve(URL, ZIP_PATH)
    else:
        print("Archive already present; skipping download.")

    extract_dir = RAW / "beijing_multisite_air_quality"
    extract_dir.mkdir(exist_ok=True)
    with zipfile.ZipFile(ZIP_PATH) as zf:
        zf.extractall(extract_dir)
    print(f"Extracted to {extract_dir}")


if __name__ == "__main__":
    main()

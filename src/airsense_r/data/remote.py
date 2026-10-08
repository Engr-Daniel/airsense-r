"""Remote-only acquisition for the UCI Beijing Multi-Site Air Quality dataset.

The project deliberately avoids persisting the raw dataset. The authoritative UCI
archive is streamed into a temporary directory, hashed, unpacked recursively, and
exposed to callers only for the lifetime of a context manager.
"""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Iterator
import json
import zipfile

import requests

UCI_DATASET_PAGE = "https://archive.ics.uci.edu/dataset/501/beijing+multi+site+air+quality+data"
UCI_ARCHIVE_URL = "https://archive.ics.uci.edu/static/public/501/beijing+multi+site+air+quality+data.zip"
UCI_DOI = "10.24432/C5RK5G"
DATASET_ID = 501


@dataclass(frozen=True)
class AcquisitionReceipt:
    source_url: str
    dataset_page: str
    doi: str
    sha256: str
    bytes_downloaded: int
    csv_files: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "source_url": self.source_url,
            "dataset_page": self.dataset_page,
            "doi": self.doi,
            "sha256": self.sha256,
            "bytes_downloaded": self.bytes_downloaded,
            "csv_files": list(self.csv_files),
        }


def _download_to_path(url: str, destination: Path, timeout: int = 120) -> tuple[str, int]:
    digest = sha256()
    n_bytes = 0
    with requests.get(url, stream=True, timeout=timeout) as response:
        response.raise_for_status()
        with destination.open("wb") as handle:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if not chunk:
                    continue
                handle.write(chunk)
                digest.update(chunk)
                n_bytes += len(chunk)
    return digest.hexdigest(), n_bytes


def _extract_recursive(zip_path: Path, destination: Path) -> None:
    """Extract an archive and any nested ZIP files without a persistent cache."""
    with zipfile.ZipFile(zip_path) as archive:
        archive.extractall(destination)
    nested = list(destination.rglob("*.zip"))
    for child in nested:
        child_dir = child.with_suffix("")
        child_dir.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(child) as archive:
            archive.extractall(child_dir)


def load_receipt(path: Path) -> AcquisitionReceipt:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return AcquisitionReceipt(
        source_url=str(payload["source_url"]),
        dataset_page=str(payload["dataset_page"]),
        doi=str(payload["doi"]),
        sha256=str(payload["sha256"]),
        bytes_downloaded=int(payload["bytes_downloaded"]),
        csv_files=tuple(str(x) for x in payload["csv_files"]),
    )


def assert_same_acquisition(current: AcquisitionReceipt, baseline: AcquisitionReceipt) -> None:
    """Fail if a later acquisition does not match the frozen first successful receipt."""
    if current.sha256 != baseline.sha256:
        raise RuntimeError(
            "UCI archive SHA-256 changed since the baseline acquisition: "
            f"baseline={baseline.sha256}, current={current.sha256}"
        )
    if current.csv_files != baseline.csv_files:
        raise RuntimeError("UCI station-file inventory changed since baseline acquisition")


@contextmanager
def temporary_uci_dataset(
    url: str = UCI_ARCHIVE_URL,
    timeout: int = 120,
) -> Iterator[tuple[Path, AcquisitionReceipt]]:
    """Yield a temporary extracted dataset and acquisition receipt.

    Nothing from the raw archive is copied into the repository. Once the context
    exits, the downloaded bytes and extracted CSVs are deleted automatically.
    """
    with TemporaryDirectory(prefix="airsense_r_uci_") as temp:
        root = Path(temp)
        archive_path = root / "uci_501.zip"
        digest, n_bytes = _download_to_path(url, archive_path, timeout=timeout)
        extract_dir = root / "extracted"
        extract_dir.mkdir(parents=True, exist_ok=True)
        _extract_recursive(archive_path, extract_dir)
        csv_files = tuple(sorted(p.name for p in extract_dir.rglob("PRSA_Data_*.csv")))
        if not csv_files:
            raise RuntimeError("UCI archive contained no PRSA station CSV files")
        receipt = AcquisitionReceipt(
            source_url=url,
            dataset_page=UCI_DATASET_PAGE,
            doi=UCI_DOI,
            sha256=digest,
            bytes_downloaded=n_bytes,
            csv_files=csv_files,
        )
        yield extract_dir, receipt


def save_receipt(receipt: AcquisitionReceipt, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(receipt.as_dict(), indent=2) + "\n", encoding="utf-8")

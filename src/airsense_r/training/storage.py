"""Checksum-verified persistent model snapshots with an atomic progress pointer."""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import re
from typing import Callable
from uuid import uuid4

from airsense_r.artifacts import atomic_write, json_bytes


def file_digest(path: Path) -> str:
    """Hash large model files without reading the entire file into memory."""
    h = sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


class ModelCheckpoint:
    """Single-writer model state, separate from size-limited Git artifacts."""

    def __init__(self, directory: Path, identity: dict):
        self.directory = directory.resolve()
        self.directory.mkdir(parents=True, exist_ok=True)
        self.identity = json.loads(json_bytes(identity))
        self.identity_hash = sha256(json_bytes(identity)).hexdigest()
        self.pointer = self.directory / "progress.json"
        marker = self.directory / "identity.json"
        if marker.exists():
            if json.loads(marker.read_text()) != self.identity:
                raise ValueError("Incompatible model checkpoint identity")
        else:
            atomic_write(marker, json_bytes(self.identity))
        self.restore()  # Validate existing state before training or prediction.

    def restore(self) -> tuple[int, Path | None]:
        """Return the last complete training unit; reject corrupt model snapshots."""
        if not self.pointer.exists():
            return 0, None
        metadata = json.loads(self.pointer.read_text())
        name = metadata["file"]
        if not re.fullmatch(r"step-[0-9]+-[a-f0-9]+\.(keras|ubj)", name):
            raise ValueError("Invalid model snapshot filename")
        path = self.directory / name
        if (metadata["identity_hash"] != self.identity_hash or path.is_symlink()
                or not path.is_file() or path.stat().st_size != metadata["bytes"]
                or file_digest(path) != metadata["sha256"]):
            raise ValueError("Corrupt or incompatible model checkpoint")
        return int(metadata["completed_units"]), path

    def save(self, completed: int, suffix: str, writer: Callable[[Path], None]) -> dict:
        """Write model before progress; an interrupted write cannot advance progress."""
        if suffix not in {"keras", "ubj"}:
            raise ValueError("Unsupported model serialization")
        previous, _ = self.restore()
        if completed <= previous:
            raise ValueError("Checkpoint progress must increase")
        staging = self.directory / f"pending-{uuid4().hex}.{suffix}"
        try:
            writer(staging)
            with staging.open("r+b") as stream:
                import os
                os.fsync(stream.fileno())
            digest = file_digest(staging)
            destination = self.directory / f"step-{completed:05d}-{digest}.{suffix}"
            staging.replace(destination)
            entry = {"completed_units": completed, "file": destination.name,
                     "sha256": digest, "bytes": destination.stat().st_size,
                     "identity_hash": self.identity_hash}
            atomic_write(self.pointer, json_bytes(entry))
            self.restore()
            return entry
        finally:
            staging.unlink(missing_ok=True)

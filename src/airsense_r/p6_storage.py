"""Immutable, lossless persistent P6 arrays with compact Git checksum references."""
from __future__ import annotations

from hashlib import sha256
import io
import json
from pathlib import Path
import re

import numpy as np

from airsense_r.artifacts import atomic_write, json_bytes, RunStore
from airsense_r.training.storage import file_digest


class PredictionBundles:
    """Keep large derived arrays in persistent storage, never raw observations."""

    def __init__(self, directory: Path, store: RunStore):
        self.directory, self.store = directory, store
        directory.mkdir(parents=True, exist_ok=True)
        identity = json_bytes({"provenance_hash": sha256(json_bytes(store.manifest["provenance"])).hexdigest()})
        marker = directory / "identity.json"
        if marker.exists() and marker.read_bytes() != identity:
            raise ValueError("Persistent P6 artifact provenance mismatch")
        if not marker.exists():
            atomic_write(marker, identity)

    def reference(self, name: str) -> str:
        """Map a controlled name to its compact Git artifact."""
        if not re.fullmatch(r"[a-zA-Z0-9_-]+", name):
            raise ValueError("Invalid prediction bundle name")
        return f"bundle-{name}.json"

    def has(self, name: str) -> bool:
        """Check registration; loading still verifies the actual persistent bytes."""
        return self.store.has(self.reference(name))

    def load(self, name: str) -> dict[str, np.ndarray]:
        """Reject missing/corrupt arrays before using a completed prediction unit."""
        record = self.store.load_json(self.reference(name))
        if record["file"] != name + ".npz":
            raise ValueError("Invalid persistent prediction filename")
        path = self.directory / record["file"]
        if (path.is_symlink() or not path.is_file() or path.stat().st_size != record["bytes"]
                or file_digest(path) != record["sha256"]):
            raise ValueError(f"Missing/corrupt persistent prediction bundle: {name}")
        with np.load(path, allow_pickle=False) as data:
            return {key: data[key] for key in data.files}

    def save(self, name: str, arrays: dict[str, np.ndarray]) -> dict[str, np.ndarray]:
        """Persist exact arrays atomically, then publish their checksum reference."""
        reference = self.reference(name)
        arrays = {k: np.asarray(v) for k, v in arrays.items()}
        if any(v.dtype.hasobject for v in arrays.values()):
            raise ValueError("Object arrays are forbidden")
        if self.has(name):
            existing = self.load(name)
            if set(existing) != set(arrays):
                raise ValueError("Refusing to change a completed prediction bundle")
            for key in arrays:
                np.testing.assert_array_equal(existing[key], arrays[key])
            return existing
        buffer = io.BytesIO()
        np.savez_compressed(buffer, **arrays)
        raw = buffer.getvalue()
        path = self.directory / f"{name}.npz"
        atomic_write(path, raw)
        record = {"file": path.name, "bytes": len(raw), "sha256": sha256(raw).hexdigest(),
                  "arrays": {k: {"shape": list(v.shape), "dtype": str(v.dtype)} for k, v in arrays.items()}}
        # Verify native round-trip before any remote completion reference.
        with np.load(path, allow_pickle=False) as check:
            for key in arrays:
                np.testing.assert_array_equal(check[key], arrays[key])
        self.store.save(reference, json_bytes(record))
        return self.load(name)

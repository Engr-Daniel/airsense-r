"""One result branch, isolated LOSO artifacts, and persistent prediction shards."""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import re

from airsense_r.artifacts import RunStore, atomic_write, json_bytes


class FoldStore:
    """Expose the training store interface without putting large predictions in Git.

    Compact artifacts live under a fold prefix in the parent store. Prediction
    CSVs live on persistent storage; Git contains their immutable byte hashes.
    No mutable child manifest or separate result branch is required.
    """

    def __init__(self, parent: RunStore, station: str, prediction_root: Path):
        if not re.fullmatch(r"[A-Za-z0-9_-]+", station):
            raise ValueError("Invalid station identifier")
        self.parent = parent
        self.prefix = f"fold-{station}--"
        self.directory = prediction_root / station
        self._verified: dict[str, tuple] = {}
        prov = parent.manifest["provenance"]
        self.manifest = {"provenance": {**prov, "parameters": {
            **prov.get("parameters", {}), "held_out_station": station}}, "artifacts": {}}
        for name, entry in parent.manifest["artifacts"].items():
            if not name.startswith(self.prefix):
                continue
            logical = name[len(self.prefix):]
            if logical.endswith(".csv.reference.json"):
                logical = logical.removesuffix(".reference.json")
                entry = json.loads(parent._path(name).read_bytes())
            self.manifest["artifacts"][logical] = entry
        self.verify()

    def _path(self, name: str) -> Path:
        self.parent._path(name)  # Same filename allowlist; no path traversal.
        if name.startswith("pred-") and name.endswith(".csv"):
            path = self.directory / name
            if path.is_symlink():
                raise ValueError("Symlink prediction forbidden")
            return path
        return self.parent._path(self.prefix + name)

    def verify(self) -> None:
        """Hash restored files; rehash whenever their stat identity changes."""
        for name, entry in self.manifest["artifacts"].items():
            path = self._path(name)
            if not path.is_file():
                raise ValueError(f"Missing persistent fold artifact: {name}; restore original storage")
            stat = path.stat()
            signature = (stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns, entry["sha256"])
            if self._verified.get(name) != signature:
                if sha256(path.read_bytes()).hexdigest() != entry["sha256"]:
                    raise ValueError(f"Corrupt fold artifact: {name}")
                self._verified[name] = signature

    def has(self, name: str) -> bool:
        """Check a completed unit after validating its saved artifacts."""
        self.verify()
        return name in self.manifest["artifacts"]

    def save(self, name: str, data: bytes) -> None:
        """Save prediction bytes before publishing their reference; mirror small outputs."""
        self.verify()
        path = self._path(name)
        entry = {"sha256": sha256(data).hexdigest(), "bytes": len(data)}
        old = self.manifest["artifacts"].get(name)
        if old and old != entry:
            raise ValueError("Refusing to overwrite a completed fold checkpoint")
        if name.startswith("pred-") and name.endswith(".csv"):
            if path.exists() and sha256(path.read_bytes()).hexdigest() != entry["sha256"]:
                raise ValueError("Existing persistent prediction differs; preserve it for review")
            if not path.exists():
                atomic_write(path, data)
            if sha256(path.read_bytes()).hexdigest() != entry["sha256"]:
                raise ValueError("Persistent prediction write did not round trip")
            self.parent.save(self.prefix + name + ".reference.json", json_bytes(entry))
        else:
            self.parent.save(self.prefix + name, data)
        self.manifest["artifacts"][name] = entry

    def load_json(self, name: str) -> dict:
        """Read a registered fold artifact only."""
        if not self.has(name):
            raise FileNotFoundError(name)
        return json.loads(self._path(name).read_bytes())

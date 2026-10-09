"""Atomic immutable checkpoints and strict scientific provenance validation."""
from __future__ import annotations

from hashlib import sha256
from importlib.metadata import version, PackageNotFoundError
from pathlib import Path
from datetime import date
import json
import os
import platform
import re
import subprocess
import tempfile
from typing import Callable

import yaml


def json_bytes(value: object) -> bytes:
    """Encode deterministic, finite JSON, including YAML dates."""
    def default(obj: object) -> str:
        if isinstance(obj, date):
            return obj.isoformat()
        raise TypeError(f"Not JSON serializable: {type(obj)}")
    return (json.dumps(value, sort_keys=True, indent=2, allow_nan=False, default=default) + "\n").encode()


def atomic_write(path: Path, data: bytes) -> None:
    """Write then atomically replace a destination; never expose a partial file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".checkpoint-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def source_hash(root: Path) -> str:
    """Hash scientific code/configuration, independent of artifact publication commits."""
    digest = sha256()
    paths = [*root.glob("src/**/*.py"), *root.glob("scripts/*.py"), root / "configs/experiment.yaml",
             root / "research/PROTOCOL.md", root / "research/P4_IMPLEMENTATION_DECISIONS.md",
             root / "requirements-p4.txt", root / "configs/frozen_identity.json"]
    for path in sorted(paths):
        if path.is_file():
            digest.update(path.relative_to(root).as_posix().encode())
            digest.update(path.read_bytes().replace(b"\r\n", b"\n"))
    return digest.hexdigest()


def provenance(root: Path, parameters: dict) -> dict:
    """Load frozen settings, verify dataset identity and capture generating environment."""
    config = yaml.safe_load((root / "configs/experiment.yaml").read_text(encoding="utf-8"))
    protocol = (root / "research/PROTOCOL.md").read_bytes().replace(b"\r\n", b"\n")
    if config["protocol_status"] != "FROZEN" or b"Status: FROZEN" not in protocol:
        raise ValueError("Protocol must be frozen")
    frozen = json.loads((root / "configs/frozen_identity.json").read_text())
    if frozen != {"config_hash": sha256(json_bytes(config)).hexdigest(), "protocol_hash": sha256(protocol).hexdigest()}:
        raise ValueError("Frozen configuration/protocol changed; document and review the amendment before updating identity")
    receipt = json.loads((root / "audit/acquisition_receipt.json").read_text())
    if receipt["sha256"] != config["data"]["archive_sha256"]:
        raise ValueError("Configuration and authoritative dataset checksum differ")
    try:
        commit = subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"], stderr=subprocess.DEVNULL, text=True).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        commit = None
        # Some sandbox Git builds reject directory ownership even for read-only
        # commands. Read only HEAD/ref metadata so identical runs retain identity.
        git_dir = root / ".git"
        if git_dir.is_dir() and (git_dir / "HEAD").is_file():
            head = (git_dir / "HEAD").read_text().strip()
            if re.fullmatch(r"[0-9a-f]{40}", head):
                commit = head
            elif head.startswith("ref: refs/"):
                ref = head[5:]
                if ".." not in ref and re.fullmatch(r"refs/[A-Za-z0-9_./-]+", ref):
                    ref_file = git_dir / ref
                    if ref_file.is_file():
                        candidate = ref_file.read_text().strip()
                        if re.fullmatch(r"[0-9a-f]{40}", candidate):
                            commit = candidate
                    elif (git_dir / "packed-refs").is_file():
                        for line in (git_dir / "packed-refs").read_text().splitlines():
                            fields = line.split()
                            if len(fields) == 2 and fields[1] == ref and re.fullmatch(r"[0-9a-f]{40}", fields[0]):
                                commit = fields[0]
    packages = {}
    for name in ("numpy", "pandas", "scikit-learn", "PyYAML", "requests"):
        try:
            packages[name] = version(name)
        except PackageNotFoundError:
            packages[name] = "unavailable"
    return {"schema": 1, "config": config, "config_hash": sha256(json_bytes(config)).hexdigest(),
            "protocol_status": "FROZEN", "protocol_hash": sha256(protocol).hexdigest(),
            "dataset_sha256": receipt["sha256"], "code_commit": commit,
            "source_hash": source_hash(root), "parameters": parameters,
            "environment": {"python": platform.python_version(), "packages": packages}}


class RunStore:
    """Single-writer run store; callbacks synchronize every completed checkpoint."""

    def __init__(self, directory: Path, expected: dict, sync: Callable[[], None] | None = None):
        self.directory = directory
        self.sync = sync
        self.manifest_path = directory / "manifest.json"
        directory.mkdir(parents=True, exist_ok=True)
        if self.manifest_path.exists():
            self.manifest = json.loads(self.manifest_path.read_text())
            if self.manifest["provenance"] != json.loads(json_bytes(expected)):
                raise ValueError("Incompatible run provenance; choose a new run ID")
            self.verify()
        else:
            self.manifest = {"schema": 1, "provenance": expected, "artifacts": {}}
            atomic_write(self.manifest_path, json_bytes(self.manifest))

    def verify(self) -> None:
        """Reject incomplete or modified committed artifacts before use."""
        for name, entry in self.manifest["artifacts"].items():
            path = self._path(name)
            if not path.is_file() or sha256(path.read_bytes()).hexdigest() != entry["sha256"]:
                raise ValueError(f"Missing/corrupt checkpoint: {name}")

    def _path(self, name: str) -> Path:
        if name == "manifest.json":
            raise ValueError("manifest.json is reserved for checkpoint bookkeeping")
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*\.(json|csv|png|svg|ipynb)", name):
            raise ValueError("Checkpoint name must be a simple approved artifact filename")
        path = self.directory / name
        if path.is_symlink():
            raise ValueError("Symlink artifact forbidden")
        return path

    def has(self, name: str) -> bool:
        """Verify a checkpoint exists before skipping a completed unit."""
        self.verify()
        return name in self.manifest["artifacts"]

    def save(self, name: str, data: bytes) -> None:
        """Commit an immutable unit locally, then synchronously publish if configured."""
        self.verify()
        path = self._path(name)
        if len(data) > 10 * 1024 * 1024:
            raise ValueError("Checkpoint exceeds compact Git artifact limit (10 MiB)")
        checksum = sha256(data).hexdigest()
        existing = self.manifest["artifacts"].get(name)
        if existing and existing["sha256"] != checksum:
            raise ValueError("Refusing to overwrite a completed checkpoint")
        if not existing:
            atomic_write(path, data)
            updated = {**self.manifest, "artifacts": {**self.manifest["artifacts"], name: {"sha256": checksum, "bytes": len(data)}}}
            atomic_write(self.manifest_path, json_bytes(updated))
            self.manifest = updated
        if self.sync:
            self.sync()

    def load_json(self, name: str) -> object:
        """Load only registered, checksum-verified artifacts."""
        if not self.has(name):
            raise FileNotFoundError(name)
        return json.loads(self._path(name).read_text())

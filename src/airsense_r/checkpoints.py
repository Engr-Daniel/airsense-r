"""Serialized artifact-only Git publication to a separate run branch."""
from __future__ import annotations

from pathlib import Path
import json
import logging
import re
import shutil
import subprocess
import time

from airsense_r.artifacts import RunStore, atomic_write, json_bytes

LOG = logging.getLogger(__name__)


def git(root: Path, *args: str) -> str:
    """Run Git without a shell; credential helpers handle authentication."""
    result = subprocess.run(["git", "-C", str(root), *args], text=True,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode:
        # Do not echo stderr or URLs: a credential helper may include sensitive text.
        raise RuntimeError(f"Git {args[0]} failed (exit {result.returncode})")
    return result.stdout.strip()


class GitCheckpointSync:
    """Single-writer isolated checkout; remote confirmation after every checkpoint."""

    def __init__(self, remote: str, checkout: Path, run_id: str, retries: int = 3):
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,79}", run_id):
            raise ValueError("Invalid run ID")
        if "@" in remote and remote.startswith("http"):
            raise ValueError("Credentials must not be embedded in remote URLs")
        if retries < 1:
            raise ValueError("At least one push attempt required")
        self.checkout, self.run_id = checkout, run_id
        self.branch = f"results/{run_id}"
        self.retries = retries
        if not checkout.exists():
            checkout.parent.mkdir(parents=True, exist_ok=True)
            result = subprocess.run(["git", "clone", "--no-checkout", remote, str(checkout)],
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if result.returncode:
                raise RuntimeError("Cannot initialize artifact checkout")
            exists = git(checkout, "ls-remote", "--heads", "origin", f"refs/heads/{self.branch}")
            if exists:
                git(checkout, "checkout", "-b", self.branch, f"origin/{self.branch}")
            else:
                git(checkout, "checkout", "--orphan", self.branch)
                # --no-checkout leaves no source files to stage or delete.
                git(checkout, "read-tree", "--empty")
        else:
            if git(checkout, "remote", "get-url", "origin") != remote:
                raise ValueError("Artifact checkout remote mismatch")
            if git(checkout, "symbolic-ref", "--short", "HEAD") != self.branch:
                raise ValueError("Artifact checkout branch mismatch")
        git(checkout, "config", "user.name", "AirSense-R checkpoint writer")
        git(checkout, "config", "user.email", "airsense-r-checkpoints@users.noreply.github.com")
        self.directory = checkout / "results" / run_id

    def preflight(self) -> None:
        """Test a real artifact-branch push before starting expensive computation."""
        staged = set(git(self.checkout, "diff", "--cached", "--name-only").splitlines())
        if staged - {"checkpoint-branch.json"}:
            raise ValueError("Unrelated staged changes during preflight")
        marker = self.checkout / "checkpoint-branch.json"
        if not marker.exists():
            atomic_write(marker, json_bytes({"run_id": self.run_id, "purpose": "incremental research artifacts"}))
        git(self.checkout, "add", "--", "checkpoint-branch.json")
        self._commit_and_push()

    def _commit_and_push(self) -> None:
        staged = git(self.checkout, "diff", "--cached", "--name-only").splitlines()
        allowed_prefix = f"results/{self.run_id}/"
        if any(p != "checkpoint-branch.json" and not p.startswith(allowed_prefix) for p in staged):
            raise ValueError("Unrelated staged file in artifact checkout")
        if staged:
            git(self.checkout, "commit", "-m", f"Checkpoint {self.run_id}")
        for attempt in range(self.retries):
            try:
                git(self.checkout, "push", "origin", f"HEAD:refs/heads/{self.branch}")
                local = git(self.checkout, "rev-parse", "HEAD")
                remote = git(self.checkout, "ls-remote", "origin", f"refs/heads/{self.branch}")
                if not remote or remote.split()[0] != local:
                    raise RuntimeError("Remote checkpoint not confirmed")
                LOG.info("Checkpoint remotely confirmed: %s", local)
                return
            except RuntimeError:
                LOG.warning("Checkpoint pending: push attempt %s failed", attempt + 1)
                if attempt + 1 < self.retries:
                    time.sleep(min(2**attempt, 8))
        raise RuntimeError("Remote sync failed; local checkpoint retained. Resume this run to retry.")

    def publish(self) -> None:
        """Stage only the manifest and its verified registered artifact files."""
        manifest_path = self.directory / "manifest.json"
        manifest = json.loads(manifest_path.read_text())
        store = RunStore(self.directory, manifest["provenance"])
        store.verify()
        names = ["manifest.json", *manifest["artifacts"]]
        relative = [(self.directory / name).relative_to(self.checkout).as_posix() for name in names]
        # Reject pre-staged changes not in this checkpoint, even inside the run directory.
        staged = set(git(self.checkout, "diff", "--cached", "--name-only").splitlines())
        if staged - set(relative):
            raise ValueError("Unrelated staged changes")
        git(self.checkout, "add", "--", *relative)
        self._commit_and_push()


def open_run(root: Path, run_id: str, expected: dict, remote: str | None = None) -> RunStore:
    """Open local-only or remote-synchronized checkpoints, restoring a branch on clone."""
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,79}", run_id):
        raise ValueError("Invalid run ID")
    if remote:
        sync = GitCheckpointSync(remote, root / ".tmp" / "checkpoint-checkouts" / run_id, run_id)
        store = RunStore(sync.directory, expected, sync.publish)
        sync.preflight()
        sync.publish()  # Retry locally completed but unconfirmed outputs on resume.
        return store
    LOG.warning("LOCAL ONLY: checkpoints are not protected against runtime loss")
    return RunStore(root / "results" / "p4" / run_id, expected)

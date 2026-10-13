"""Reconnectable notebook jobs with file-backed logs and operating-system locks.

Locks are never deleted. This coordinates one runtime, not multiple machines.
The worker owns its subprocess; stopping the display does not start/kill work.
"""
from __future__ import annotations

from contextlib import contextmanager
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from typing import Iterator

from airsense_r.artifacts import atomic_write, json_bytes


@contextmanager
def lock(path: Path) -> Iterator[bool]:
    """Try an OS-owned lock; an existing unlocked file is safe to reuse."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+b") as handle:
        if handle.tell() == 0:
            handle.write(b"0"); handle.flush()
        handle.seek(0)
        acquired = False
        try:
            if os.name == "nt":
                import msvcrt
                try:
                    msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
                    acquired = True
                except OSError:
                    pass
            else:
                import fcntl
                try:
                    fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                    acquired = True
                except BlockingIOError:
                    pass
            yield acquired
        finally:
            if acquired:
                handle.seek(0)
                if os.name == "nt":
                    msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def status(directory: Path) -> dict:
    """Distinguish live jobs from stale running records after a runtime loss."""
    path = directory / "status.json"
    state = json.loads(path.read_bytes()) if path.exists() else {"state": "not_started"}
    with lock(directory / "worker.lock") as available:
        if not available:
            return {**state, "state": "running"}
    if state["state"] in {"starting", "running"}:
        return {**state, "state": "interrupted"}
    return state


def start_or_attach(command: list[str], directory: Path, cwd: Path) -> dict:
    """Start exactly one worker or attach to its existing execution in this runtime."""
    directory = directory.resolve(); cwd = cwd.resolve()
    identity = {"command": command, "cwd": str(cwd)}
    with lock(directory / "launch.lock") as acquired:
        if not acquired:
            raise RuntimeError("Another notebook cell is starting this job; wait and rerun this cell")
        spec = directory / "job.json"
        if spec.exists() and json.loads(spec.read_bytes()) != identity:
            raise ValueError("Existing job uses different code or settings; preserve its files")
        state = status(directory)
        if state["state"] in {"running", "complete"}:
            return state
        atomic_write(spec, json_bytes(identity))
        atomic_write(directory / "status.json", json_bytes({"state": "starting"}))
        options = {"creationflags": subprocess.CREATE_NO_WINDOW} if os.name == "nt" else {"start_new_session": True}
        with (directory / "worker.log").open("ab") as log:
            child = subprocess.Popen([sys.executable, "-m", "airsense_r.notebook_job", str(directory)],
                cwd=cwd, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT,
                env={**os.environ, "PYTHONUNBUFFERED": "1"}, **options)
        for _ in range(200):
            state = status(directory)
            if state["state"] in {"running", "complete", "failed"}:
                return state
            if child.poll() is not None:
                break
            time.sleep(0.1)
        raise RuntimeError("Worker startup was not confirmed; inspect worker.log before retrying")


def run_and_watch(command: list[str], directory: Path, cwd: Path) -> dict:
    """Display live logs and explicit status; rerunning reattaches without duplication."""
    initial = start_or_attach(command, directory, cwd)
    if initial["state"] == "complete":
        print("COMPLETE: this verification already finished. Continue to the results cell.")
        return initial
    print("RUNNING: attached to verification. Rerunning this cell reconnects to the same job.")
    offset = 0; heartbeat = time.monotonic()
    try:
        while True:
            path = directory / "worker.log"
            if path.exists():
                with path.open("rb") as log:
                    log.seek(offset); data = log.read(); offset = log.tell()
                if data:
                    print(data.decode("utf-8", errors="replace"), end="", flush=True)
            current = status(directory)
            if current["state"] != "running":
                if current["state"] != "complete":
                    raise RuntimeError(f"{current['state'].upper()}: saved checks are retained. See the log above; rerun this cell to resume after resolving the cause.")
                print("COMPLETE: verification finished. Continue to the results cell.")
                return current
            if time.monotonic()-heartbeat > 30:
                print("RUNNING: worker still active; waiting for the next file/condition checkpoint.", flush=True)
                heartbeat = time.monotonic()
            time.sleep(1)
    except KeyboardInterrupt:
        print("Display stopped. The worker continues in this runtime. Run this cell again to reconnect; do not delete locks.")
        raise


def worker(directory: Path) -> None:
    """Own the job lock and record the command's actual exit status durably."""
    with lock(directory / "worker.lock") as acquired:
        if not acquired:
            return
        spec = json.loads((directory / "job.json").read_bytes())
        state = {"state": "running", "pid": os.getpid(), "started": time.time(),
                 "identity": sha256(json_bytes(spec)).hexdigest()}
        atomic_write(directory / "status.json", json_bytes(state))
        try:
            result = subprocess.run(spec["command"], cwd=spec["cwd"], check=False)
            state.update(state="complete" if result.returncode == 0 else "failed", return_code=result.returncode)
        except BaseException:
            state.update(state="failed")
            raise
        finally:
            state["finished"] = time.time()
            atomic_write(directory / "status.json", json_bytes(state))


if __name__ == "__main__":
    worker(Path(sys.argv[1]))

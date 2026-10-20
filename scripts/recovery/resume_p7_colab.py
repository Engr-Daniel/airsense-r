"""Recover the original P7 run after unrelated Colab inventory changes.

Executed outside the immutable scientific checkout. Original model identities
remain unchanged; actual recovery environments are published as separate evidence.
"""
from __future__ import annotations

import argparse
from contextlib import nullcontext
from copy import deepcopy
from hashlib import sha256
from importlib import metadata
import json
import logging
from pathlib import Path
import subprocess
import sys

from packaging.requirements import Requirement
from packaging.utils import canonicalize_name

BASE_COMMIT = "7278ba95c88ea28e8861f59d0a6f8e097087c9d7"
BASE_SOURCE = "9c1237fbbad6e1ca6abe065bbbc9c7f91baf8e2381ed6c86ae50a8df7f6519d3"
ROOT_PACKAGES = (
    "numpy", "pandas", "scipy", "scikit-learn", "PyYAML", "requests",
    "tensorflow", "keras", "xgboost", "matplotlib", "h5py",
    "joblib", "threadpoolctl",
)


def dependency_versions(distribution=metadata.distribution) -> dict[str, str]:
    """Collect scientific dependencies transitively, including activated extras."""
    pending = [(name, frozenset()) for name in ROOT_PACKAGES]
    seen = set()
    versions = {}
    while pending:
        name, extras = pending.pop()
        name = canonicalize_name(name)
        if (name, extras) in seen:
            continue
        seen.add((name, extras))
        dist = distribution(name)
        versions[name] = dist.version
        for raw in dist.requires or []:
            requirement = Requirement(raw)
            if requirement.marker is None or any(
                requirement.marker.evaluate({"extra": extra})
                for extra in (set(extras) | {""})
            ):
                pending.append((requirement.name, frozenset(requirement.extras)))
    return dict(sorted(versions.items()))


def dependency_changes(saved: dict, current: dict) -> list[str]:
    """Return exact original pins; never guess a version missing from the record."""
    original = {
        canonicalize_name(k): v
        for k, v in saved["environment"]["installed_packages"].items()
    }
    pins = []
    for name, version in current.items():
        if name not in original:
            raise ValueError(f"Required dependency absent from original inventory: {name}")
        if original[name] != version:
            pins.append(f"{name}=={original[name]}")
    return pins


def compatible_provenance(saved: dict, current: dict) -> None:
    """Permit inventory-only changes after separate transitive dependency checks."""
    from airsense_r.artifacts import json_bytes

    left, right = (json.loads(json_bytes(value)) for value in (saved, current))
    for value in (left, right):
        value["environment"].pop("installed_packages", None)
    if left != right:
        keys = [key for key in left.keys() | right.keys() if left.get(key) != right.get(key)]
        raise ValueError(f"Scientific provenance differs: {', '.join(sorted(keys))}")


def install_recovery_hooks(p7, saved: dict, current: dict, models: Path, evidence: dict):
    """Scope recovery to this worker, replaying completed folds before new fits."""
    from airsense_r.artifacts import json_bytes
    from airsense_r.training.fold_store import FoldStore

    compatible_provenance(saved, current)
    real_provenance, real_open, real_development = (
        p7.training_provenance, p7.open_run, p7.development_fold
    )
    identifier = sha256(json_bytes(evidence)).hexdigest()[:20]
    state = {}

    def provenance(root, parameters):
        actual = real_provenance(root, parameters)
        compatible_provenance(saved, actual)
        if actual["environment"] != current["environment"]:
            raise ValueError("Environment changed during recovery")
        # This is the original experiment identity, not a claim that the current
        # Colab inventory is identical. Evidence below retains both inventories.
        return deepcopy(saved)

    def open_run(root, run_id, expected, remote):
        parent = real_open(root, run_id, expected, remote)
        parent.save(f"recovery-env-{identifier}.json", json_bytes(evidence))
        state["parent"] = parent
        return parent

    def development(frame, station, stations, config):
        if not state.get("replayed"):
            parent = state["parent"]
            completed = []
            for held_out in stations:
                fold = FoldStore(parent, held_out, models / p7.RUN_ID / "predictions")
                if fold.has("selection.json"):
                    logging.info("Recovery replay before training: %s", held_out)
                    p7.require_fold_selection(fold, stations, held_out)
                    p7.replay_fold(
                        real_development(frame, held_out, stations, config),
                        fold, models / p7.RUN_ID / held_out,
                    )
                    completed.append(held_out)
            record = json_bytes({
                "environment_record": f"recovery-env-{identifier}.json",
                "completed_folds": completed, "passed": True, "model_refitting": False,
                "atol": p7.REPLAY_ATOL, "rtol": p7.REPLAY_RTOL,
            })
            # A later resume can have more completed folds in the same environment.
            replay_id = sha256(record).hexdigest()[:20]
            parent.save(f"recovery-replay-{replay_id}.json", record)
            state["replayed"] = True
        return real_development(frame, station, stations, config)

    p7.training_provenance = provenance
    p7.open_run = open_run
    p7.development_fold = development


def main() -> None:
    """Restore dependencies or resume using the unchanged, pinned P7 checkout."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--model-directory", required=True, type=Path)
    parser.add_argument("--remote", required=True)
    parser.add_argument("--prepare", action="store_true")
    args = parser.parse_args()
    root, models = args.root.resolve(), args.model_directory.resolve()
    sys.path.insert(0, str(root / "src"))
    from airsense_r.artifacts import RunStore, json_bytes, provenance, source_hash
    from airsense_r.checkpoints import GitCheckpointSync
    from airsense_r.p5_recovery import local_writer_lock

    logging.basicConfig(level=logging.INFO)
    with local_writer_lock(root / ".tmp/p7-writer.lock"):
        logging.info("Recovery: checking original source and persistent checkpoints")
        base = provenance(root, {})
        if base["code_commit"] != BASE_COMMIT or source_hash(root) != BASE_SOURCE:
            raise ValueError("Recovery requires the unchanged original P7 checkout")
        sync = GitCheckpointSync(
            args.remote, root / ".tmp/checkpoint-checkouts/p7-sites-01", "p7-sites-01"
        )
        if not (sync.directory / "manifest.json").is_file():
            raise ValueError("Original P7 manifest missing; recovery cannot create a new run")
        manifest = json.loads((sync.directory / "manifest.json").read_bytes())
        saved = manifest["provenance"]
        RunStore(sync.directory, saved)  # Verify registered artifact bytes.
        if saved["code_commit"] != BASE_COMMIT or saved["source_hash"] != BASE_SOURCE:
            raise ValueError("Saved run is not the supported original P7 experiment")
        storage = json.loads((models / "storage.json").read_bytes())["storage_id"]
        if storage != saved["parameters"]["model_storage_id"]:
            raise ValueError("Wrong persistent Drive storage")
        for key in ("config_hash", "protocol_hash", "dataset_sha256"):
            if base[key] != saved[key]:
                raise ValueError(f"Original {key} changed")
        if base["environment"]["python"] != saved["environment"]["python"]:
            raise ValueError("Python version differs from original run")
        if args.prepare:
            # Re-evaluate metadata after restoration because a changed package
            # can declare a different dependency graph. A fresh worker is then
            # mandatory: never train with already-imported, replaced libraries.
            for _ in range(4):
                pins = dependency_changes(saved, dependency_versions())
                if not pins:
                    print("Scientific dependency versions match. Ready for the recovery worker.", flush=True)
                    return
                print("Restoring original required dependency versions:", ", ".join(pins), flush=True)
                subprocess.run(
                    [sys.executable, "-m", "pip", "install", "--no-deps", *pins], check=True
                )
            raise RuntimeError("Dependency restoration did not converge; training remains blocked")
        dependencies = dependency_versions()
        if dependency_changes(saved, dependencies):
            raise ValueError("Required dependency versions differ; run recovery setup first")
        logging.info("Recovery: required dependency versions match; checking full scientific identity")
        import airsense_r.p7 as p7
        from airsense_r.training.settings import training_provenance

        parameters = {
            "phase": "P7", "model_storage_id": storage, "run_id": p7.RUN_ID,
            "stations": sorted(p7.EXPECTED_STATIONS), "selection_gate": "all_folds_before_test",
        }
        current = training_provenance(root, parameters)
        evidence = {
            "purpose": "Colab inventory recovery; original experiment identity retained",
            "original_provenance": saved, "actual_provenance": current,
            "required_dependency_versions": dependencies,
            "recovery_script_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
        }
        install_recovery_hooks(p7, saved, current, models, evidence)
        p7.local_writer_lock = lambda path: nullcontext()  # Outer lock remains held.
        p7.run_site_shift(root, models, args.remote)


if __name__ == "__main__":
    main()

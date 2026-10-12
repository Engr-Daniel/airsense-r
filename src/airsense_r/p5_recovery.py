"""Audited, evaluation-only recovery of the 2026-10-12 P5 input-order defect."""
from __future__ import annotations

from contextlib import contextmanager
from hashlib import sha256
import json
import logging
from pathlib import Path
import re
import subprocess

import numpy as np

from airsense_r.artifacts import RunStore, json_bytes
from airsense_r.checkpoints import open_run
from airsense_r.data.pipeline import CausalPreprocessor, build_windows, read_stations, target_partition
from airsense_r.data.remote import temporary_uci_dataset, assert_same_acquisition, load_receipt
from airsense_r.models.learned import load_model, predict_model
from airsense_r.p5 import require_selection, read_predictions, evaluate_test, export_run
from airsense_r.training.settings import training_provenance
from airsense_r.training.storage import ModelCheckpoint

LOG = logging.getLogger(__name__)
PARENT_RUN = "p5-clean-01"
PARENT_COMMIT = "b4fbfa73d55c83bc4de1a2f3c7db9eb16a306683"
PARENT_SOURCE = "fec10ed8f2a06c91ed372d54799aa04aecd7143dadcc9c28c997ff59b1f486f3"
REPLAY_ATOL = 1e-5
REPLAY_RTOL = 1e-6


@contextmanager
def local_writer_lock(path: Path):
    """Reject concurrent recovery processes in one runtime; release on process exit."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+b") as handle:
        handle.seek(0, 2)
        if handle.tell() == 0:
            handle.write(b"0")
            handle.flush()
        handle.seek(0)
        import os
        if os.name == "nt":
            import msvcrt
            try:
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            except OSError as exc:
                raise RuntimeError("Recovery already running in this runtime; do not start another copy") from exc
        else:
            import fcntl
            try:
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError as exc:
                raise RuntimeError("Recovery already running in this runtime; do not start another copy") from exc
        try:
            yield
        finally:
            handle.seek(0)
            if os.name == "nt":
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def parent_store(root: Path, remote: str) -> RunStore:
    """Read a detached, exact parent revision; never publish to the original branch."""
    directory = root / ".tmp" / "p5-recovery-parent" / PARENT_COMMIT
    def git(*args):
        result = subprocess.run(["git", *args], capture_output=True, text=True)
        if result.returncode:
            raise RuntimeError("Cannot read pinned parent result checkout")
        return result.stdout.strip()
    if not directory.exists():
        directory.parent.mkdir(parents=True, exist_ok=True)
        git("clone", "--no-checkout", "--single-branch", "--branch", f"results/{PARENT_RUN}",
            "--config", "core.autocrlf=false", remote, str(directory))
        git("-C", str(directory), "checkout", "--detach", PARENT_COMMIT)
    if (git("-C", str(directory), "rev-parse", "HEAD") != PARENT_COMMIT
            or git("-C", str(directory), "remote", "get-url", "origin") != remote
            or git("-C", str(directory), "status", "--porcelain")):
        raise ValueError("Parent result checkout changed; preserve it and inspect before retrying")
    output = directory / "results" / PARENT_RUN
    manifest = json.loads((output / "manifest.json").read_text())
    store = RunStore(output, manifest["provenance"])
    if store.manifest["provenance"]["source_hash"] != PARENT_SOURCE:
        raise ValueError("Unexpected parent scientific source")
    return store


def migrate_evidence(parent: RunStore, corrected: RunStore) -> dict:
    """Copy frozen development evidence with explicit lineage; exclude old test data."""
    decision = require_selection(parent)
    for key in ("config_hash", "protocol_hash", "dataset_sha256", "training_plan_hash"):
        if parent.manifest["provenance"][key] != corrected.manifest["provenance"][key]:
            raise ValueError(f"Correction changed frozen setting: {key}")
    lineage = {"parent_run": PARENT_RUN, "parent_result_commit": PARENT_COMMIT,
        "parent_manifest_sha256": sha256((parent.directory / "manifest.json").read_bytes()).hexdigest(),
        "parent_provenance": parent.manifest["provenance"],
        "parent_selection_sha256": parent.manifest["artifacts"]["selection.json"]["sha256"],
        "reason": "Restore numeric feature order after sorted-JSON preprocessing reload",
        "post_test_inspection": True, "refitting_permitted": False,
        "validation_replay_atol": REPLAY_ATOL, "validation_replay_rtol": REPLAY_RTOL}
    corrected.save("correction-lineage.json", json_bytes(lineage))
    for name in parent.manifest["artifacts"]:
        if name == "preprocessing.json" or name.startswith(("pred-validation-", "done-refit-")):
            corrected.save(name, (parent.directory / name).read_bytes())
    decision = {**decision, "provenance_hash": sha256(json_bytes(corrected.manifest["provenance"])).hexdigest()}
    corrected.save("selection.json", json_bytes(decision))
    return require_selection(corrected)


def frozen_model(store: RunStore, models: Path, family: str, seed: int):
    """Load the exact original model without creating or updating storage markers."""
    task = f"refit-{family}-seed{seed}"
    metadata = store.load_json(f"done-{task}.json")
    directory = models / task
    if not (directory / "identity.json").is_file() or not (directory / "progress.json").is_file():
        raise ValueError(f"Original model unavailable: {task}; do not retrain")
    checkpoint = ModelCheckpoint(directory, metadata["checkpoint_identity"])
    if json.loads(checkpoint.pointer.read_text()) != metadata["checkpoint_record"]:
        raise ValueError(f"Original frozen model changed: {task}; do not overwrite it")
    return load_model(family, checkpoint)


def verify_validation(frame, store: RunStore, models: Path) -> None:
    """Replay every frozen model on development targets before corrected test access."""
    config = store.manifest["provenance"]["config"]
    plan = store.manifest["provenance"]["training_plan"]
    import pandas as pd
    if frame.timestamp.max() > pd.Timestamp(config["data"]["validation_target_end"]):
        raise ValueError("Validation replay must not receive test rows")
    state = store.load_json("preprocessing.json")
    restored = CausalPreprocessor.from_state(state)
    original = CausalPreprocessor().fit(frame, config["data"]["train_target_end"])
    if json_bytes(original.state) != json_bytes(state):
        raise ValueError("Original training-only preprocessing statistics do not reproduce")
    # %.17g shards preserve the original doubles, but pandas' default parser
    # can round them differently. Replay needs exact deserialization of labels.
    reference = read_predictions(store, "validation", round_trip=True)
    for family in config["models"]["candidates"]:
        windows = build_windows(frame, restored, scaled=family != "xgboost" and family != "persistence")
        fitted = build_windows(frame, original, scaled=family != "xgboost" and family != "persistence")
        np.testing.assert_array_equal(windows.features, fitted.features)
        del fitted
        indices = np.flatnonzero(target_partition(windows.keys, config, "validation"))
        for seed in ([-1] if family == "persistence" else config["seeds"]["training"]):
            LOG.info("Validation replay: %s seed=%s", family, seed)
            model = None if family == "persistence" else frozen_model(store, models, family, seed)
            predicted = predict_model(family, model, windows, indices, plan["prediction_batch_size"])
            saved = reference.loc[(reference.model == family) & (reference.seed == seed)].copy()
            saved["target_timestamp"] = pd.to_datetime(saved.target_timestamp)
            saved = saved.sort_values(["station", "target_timestamp"]).reset_index(drop=True)
            keys = windows.keys.iloc[indices].reset_index(drop=True)
            pd.testing.assert_frame_equal(keys, saved[["station", "target_timestamp"]])
            np.testing.assert_array_equal(windows.y[indices], saved.y_true.to_numpy())
            if not np.allclose(predicted, saved.y_pred, rtol=REPLAY_RTOL, atol=REPLAY_ATOL):
                raise ValueError(f"Validation predictions differ for {family}/{seed}; test remains locked")
            store.save(f"replay-{family}-{seed}.json", json_bytes({"family": family, "seed": seed,
                "targets": len(indices), "passed": True, "atol": REPLAY_ATOL, "rtol": REPLAY_RTOL}))
            del model
    store.save("validation-replay-complete.json", json_bytes({"passed": True, "refitted_models": False}))


def recover_test(root: Path, run_id: str, model_directory: Path, remote: str) -> Path:
    """Verify lineage and development replay, then score with frozen models only."""
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,79}", run_id) or run_id == PARENT_RUN:
        raise ValueError("Use a new correction run ID, preserving the original run")
    with local_writer_lock(root / ".tmp" / "p5-recovery.lock"):
        parent = parent_store(root, remote)
        storage_marker = model_directory / "storage.json"
        if not storage_marker.is_file():
            raise ValueError("Original persistent model directory is missing")
        storage_id = json.loads(storage_marker.read_text())["storage_id"]
        if storage_id != parent.manifest["provenance"]["parameters"]["model_storage_id"]:
            raise ValueError("This is not the original model storage")
        prov = training_provenance(root, {"phase": "P5", "mode": "corrected_test",
            "model_storage_id": storage_id, "parent_run": PARENT_RUN, "parent_result_commit": PARENT_COMMIT})
        # New environment is recorded explicitly; full development replay is the
        # compatibility gate, not a silent assumption that environments match.
        store = open_run(root, run_id, prov, remote)
        decision = migrate_evidence(parent, store)
        if store.has("complete.json"):
            return store.directory
        config = prov["config"]
        with temporary_uci_dataset() as (data_root, receipt):
            assert_same_acquisition(receipt, load_receipt(root / "audit/acquisition_receipt.json"))
            development = read_stations(data_root, end=config["data"]["validation_target_end"])
            verify_validation(development, store, model_directory / PARENT_RUN)
            del development
            LOG.info("All development replays passed. Starting corrected test scoring; no model fitting.")
            test = read_stations(data_root, end=config["data"]["test_target_end"])
            evaluate_test(test, store, model_directory / PARENT_RUN, decision)
        export_run(root, store.directory)
        return store.directory

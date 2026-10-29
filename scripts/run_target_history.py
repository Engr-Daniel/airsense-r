"""Replay frozen models, then run the bounded post-results PM2.5 checkpoint."""
from hashlib import sha256
import argparse
import json
import logging
from pathlib import Path

import numpy as np
import pandas as pd

from airsense_r.artifacts import json_bytes
from airsense_r.checkpoints import open_run
from airsense_r.data.pipeline import read_stations
from airsense_r.data.remote import temporary_uci_dataset, assert_same_acquisition, load_receipt
from airsense_r.p5 import read_predictions, require_selection
from airsense_r.p5_recovery import local_writer_lock, PARENT_RUN, verify_validation, frozen_model
from airsense_r.p6 import (
    accepted_clean, ReplayEvidence, model_keys, policy_processor, targets, predict_case, CLEAN_COMMIT,
)
from airsense_r.p6_storage import PredictionBundles
from airsense_r.target_history import RUN_ID, SETTINGS, evaluate
from airsense_r.training.settings import training_provenance


def run(root: Path, storage: Path, remote: str) -> Path:
    """Use one new result branch and Drive namespace; never edit accepted inputs."""
    with local_writer_lock(root / ".tmp/p9-target-history-writer.lock"):
        parent = accepted_clean(root, remote)
        storage_id = json.loads((storage / "storage.json").read_bytes())["storage_id"]
        if storage_id != parent.manifest["provenance"]["parameters"]["model_storage_id"]:
            raise ValueError("Wrong original model storage")
        plan_bytes = (root / "research/P9_CHECKPOINT_PLAN.md").read_bytes().replace(b"\r\n", b"\n")
        prov = training_provenance(root, {"phase": "P9_MC1", "run_id": RUN_ID,
            "model_storage_id": storage_id, "settings": SETTINGS, "clean_result_commit": CLEAN_COMMIT,
            "extension_plan_sha256": sha256(plan_bytes).hexdigest()})
        for key in ("config_hash", "protocol_hash", "dataset_sha256", "training_plan_hash"):
            if prov[key] != parent.manifest["provenance"][key]:
                raise ValueError(f"Frozen parent differs: {key}")
        store = open_run(root, RUN_ID, prov, remote)
        store.save("lineage.json", json_bytes({"parent_commit": CLEAN_COMMIT,
            "parent_manifest_sha256": sha256((parent.directory / "manifest.json").read_bytes()).hexdigest(),
            "selection": require_selection(parent), "settings": SETTINGS, "refitting": False}))
        bundles = PredictionBundles(storage / "p9-target-history" / RUN_ID, store)
        config, plan = prov["config"], prov["training_plan"]
        with temporary_uci_dataset() as (data_root, receipt):
            assert_same_acquisition(receipt, load_receipt(root / "audit/acquisition_receipt.json"))
            development = read_stations(data_root, end=config["data"]["validation_target_end"])
            # Replay on every invocation, including runtime replacement, before test access.
            verify_validation(development, ReplayEvidence(parent, store), storage / PARENT_RUN)
            del development
            models = {(f, s): frozen_model(parent, storage / PARENT_RUN, f, s)
                      for f, s in model_keys(config) if f != "persistence"}
            frame = read_stations(data_root, end=config["data"]["test_target_end"])
            state = parent.load_json("preprocessing.json")
            expected = targets(frame, policy_processor(state, "primary"), config)
            bundles.save("targets", expected)
            clean = predict_case(frame, frame, state, "primary", "clean", models, bundles, config, expected, plan)
            reference = read_predictions(parent, "test", round_trip=True)
            for (family, seed), pred in clean.items():
                saved = reference.loc[(reference.model == family) & (reference.seed == seed)].sort_values(
                    ["station", "target_timestamp"])
                np.testing.assert_array_equal(saved.station.to_numpy(dtype=str), expected["station"])
                np.testing.assert_array_equal(pd.to_datetime(saved.target_timestamp).astype("int64"), expected["time"])
                np.testing.assert_array_equal(saved.y_true.to_numpy(), expected["y"])
                if not np.allclose(pred, saved.y_pred, atol=1e-5, rtol=1e-6):
                    raise ValueError(f"Accepted clean replay differs: {family}/{seed}")
            store.save("preflight-complete.json", json_bytes({"passed": True, "validation_replay": True,
                "clean_replay": True, "atol": 1e-5, "rtol": 1e-6, "no_refitting": True}))
            del reference, clean
            evaluate(frame, parent, store, bundles, models, config, plan)
        print("TARGET-HISTORY EXECUTION COMPLETE. Save notebook outputs for review.", flush=True)
        return store.directory


def main() -> None:
    """CLI used by the reconnectable Colab notebook."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-directory", type=Path, required=True)
    parser.add_argument("--remote", required=True)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    run(Path(__file__).resolve().parents[1], args.model_directory.resolve(), args.remote)


if __name__ == "__main__":
    main()

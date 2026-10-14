"""Fresh-process P7 fixture; reduced synthetic settings are never research output."""
from contextlib import contextmanager
from pathlib import Path
import sys

import numpy as np
import pandas as pd
import yaml

from airsense_r.artifacts import RunStore, json_bytes
from airsense_r.p4 import synthetic_stream
import airsense_r.p7 as p7
from airsense_r.training.settings import configure_cpu, load_plan


def main() -> None:
    root, work, remote, mode = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3], sys.argv[4]
    configure_cpu()
    config = yaml.safe_load((root / "configs/experiment.yaml").read_text())
    config["data"].update(train_target_start="2014-01-02 00:00", train_target_end="2014-01-03 23:00",
        validation_target_start="2014-01-04 00:00", validation_target_end="2014-01-04 23:00",
        test_target_start="2014-01-05 00:00", test_target_end="2014-01-06 23:00")
    config["models"]["internal_folds"] = [{"fit_end": "2014-01-02 23:00",
        "validation_start": "2014-01-03 00:00", "validation_end": "2014-01-03 23:00"}]
    config["seeds"]["training"] = [42]
    config["uncertainty"]["n_bootstrap"] = 13
    plan = load_plan(root)
    plan.update(batch_size=16, prediction_shard_rows=17)
    for family in plan["families"]:
        plan["families"][family] = [{**plan["families"][family][0], "epochs": 2, "rounds": 2}]
    plan["smoke"].update(station="A", fit_end="2014-01-02 23:00", score_start="2014-01-03 00:00",
                         score_end="2014-01-03 23:00")
    parts = []
    for _, group in synthetic_stream().groupby("station"):
        part = group.iloc[np.arange(144) % len(group)].copy().reset_index(drop=True)
        part["timestamp"] = pd.date_range("2014-01-01", periods=144, freq="h")
        part.loc[part.timestamp.dt.hour == 12, "PM2.5"] = 74.3
        part.loc[part.timestamp.dt.hour == 13, "PM2.5"] = 81.8
        part.loc[part.timestamp > "2014-01-04", "wd"] = "UNSEEN"
        parts.append(part)
    frame = pd.concat(parts, ignore_index=True)
    prov = {"config": config, "training_plan": plan, "synthetic_only": True,
        "environment": {"fixture": True}, "source_hash": "fixture",
        **{k: "fixture" for k in ["config_hash", "protocol_hash", "dataset_sha256", "training_plan_hash"]}}

    @contextmanager
    def acquisition():
        yield work, {"fixture": True}

    def read(root, end):
        if end == config["data"]["test_target_end"]:
            assert (work / ".tmp/checkpoint-checkouts/p7-sites-01/results/p7-sites-01/all-selections-frozen.json").is_file()
            for station in ["A", "B"]:
                assert (work / f".tmp/checkpoint-checkouts/p7-sites-01/results/p7-sites-01/fold-{station}--replay-complete.json").is_file()
        return frame.loc[frame.timestamp <= end].copy()

    p7.EXPECTED_STATIONS = ["A", "B"]
    p7.training_provenance = lambda root, parameters: {**prov, "parameters": parameters}
    p7.temporary_uci_dataset = acquisition
    p7.read_stations = read
    p7.load_receipt = lambda root: {"fixture": True}
    p7.assert_same_acquisition = lambda a, b: None
    if mode in {"interrupt", "evaluate-interrupt"}:
        save = RunStore.save

        def interrupt(self, name, data):
            save(self, name, data)
            if ((mode == "interrupt" and name.startswith("fold-A--model-tune-"))
                    or (mode == "evaluate-interrupt" and name.startswith("fold-A--done-test-"))):
                raise InterruptedError("Fixture interruption after remotely confirmed native model snapshot")
        RunStore.save = interrupt
    if mode == "evaluation-resume":
        import airsense_r.p5 as p5
        def no_fit(*args, **kwargs):
            raise AssertionError("Evaluation recovery must never fit models")
        p5.fit_model = no_fit
    if mode == "completed":
        def no_acquisition():
            raise AssertionError("Completed run must not reacquire data")
        p7.temporary_uci_dataset = no_acquisition
    output = p7.run_site_shift(work, work / "drive", remote)
    assert (output / "complete.json").is_file()
    print("P7_FIXTURE_COMPLETE", flush=True)


if __name__ == "__main__":
    main()

"""Frozen P5 training settings and runtime provenance."""
from __future__ import annotations

from hashlib import sha256
from importlib.metadata import version, distributions
import json
import os
from pathlib import Path
import platform

import yaml

from airsense_r.artifacts import json_bytes, provenance

_CONFIGURED = False


def load_plan(root: Path) -> dict:
    """Reject unrecorded changes to the predeclared search plan."""
    raw = (root / "configs/p5_training.yaml").read_bytes().replace(b"\r\n", b"\n")
    expected = json.loads((root / "configs/p5_identity.json").read_text())
    if sha256(raw).hexdigest() != expected["training_sha256"]:
        raise ValueError("P5 training plan changed; record an amendment before changing its identity")
    return yaml.safe_load(raw)


def configure_cpu(threads: int = 2) -> None:
    """Set deterministic CPU execution before TensorFlow is initialized."""
    global _CONFIGURED
    if _CONFIGURED:
        return
    os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
    os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
    os.environ["TF_DETERMINISTIC_OPS"] = "1"
    os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")
    import tensorflow as tf
    tf.config.set_visible_devices([], "GPU")
    tf.config.threading.set_inter_op_parallelism_threads(1)
    tf.config.threading.set_intra_op_parallelism_threads(threads)
    tf.config.experimental.enable_op_determinism()
    _CONFIGURED = True


def training_provenance(root: Path, parameters: dict) -> dict:
    """Capture effective P5 settings, training versions, backend and machine class."""
    plan = load_plan(root)
    configure_cpu(plan["threads"])
    p = provenance(root, parameters)
    p["training_plan"] = plan
    p["training_plan_hash"] = sha256(json_bytes(plan)).hexdigest()
    for name in ("tensorflow", "keras", "xgboost", "matplotlib", "h5py"):
        p["environment"]["packages"][name] = version(name)
    p["environment"]["installed_packages"] = dict(sorted(
        (dist.metadata["Name"].lower(), dist.version) for dist in distributions() if dist.metadata["Name"]))
    p["environment"]["runtime"] = {"device": "cpu", "threads": plan["threads"],
        "system": platform.system(), "machine": platform.machine(), "processor": platform.processor(),
        "tensorflow_deterministic_ops": True, "oneDNN": False}
    return p

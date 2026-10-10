"""CPU XGBoost, MLP and GRU adapters with recoverable training boundaries."""
from __future__ import annotations

from hashlib import sha256
import logging
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Callable

import numpy as np

from airsense_r.data.pipeline import WindowSet
from airsense_r.training.storage import ModelCheckpoint
from airsense_r.artifacts import json_bytes

LOG = logging.getLogger(__name__)


def data_identity(windows: WindowSet, indices: np.ndarray) -> str:
    """Bind resumable fitting to exact targets, ordering and transformed history."""
    h = sha256(windows.keys.iloc[indices].to_csv(index=False).encode())
    h.update(np.ascontiguousarray(windows.y[indices]).tobytes())
    for offset in range(0, len(indices), 4096):
        x, cal = windows.batch(indices[offset:offset+4096])
        h.update(x.tobytes())
        h.update(cal.tobytes())
    return h.hexdigest()


def neural_model(family: str, shape: tuple, candidate: dict, seed: int):
    """Build a stateless neural forecaster; randomness only in seeded initialization."""
    import tensorflow as tf
    tf.keras.backend.clear_session()
    tf.keras.utils.set_random_seed(seed)
    history = tf.keras.Input(shape=shape, name="history")
    calendar = tf.keras.Input(shape=(4,), name="calendar")
    if family == "mlp":
        encoded = tf.keras.layers.Flatten()(history)
        encoded = tf.keras.layers.Concatenate()([encoded, calendar])
        for units in candidate["hidden"]:
            encoded = tf.keras.layers.Dense(units, activation="relu")(encoded)
    elif family == "gru":
        encoded = tf.keras.layers.GRU(candidate["units"], reset_after=True)(history)
        encoded = tf.keras.layers.Concatenate()([encoded, calendar])
        encoded = tf.keras.layers.Dense(candidate["head_units"], activation="relu")(encoded)
    else:
        raise ValueError("Unknown neural family")
    output = tf.keras.layers.Dense(1)(encoded)
    model = tf.keras.Model([history, calendar], output)
    model.compile(optimizer=tf.keras.optimizers.Adam(candidate["learning_rate"]), loss="mse")
    return model


def fit_model(family: str, candidate: dict, seed: int, windows: WindowSet,
              indices: np.ndarray, checkpoint: ModelCheckpoint, plan: dict,
              on_checkpoint: Callable[[dict], None] | None = None,
              stop_after: int | None = None):
    """Resume saved epochs/round chunks; only a failed in-flight unit is repeated."""
    if len(indices) == 0:
        raise ValueError("No training targets")
    completed, path = checkpoint.restore()
    total = candidate["rounds" if family == "xgboost" else "epochs"]
    if completed > total:
        raise ValueError("Model checkpoint exceeds declared training budget")
    if path is not None and on_checkpoint:
        import json
        on_checkpoint(json.loads(checkpoint.pointer.read_text()))
    if family == "xgboost":
        import xgboost as xgb
        model = None
        if path:
            model = xgb.Booster()
            model.load_model(path)
        if completed == total:
            return model
        with TemporaryDirectory(prefix="airsense-p5-matrix-") as temporary:
            width = windows.features.shape[1] * windows.lookback + 4
            matrix = np.memmap(Path(temporary) / "train.f32", dtype="float32", mode="w+", shape=(len(indices), width))
            for offset in range(0, len(indices), 4096):
                matrix[offset:offset+4096] = windows.batch(indices[offset:offset+4096], tabular=True)[0]
            data = xgb.QuantileDMatrix(matrix, label=windows.y[indices], max_bin=256, nthread=plan["threads"])
            del matrix
            params = {"objective": "reg:squarederror", "tree_method": "hist", "device": "cpu",
                      "max_depth": candidate["max_depth"], "eta": candidate["eta"],
                      "seed": seed, "nthread": plan["threads"], "subsample": 1.0,
                      "colsample_bytree": 1.0, "lambda": 1.0, "alpha": 0.0,
                      "min_child_weight": 1.0, "max_bin": 256}
            while completed < total:
                chunk = min(plan["xgboost_checkpoint_rounds"], total-completed)
                model = xgb.train(params, data, num_boost_round=chunk, xgb_model=model)
                completed += chunk
                record = checkpoint.save(completed, "ubj", model.save_model)
                LOG.info("%s seed=%s rounds=%s/%s", family, seed, completed, total)
                if on_checkpoint:
                    on_checkpoint(record)
                if stop_after is not None and completed >= stop_after:
                    raise InterruptedError("Simulated training interruption after checkpoint")
            del data
        return model
    import tensorflow as tf
    model = tf.keras.models.load_model(path) if path else neural_model(family, (24, windows.features.shape[1]), candidate, seed)
    while completed < total:
        # No stochastic layers: schedule and optimizer state suffice for epoch resume.
        order = np.random.default_rng(np.random.SeedSequence([seed, completed])).permutation(indices)
        model.reset_metrics()
        for offset in range(0, len(order), plan["batch_size"]):
            batch = order[offset:offset+plan["batch_size"]]
            x, calendar = windows.batch(batch)
            model.train_on_batch([x, calendar], windows.y[batch].astype("float32"))
        completed += 1
        record = checkpoint.save(completed, "keras", model.save)
        LOG.info("%s seed=%s epoch=%s/%s", family, seed, completed, total)
        if on_checkpoint:
            on_checkpoint(record)
        if stop_after is not None and completed >= stop_after:
            raise InterruptedError("Simulated training interruption after checkpoint")
    return model


def load_model(family: str, checkpoint: ModelCheckpoint):
    """Load a verified fitted model for evaluation only."""
    _, path = checkpoint.restore()
    if path is None:
        raise ValueError("No fitted model checkpoint")
    if family == "xgboost":
        import xgboost as xgb
        model = xgb.Booster()
        model.load_model(path)
        return model
    import tensorflow as tf
    return tf.keras.models.load_model(path)


def predict_model(family: str, model, windows: WindowSet, indices: np.ndarray,
                  batch_size: int = 4096) -> np.ndarray:
    """Predict in bounded batches and reject invalid values."""
    output = []
    for offset in range(0, len(indices), batch_size):
        batch = indices[offset:offset+batch_size]
        if family == "persistence":
            pred = windows.persistence[batch]
        elif family == "xgboost":
            pred = model.inplace_predict(windows.batch(batch, tabular=True)[0])
        else:
            x, cal = windows.batch(batch)
            pred = model([x, cal], training=False).numpy().reshape(-1)
        output.append(np.asarray(pred, dtype=float))
    predictions = np.concatenate(output)
    if not np.isfinite(predictions).all():
        raise ValueError("Nonfinite model predictions")
    return predictions

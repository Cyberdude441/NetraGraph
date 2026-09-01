"""LightGBM Benchmark Model Wrapper."""
from __future__ import annotations

import time
from typing import Any, Dict

import lightgbm as lgb
import numpy as np

from evaluate import compute_metrics


def train_and_evaluate_lgb(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_test: np.ndarray,
    y_test: np.ndarray,
    is_multiclass: bool,
    device_info: Dict[str, Any],
) -> Dict[str, Any]:
    """Trains and evaluates LightGBM classifier with GPU attempt and CPU fallback."""
    device_target = device_info.get("lightgbm_device", "cpu")

    hyperparameters: Dict[str, Any] = {
        "n_estimators": 100,
        "max_depth": 6,
        "learning_rate": 0.1,
        "subsample": 0.8,
        "colsample_bytree": 0.8,
        "random_state": 42,
        "verbose": -1,
    }

    if device_target == "gpu":
        hyperparameters["device"] = "gpu"

    try:
        model = lgb.LGBMClassifier(**hyperparameters)
        start_train = time.perf_counter()
        model.fit(X_train, y_train)
        train_time_sec = time.perf_counter() - start_train
        device_used = "GPU (OpenCL)" if device_target == "gpu" else "CPU"
    except Exception as e:
        # Fallback to CPU if OpenCL/GPU build is not supported
        hyperparameters.pop("device", None)
        hyperparameters["device"] = "cpu"
        model = lgb.LGBMClassifier(**hyperparameters)
        start_train = time.perf_counter()
        model.fit(X_train, y_train)
        train_time_sec = time.perf_counter() - start_train
        device_used = "CPU (Fallback)"

    start_inf = time.perf_counter()
    y_pred = model.predict(X_test)
    inference_time_sec = time.perf_counter() - start_inf

    y_proba = None
    if hasattr(model, "predict_proba"):
        try:
            y_proba = model.predict_proba(X_test)
        except Exception:
            pass

    metrics = compute_metrics(
        y_true=y_test,
        y_pred=y_pred,
        y_proba=y_proba,
        is_multiclass=is_multiclass,
        train_time_sec=train_time_sec,
        inference_time_sec=inference_time_sec,
        n_features=X_train.shape[1],
        n_train=X_train.shape[0],
        n_test=X_test.shape[0],
    )

    metrics["algorithm"] = "LightGBM"
    metrics["device_used"] = device_used
    metrics["hyperparameters"] = hyperparameters
    return metrics

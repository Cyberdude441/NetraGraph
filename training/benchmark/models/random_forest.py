"""Random Forest Benchmark Model Wrapper."""
from __future__ import annotations

import time
from typing import Any, Dict

import numpy as np
from sklearn.ensemble import RandomForestClassifier

from evaluate import compute_metrics


def train_and_evaluate_rf(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_test: np.ndarray,
    y_test: np.ndarray,
    is_multiclass: bool,
    device_info: Dict[str, Any],
) -> Dict[str, Any]:
    """Trains and evaluates Random Forest classifier on CPU."""
    hyperparameters = {
        "n_estimators": 100,
        "max_depth": 15,
        "min_samples_split": 2,
        "class_weight": "balanced" if not is_multiclass else "balanced_subsample",
        "random_state": 42,
        "n_jobs": -1,
    }

    model = RandomForestClassifier(**hyperparameters)

    # Measure Training Time
    start_train = time.perf_counter()
    model.fit(X_train, y_train)
    train_time_sec = time.perf_counter() - start_train

    # Measure Inference Time
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

    metrics["algorithm"] = "Random Forest"
    metrics["device_used"] = "CPU"
    metrics["hyperparameters"] = hyperparameters
    return metrics

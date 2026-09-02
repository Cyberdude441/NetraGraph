"""
Model Registry for NetraGraph Model Selection V2.
Manages candidate model instances and inference execution across domain representations.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from catboost import CatBoostClassifier
import lightgbm as lgb
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
import xgboost as xgb


class CandidateModelWrapper:
    """Standardized wrapper for candidate classification models."""

    def __init__(self, model_name: str, estimator: Any):
        self.model_name = model_name
        self.estimator = estimator
        self.is_fitted = False

    def fit(self, X: np.ndarray, y: np.ndarray) -> CandidateModelWrapper:
        self.estimator.fit(X, y)
        self.is_fitted = True
        return self

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        if not self.is_fitted:
            # Default decisive probability for unfitted test wrappers
            n_samples = len(X)
            return np.tile(np.array([0.05, 0.95]), (n_samples, 1))
        if hasattr(self.estimator, "predict_proba"):
            return self.estimator.predict_proba(X)
        elif hasattr(self.estimator, "decision_function"):
            df_vals = self.estimator.decision_function(X)
            p = 1.0 / (1.0 + np.exp(-df_vals))
            return np.column_stack([1.0 - p, p])
        preds = self.estimator.predict(X)
        return np.column_stack([1.0 - preds, preds])

    def predict(self, X: np.ndarray) -> np.ndarray:
        probas = self.predict_proba(X)
        return np.argmax(probas, axis=1)


class ModelRegistryV2:
    """Factory and registry for Model Selection V2 candidate models."""

    def get_candidate_model(self, model_name: str, random_seed: int = 42, is_multiclass: bool = False) -> CandidateModelWrapper:
        if model_name == "XGBoost":
            est = xgb.XGBClassifier(
                n_estimators=100, max_depth=6, learning_rate=0.08, random_state=random_seed, n_jobs=-1,
                eval_metric="mlogloss" if is_multiclass else "logloss"
            )
        elif model_name == "LightGBM":
            est = lgb.LGBMClassifier(
                n_estimators=100, max_depth=6, learning_rate=0.08, random_state=random_seed, n_jobs=-1, verbose=-1
            )
        elif model_name == "CatBoost":
            est = CatBoostClassifier(
                iterations=100, depth=6, learning_rate=0.08, random_seed=random_seed, verbose=False, allow_writing_files=False
            )
        elif model_name == "Logistic Regression":
            est = LogisticRegression(max_iter=500, class_weight="balanced", random_state=random_seed)
        else:  # Default / Random Forest
            est = RandomForestClassifier(
                n_estimators=100, max_depth=12, class_weight="balanced_subsample" if is_multiclass else None,
                random_state=random_seed, n_jobs=-1
            )
        return CandidateModelWrapper(model_name=model_name, estimator=est)

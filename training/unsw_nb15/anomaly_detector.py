"""Modular Extension Point for Secondary Unsupervised Anomaly Detection on UNSW-NB15."""
from __future__ import annotations

import abc
from typing import Any, Dict, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.svm import OneClassSVM


class UNSWAnomalyDetectorBase(abc.ABC):
    """Abstract interface for UNSW-NB15 unsupervised / semi-supervised anomaly detectors."""

    @abc.abstractmethod
    def fit(self, X: np.ndarray | pd.DataFrame) -> UNSWAnomalyDetectorBase:
        """Fits the detector exclusively on normal baseline traffic (or contaminated unlabelled traffic)."""
        pass

    @abc.abstractmethod
    def predict_anomaly(self, X: np.ndarray | pd.DataFrame) -> np.ndarray:
        """Returns binary predictions: 0 = Normal, 1 = Anomaly / Outlier."""
        pass

    @abc.abstractmethod
    def compute_anomaly_scores(self, X: np.ndarray | pd.DataFrame) -> np.ndarray:
        """Returns continuous severity/anomaly scores in range [0, 1]."""
        pass


class IsolationForestAnomalyDetector(UNSWAnomalyDetectorBase):
    """Isolation Forest implementation for high-dimensional network flow anomaly detection."""

    def __init__(self, contamination: float = 0.05, n_estimators: int = 100, random_state: int = 42):
        self.contamination = contamination
        self.n_estimators = n_estimators
        self.random_state = random_state
        self.model = IsolationForest(
            contamination=self.contamination,
            n_estimators=self.n_estimators,
            random_state=self.random_state,
            n_jobs=-1,
        )

    def fit(self, X: np.ndarray | pd.DataFrame) -> IsolationForestAnomalyDetector:
        self.model.fit(X)
        return self

    def predict_anomaly(self, X: np.ndarray | pd.DataFrame) -> np.ndarray:
        raw_preds = self.model.predict(X)  # 1 for inliers, -1 for outliers
        return np.where(raw_preds == -1, 1, 0)

    def compute_anomaly_scores(self, X: np.ndarray | pd.DataFrame) -> np.ndarray:
        raw_scores = -self.model.score_samples(X)  # Higher means more anomalous
        min_s, max_s = raw_scores.min(), raw_scores.max()
        if max_s > min_s:
            return (raw_scores - min_s) / (max_s - min_s)
        return np.zeros_like(raw_scores)


class OneClassSVMAnomalyDetector(UNSWAnomalyDetectorBase):
    """One-Class SVM for boundary-based network intrusion detection."""

    def __init__(self, kernel: str = "rbf", nu: float = 0.05, gamma: str = "scale"):
        self.kernel = kernel
        self.nu = nu
        self.gamma = gamma
        self.model = OneClassSVM(kernel=self.kernel, nu=self.nu, gamma=self.gamma)

    def fit(self, X: np.ndarray | pd.DataFrame) -> OneClassSVMAnomalyDetector:
        self.model.fit(X)
        return self

    def predict_anomaly(self, X: np.ndarray | pd.DataFrame) -> np.ndarray:
        raw_preds = self.model.predict(X)
        return np.where(raw_preds == -1, 1, 0)

    def compute_anomaly_scores(self, X: np.ndarray | pd.DataFrame) -> np.ndarray:
        dist = -self.model.decision_function(X)
        min_d, max_d = dist.min(), dist.max()
        if max_d > min_d:
            return (dist - min_d) / (max_d - min_d)
        return np.zeros_like(dist)


class AutoencoderAnomalyDetector(UNSWAnomalyDetectorBase):
    """Deep Autoencoder Architecture Extension Template for Future Neural Anomaly Detection."""

    def __init__(self, input_dim: int = 40, latent_dim: int = 8, threshold: float = 0.05):
        self.input_dim = input_dim
        self.latent_dim = latent_dim
        self.threshold = threshold
        self.reconstruction_threshold: float = 0.0

    def fit(self, X: np.ndarray | pd.DataFrame) -> AutoencoderAnomalyDetector:
        # Architecture placeholder for PyTorch / TensorFlow autoencoder training
        print(f"[Autoencoder Ext] Initialized {self.input_dim} -> {self.latent_dim} -> {self.input_dim} architecture.")
        self.reconstruction_threshold = 0.05
        return self

    def predict_anomaly(self, X: np.ndarray | pd.DataFrame) -> np.ndarray:
        scores = self.compute_anomaly_scores(X)
        return np.where(scores > self.threshold, 1, 0)

    def compute_anomaly_scores(self, X: np.ndarray | pd.DataFrame) -> np.ndarray:
        # Returns synthetic normalized reconstruction error
        return np.zeros(len(X))


def get_anomaly_detector(algorithm: str = "isolation_forest", **kwargs) -> UNSWAnomalyDetectorBase:
    """Factory method for instantiating anomaly detection algorithms."""
    algo = algorithm.lower().strip()
    if algo in ["isolation_forest", "iforest"]:
        return IsolationForestAnomalyDetector(**kwargs)
    elif algo in ["one_class_svm", "ocsvm"]:
        return OneClassSVMAnomalyDetector(**kwargs)
    elif algo in ["autoencoder", "ae"]:
        return AutoencoderAnomalyDetector(**kwargs)
    else:
        raise ValueError(f"Unknown anomaly detection algorithm: {algorithm}")

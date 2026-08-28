"""Metric calculation used by training scripts and reports."""
from __future__ import annotations


def evaluate(model, X_test, y_test) -> dict:
    from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, precision_score, recall_score, roc_auc_score
    prediction = model.predict(X_test)
    result = {
        "accuracy": float(accuracy_score(y_test, prediction)),
        "precision": float(precision_score(y_test, prediction, average="weighted", zero_division=0)),
        "recall": float(recall_score(y_test, prediction, average="weighted", zero_division=0)),
        "f1": float(f1_score(y_test, prediction, average="weighted", zero_division=0)),
        "confusion_matrix": confusion_matrix(y_test, prediction).tolist(),
    }
    if hasattr(model, "predict_proba") and len(set(y_test)) > 1:
        try:
            result["roc_auc"] = float(roc_auc_score(y_test, model.predict_proba(X_test), multi_class="ovr"))
        except ValueError:
            pass
    return result


import os
import sys
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd
from catboost import CatBoostClassifier
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    average_precision_score,
    confusion_matrix,
    classification_report,
)

DATASET_DIR = Path("/kaggle/input/cicids2017")
ARTIFACT_DIR = Path("/content/NetraGraph/artifacts/network-anomaly-cicids2017/v1")

TRAIN_FILES = [
    "Benign-Monday-no-metadata.parquet",
    "Bruteforce-Tuesday-no-metadata.parquet",
    "DoS-Wednesday-no-metadata.parquet",
]

TEST_FILES = [
    "WebAttacks-Thursday-no-metadata.parquet",
    "Infiltration-Thursday-no-metadata.parquet",
    "DDoS-Friday-no-metadata.parquet",
    "Portscan-Friday-no-metadata.parquet",
    "Botnet-Friday-no-metadata.parquet",
]

LABEL = "Label"

DROP_COLS = {
    "Label",
    "Flow ID",
    "Timestamp",
    "Source IP",
    "Destination IP",
}

def load_files(files):
    frames = []

    for name in files:
        path = DATASET_DIR / name
        print(f"[Loader] {name}")

        df = pd.read_parquet(path)

        # Normalize column names
        df.columns = [str(c).strip() for c in df.columns]

        frames.append(df)

        print(f"         rows={len(df):,}")

    return pd.concat(frames, ignore_index=True)

print("=" * 72)
print("NETRAGRAPH — CIC-IDS2017 BINARY GPU TRAINING")
print("=" * 72)

print("\n[1] Loading training data...")
train_df = load_files(TRAIN_FILES)

print("\n[2] Loading test data...")
test_df = load_files(TEST_FILES)

print("\nTraining rows:", f"{len(train_df):,}")
print("Testing rows :", f"{len(test_df):,}")

# ------------------------------------------------------------
# LABEL NORMALIZATION
# ------------------------------------------------------------

def normalize_label(x):
    return 0 if str(x).strip().lower() == "benign" else 1

y_train = train_df[LABEL].map(normalize_label).astype(np.int8)
y_test = test_df[LABEL].map(normalize_label).astype(np.int8)

print("\nTraining target:")
print(y_train.value_counts().sort_index())

print("\nTesting target:")
print(y_test.value_counts().sort_index())

# ------------------------------------------------------------
# FEATURES
# ------------------------------------------------------------

feature_cols = [
    c for c in train_df.columns
    if c not in DROP_COLS
    and c in test_df.columns
]

X_train = train_df[feature_cols].copy()
X_test = test_df[feature_cols].copy()

# Convert object columns to strings
cat_features = []

for i, col in enumerate(feature_cols):
    if X_train[col].dtype == "object":
        X_train[col] = X_train[col].fillna("missing").astype(str)
        X_test[col] = X_test[col].fillna("missing").astype(str)
        cat_features.append(i)
    else:
        X_train[col] = pd.to_numeric(X_train[col], errors="coerce")
        X_test[col] = pd.to_numeric(X_test[col], errors="coerce")

# Replace infinities
X_train.replace([np.inf, -np.inf], np.nan, inplace=True)
X_test.replace([np.inf, -np.inf], np.nan, inplace=True)

# CatBoost can handle numeric NaNs.
print("\nFeature count:", len(feature_cols))
print("Categorical:", [feature_cols[i] for i in cat_features])

# ------------------------------------------------------------
# GPU TRAINING
# ------------------------------------------------------------

print("\n[3] Initializing CatBoost GPU...")

model = CatBoostClassifier(
    iterations=1000,
    depth=8,
    learning_rate=0.05,
    loss_function="Logloss",
    eval_metric="AUC",
    random_seed=42,
    task_type="GPU",
    devices="0",
    verbose=100,
    allow_writing_files=False,
)

start = time.time()

print("\n[4] Training...")

model.fit(
    X_train,
    y_train,
    cat_features=cat_features,
    eval_set=(X_test, y_test),
    early_stopping_rounds=80,
    verbose=100,
)

elapsed = time.time() - start

# ------------------------------------------------------------
# EVALUATION
# ------------------------------------------------------------

print("\n" + "=" * 72)
print("CIC-IDS2017 TEST EVALUATION")
print("=" * 72)

pred = model.predict(X_test).astype(int).ravel()
prob = model.predict_proba(X_test)[:, 1]

accuracy = accuracy_score(y_test, pred)
precision = precision_score(y_test, pred, zero_division=0)
recall = recall_score(y_test, pred, zero_division=0)
f1 = f1_score(y_test, pred, zero_division=0)
roc_auc = roc_auc_score(y_test, prob)
pr_auc = average_precision_score(y_test, prob)

cm = confusion_matrix(y_test, pred)

tn, fp, fn, tp = cm.ravel()

fpr = fp / (fp + tn) if (fp + tn) else 0
fnr = fn / (fn + tp) if (fn + tp) else 0

print(f"Accuracy       : {accuracy:.4%}")
print(f"Precision      : {precision:.4%}")
print(f"Recall         : {recall:.4%}")
print(f"F1             : {f1:.4%}")
print(f"ROC-AUC        : {roc_auc:.4%}")
print(f"PR-AUC         : {pr_auc:.4%}")
print(f"FPR            : {fpr:.4%}")
print(f"FNR            : {fnr:.4%}")

print("\nConfusion Matrix:")
print(cm)

print("\nClassification Report:")
print(
    classification_report(
        y_test,
        pred,
        target_names=["Benign", "Attack"],
        digits=4,
        zero_division=0,
    )
)

print("\nTraining time:", f"{elapsed:.2f} seconds")
print("Best iteration:", model.get_best_iteration())

# ------------------------------------------------------------
# FEATURE IMPORTANCE
# ------------------------------------------------------------

importance = model.get_feature_importance()

importance_df = (
    pd.DataFrame({
        "feature": feature_cols,
        "importance": importance,
    })
    .sort_values("importance", ascending=False)
)

print("\n" + "=" * 72)
print("TOP 25 FEATURES")
print("=" * 72)
print(importance_df.head(25).to_string(index=False))

# ------------------------------------------------------------
# ARTIFACT
# ------------------------------------------------------------

ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

model.save_model(str(ARTIFACT_DIR / "model.cbm"))

metadata = {
    "model": "network-anomaly-cicids2017",
    "version": "v1",
    "dataset": "CIC-IDS2017",
    "task": "binary_intrusion_detection",
    "train_files": TRAIN_FILES,
    "test_files": TEST_FILES,
    "train_rows": int(len(train_df)),
    "test_rows": int(len(test_df)),
    "features": feature_cols,
    "categorical_features": [feature_cols[i] for i in cat_features],
    "metrics": {
        "accuracy": float(accuracy),
        "precision": float(precision),
        "recall": float(recall),
        "f1": float(f1),
        "roc_auc": float(roc_auc),
        "pr_auc": float(pr_auc),
        "fpr": float(fpr),
        "fnr": float(fnr),
    },
    "confusion_matrix": cm.tolist(),
    "best_iteration": int(model.get_best_iteration()),
    "random_seed": 42,
    "training_time_seconds": elapsed,
}

with open(ARTIFACT_DIR / "metadata.json", "w") as f:
    json.dump(metadata, f, indent=2)

with open(ARTIFACT_DIR / "feature_schema.json", "w") as f:
    json.dump({
        "feature_names": feature_cols,
        "categorical_features": [feature_cols[i] for i in cat_features],
        "target": LABEL,
    }, f, indent=2)

with open(ARTIFACT_DIR / "label_mapping.json", "w") as f:
    json.dump({
        "0": "Benign",
        "1": "Attack",
    }, f, indent=2)

with open(ARTIFACT_DIR / "metrics.json", "w") as f:
    json.dump(metadata["metrics"], f, indent=2)

print("\n" + "=" * 72)
print("TRAINING COMPLETE")
print("=" * 72)
print("Artifact:", ARTIFACT_DIR)

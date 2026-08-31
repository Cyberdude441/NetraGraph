
import sys
import numpy as np
import pandas as pd

from sklearn.metrics import (
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix
)

from catboost import CatBoostClassifier

MODEL_PATH = "/content/NetraGraph/artifacts/network-anomaly-cicids2017/v1/model.cbm"

DATASET_DIR = "/kaggle/input/cicids2017"

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

print("=" * 72)
print("NETRAGRAPH — CIC-IDS2017 THRESHOLD ANALYSIS")
print("=" * 72)

frames = []

for filename in TEST_FILES:
    path = f"{DATASET_DIR}/{filename}"

    print(f"Loading: {filename}")

    df = pd.read_parquet(path)
    df.columns = [str(c).strip() for c in df.columns]

    frames.append(df)

test_df = pd.concat(frames, ignore_index=True)

print("\nTest rows:", f"{len(test_df):,}")

# Labels
y_test = (
    test_df[LABEL]
    .astype(str)
    .str.strip()
    .str.lower()
    .ne("benign")
    .astype(np.int8)
)

# Features must match training
feature_cols = [
    c for c in test_df.columns
    if c not in DROP_COLS
]

X_test = test_df[feature_cols].copy()

# Clean numeric values
for col in X_test.columns:
    if X_test[col].dtype != "object":
        X_test[col] = pd.to_numeric(
            X_test[col],
            errors="coerce"
        )

X_test.replace(
    [np.inf, -np.inf],
    np.nan,
    inplace=True
)

print("Features:", len(feature_cols))

# Load model
print("\nLoading trained CatBoost model...")

model = CatBoostClassifier()

model.load_model(MODEL_PATH)

print("Model loaded successfully.")

# Probabilities
print("\nGenerating attack probabilities...")

prob = model.predict_proba(X_test)[:, 1]

results = []

for threshold in np.arange(0.05, 0.96, 0.05):

    pred = (prob >= threshold).astype(np.int8)

    tn, fp, fn, tp = confusion_matrix(
        y_test,
        pred,
        labels=[0, 1]
    ).ravel()

    precision = precision_score(
        y_test,
        pred,
        zero_division=0
    )

    recall = recall_score(
        y_test,
        pred,
        zero_division=0
    )

    f1 = f1_score(
        y_test,
        pred,
        zero_division=0
    )

    fpr = fp / (fp + tn)
    fnr = fn / (fn + tp)

    results.append({
        "threshold": round(float(threshold), 2),
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "fpr": fpr,
        "fnr": fnr,
        "TP": tp,
        "FP": fp,
        "FN": fn,
        "TN": tn
    })

results_df = pd.DataFrame(results)

print("\n" + "=" * 72)
print("THRESHOLD RESULTS")
print("=" * 72)

print(
    results_df.to_string(
        index=False,
        formatters={
            "precision": "{:.4f}".format,
            "recall": "{:.4f}".format,
            "f1": "{:.4f}".format,
            "fpr": "{:.4%}".format,
            "fnr": "{:.4%}".format,
        }
    )
)

best = results_df.loc[
    results_df["f1"].idxmax()
]

print("\n" + "=" * 72)
print("BEST F1 THRESHOLD")
print("=" * 72)

print(best.to_string())

# Best threshold subject to FPR <= 1%
acceptable = results_df[
    results_df["fpr"] <= 0.01
]

if len(acceptable):

    best_low_fpr = acceptable.loc[
        acceptable["f1"].idxmax()
    ]

    print("\n" + "=" * 72)
    print("BEST F1 WITH FPR <= 1%")
    print("=" * 72)

    print(best_low_fpr.to_string())

print("\nAnalysis complete.")

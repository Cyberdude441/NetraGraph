
import argparse
import os
import json
import time
import gc

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
)

DROP_COLS = {
    "Flow ID",
    "Src IP",
    "Dst IP",
    "Src Port",
    "Dst Port",
    "Timestamp",
}

def normalize_label(x):
    return 0 if str(x).strip().lower() == "benign" else 1


def discover_files(data_dir):
    files = [
        os.path.join(data_dir, f)
        for f in os.listdir(data_dir)
        if f.lower().endswith(".csv")
    ]
    return sorted(files)


def clean_chunk(df):
    # Normalize column names
    df.columns = [str(c).strip() for c in df.columns]

    # ------------------------------------------------------------
    # Find target BEFORE dropping any columns
    # ------------------------------------------------------------
    label_col = next(
        (
            c for c in df.columns
            if str(c).strip().lower() == "label"
        ),
        None
    )

    if label_col is None:
        raise ValueError(
            f"Label column not found. Columns: {list(df.columns)}"
        )

    # ------------------------------------------------------------
    # Extract target
    # ------------------------------------------------------------
    y = df[label_col].map(normalize_label).astype(np.int8)

    # ------------------------------------------------------------
    # Remove target + identifiers/leakage columns
    # ------------------------------------------------------------
    leakage_cols = {
        "Flow ID",
        "Src IP",
        "Dst IP",
        "Src Port",
        "Timestamp",
    }

    drop_cols = [
        c for c in df.columns
        if c == label_col or c in leakage_cols
    ]

    X = df.drop(
        columns=drop_cols,
        errors="ignore"
    )

    # ------------------------------------------------------------
    # Numeric sanitization
    # ------------------------------------------------------------
    for col in X.columns:
        if X[col].dtype == "object":
            X[col] = X[col].fillna("missing").astype(str)
        else:
            X[col] = pd.to_numeric(
                X[col],
                errors="coerce"
            )

    X.replace(
        [np.inf, -np.inf],
        np.nan,
        inplace=True
    )

    return X, y


def main():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--data-dir",
        required=True
    )

    parser.add_argument(
        "--device",
        default="gpu",
        choices=["gpu", "cpu"]
    )

    parser.add_argument(
        "--chunksize",
        type=int,
        default=50000
    )

    parser.add_argument(
        "--max-rows-per-file",
        type=int,
        default=150000
    )

    args = parser.parse_args()

    print("=" * 72)
    print("NETRAGRAPH — CIC-IDS2018 MEMORY-SAFE GPU TRAINING")
    print("=" * 72)

    files = discover_files(args.data_dir)

    print("\nFiles discovered:", len(files))

    for f in files:
        print(" -", os.path.basename(f))

    # ------------------------------------------------------------
    # Build a representative dataset without loading everything
    # ------------------------------------------------------------

    train_parts = []
    test_parts = []

    print("\n[1] Reading data in chunks...")

    for i, file in enumerate(files):

        name = os.path.basename(file)

        print("\nProcessing:", name)

        used = 0

        for chunk in pd.read_csv(
            file,
            chunksize=args.chunksize,
            low_memory=False
        ):

            remaining = args.max_rows_per_file - used

            if remaining <= 0:
                break

            if len(chunk) > remaining:
                chunk = chunk.iloc[:remaining]

            X, y = clean_chunk(chunk)

            # 80/20 split WITHIN EACH FILE
            n = len(X)
            split = int(n * 0.8)

            train_parts.append(
                (X.iloc[:split].copy(), y.iloc[:split].copy())
            )

            test_parts.append(
                (X.iloc[split:].copy(), y.iloc[split:].copy())
            )

            used += n

            del chunk, X, y
            gc.collect()

        print("Rows used:", used)

    print("\nCombining controlled samples...")

    X_train = pd.concat(
        [x for x, y in train_parts],
        ignore_index=True
    )

    y_train = pd.concat(
        [y for x, y in train_parts],
        ignore_index=True
    )

    X_test = pd.concat(
        [x for x, y in test_parts],
        ignore_index=True
    )

    y_test = pd.concat(
        [y for x, y in test_parts],
        ignore_index=True
    )

    del train_parts, test_parts
    gc.collect()

    print("\nTraining rows:", f"{len(X_train):,}")
    print("Testing rows :", f"{len(X_test):,}")

    print("\nTraining distribution:")
    print(y_train.value_counts().to_dict())

    print("\nTesting distribution:")
    print(y_test.value_counts().to_dict())

    # ------------------------------------------------------------
    # Feature typing
    # ------------------------------------------------------------
    # CIC-IDS2018 contains numeric network-flow features.
    # Timestamp was removed during clean_chunk().
    # Label was removed as the target.
    # Therefore CatBoost receives all remaining features as numeric.

    cat_features = []

    for col in X_train.columns:
        X_train[col] = pd.to_numeric(
            X_train[col],
            errors="coerce"
        )
        X_test[col] = pd.to_numeric(
            X_test[col],
            errors="coerce"
        )

    # Replace infinite values
    X_train.replace(
        [np.inf, -np.inf],
        np.nan,
        inplace=True
    )

    X_test.replace(
        [np.inf, -np.inf],
        np.nan,
        inplace=True
    )

    # Median imputation using TRAINING statistics only
    train_medians = X_train.median()

    X_train = X_train.fillna(train_medians)
    X_test = X_test.fillna(train_medians)

    print("\nFeatures:", len(X_train.columns))
    print("Categorical: []")
    print("Numeric features:", len(X_train.columns))
    print("Remaining NaN - train:", int(X_train.isna().sum().sum()))
    print("Remaining NaN - test :", int(X_test.isna().sum().sum()))

    # ------------------------------------------------------------
    # Train
    # ------------------------------------------------------------

    print("\n[2] Starting CatBoost...")

    task_type = "GPU" if args.device == "gpu" else "CPU"

    model = CatBoostClassifier(
        iterations=500,
        depth=8,
        learning_rate=0.05,
        loss_function="Logloss",
        eval_metric="AUC",
        random_seed=42,
        task_type=task_type,
        devices="0" if task_type == "GPU" else None,
        verbose=50,
        allow_writing_files=False,
    )

    start = time.time()

    model.fit(
        X_train,
        y_train,
        cat_features=cat_features,
        eval_set=(X_test, y_test),
        early_stopping_rounds=50,
    )

    elapsed = time.time() - start

    # ------------------------------------------------------------
    # Evaluation
    # ------------------------------------------------------------

    print("\n" + "=" * 72)
    print("CIC-IDS2018 EVALUATION")
    print("=" * 72)

    prob = model.predict_proba(X_test)[:, 1]

    # Default threshold
    pred = (prob >= 0.50).astype(np.int8)

    accuracy = accuracy_score(y_test, pred)
    precision = precision_score(y_test, pred, zero_division=0)
    recall = recall_score(y_test, pred, zero_division=0)
    f1 = f1_score(y_test, pred, zero_division=0)

    roc = roc_auc_score(y_test, prob)
    pr = average_precision_score(y_test, prob)

    tn, fp, fn, tp = confusion_matrix(
        y_test,
        pred,
        labels=[0, 1]
    ).ravel()

    fpr = fp / (fp + tn)
    fnr = fn / (fn + tp)

    print(f"Accuracy  : {accuracy:.4%}")
    print(f"Precision : {precision:.4%}")
    print(f"Recall    : {recall:.4%}")
    print(f"F1        : {f1:.4%}")
    print(f"ROC-AUC   : {roc:.4%}")
    print(f"PR-AUC    : {pr:.4%}")
    print(f"FPR       : {fpr:.4%}")
    print(f"FNR       : {fnr:.4%}")

    print("\nConfusion Matrix:")
    print(
        f"TN={tn:,} | FP={fp:,}\n"
        f"FN={fn:,} | TP={tp:,}"
    )

    print("\nTraining time:", f"{elapsed:.2f} seconds")

    # ------------------------------------------------------------
    # Save artifact
    # ------------------------------------------------------------

    artifact = (
        "/content/NetraGraph/"
        "artifacts/network-anomaly-cicids2018/v1"
    )

    os.makedirs(artifact, exist_ok=True)

    model.save_model(
        os.path.join(artifact, "model.cbm")
    )

    with open(
        os.path.join(artifact, "feature_schema.json"),
        "w"
    ) as f:

        json.dump(
            {
                "feature_names": list(X_train.columns),
                "categorical_features": [
                    X_train.columns[i]
                    for i in cat_features
                ],
                "target": "Label",
            },
            f,
            indent=2
        )

    with open(
        os.path.join(artifact, "label_mapping.json"),
        "w"
    ) as f:

        json.dump(
            {
                "0": "Benign",
                "1": "Attack",
            },
            f,
            indent=2
        )

    with open(
        os.path.join(artifact, "metrics.json"),
        "w"
    ) as f:

        json.dump(
            {
                "accuracy": accuracy,
                "precision": precision,
                "recall": recall,
                "f1": f1,
                "roc_auc": roc,
                "pr_auc": pr,
                "fpr": fpr,
                "fnr": fnr,
                "tn": int(tn),
                "fp": int(fp),
                "fn": int(fn),
                "tp": int(tp),
            },
            f,
            indent=2
        )

    print("\n" + "=" * 72)
    print("TRAINING COMPLETE")
    print("=" * 72)
    print("Artifact:", artifact)


if __name__ == "__main__":
    main()

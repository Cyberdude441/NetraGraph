
import os
import gc
import json
import time
import random
import argparse

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

SEED = 42
random.seed(SEED)
np.random.seed(SEED)

DROP_COLS = [
    "Unnamed: 0",
    "Flow ID",
    "Source IP",
    "Destination IP",
    "Timestamp",
]

LABEL = "Label"


def normalize_columns(df):
    df.columns = [str(c).strip() for c in df.columns]
    return df


def clean_chunk(df):
    df = normalize_columns(df)

    if LABEL not in df.columns:
        raise ValueError(
            f"Label column not found. Columns: {list(df.columns)}"
        )

    y_raw = (
        df[LABEL]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    # Binary target
    y = (y_raw != "BENIGN").astype(np.int8)

    # Remove target and identifiers
    drop = [
        c for c in DROP_COLS + [LABEL]
        if c in df.columns
    ]

    X = df.drop(columns=drop, errors="ignore").copy()

    # Force all remaining features to numeric
    for c in X.columns:
        X[c] = pd.to_numeric(X[c], errors="coerce")

    # Replace invalid numeric values
    X.replace(
        [np.inf, -np.inf],
        np.nan,
        inplace=True
    )

    return X, y


def sample_file(
    path,
    benign_target,
    attack_target,
    chunk_size=50000
):
    benign_parts = []
    attack_parts = []

    benign_seen = 0
    attack_seen = 0

    print(f"\n[Loader] {os.path.basename(path)}")

    for chunk in pd.read_csv(
        path,
        chunksize=chunk_size,
        low_memory=False
    ):
        X, y = clean_chunk(chunk)

        benign_mask = y == 0
        attack_mask = y == 1

        b = X.loc[benign_mask]
        a = X.loc[attack_mask]

        if len(b) > 0:
            remaining = benign_target - benign_seen

            if remaining > 0:
                take = min(len(b), remaining)

                if len(b) > take:
                    b = b.sample(
                        n=take,
                        random_state=SEED
                    )

                benign_parts.append(b)
                benign_seen += len(b)

        if len(a) > 0:
            remaining = attack_target - attack_seen

            if remaining > 0:
                take = min(len(a), remaining)

                if len(a) > take:
                    a = a.sample(
                        n=take,
                        random_state=SEED
                    )

                attack_parts.append(a)
                attack_seen += len(a)

        del chunk, X, y, b, a
        gc.collect()

        if (
            benign_seen >= benign_target
            and attack_seen >= attack_target
        ):
            break

    print(
        f"  collected benign={benign_seen:,}, "
        f"attack={attack_seen:,}"
    )

    return benign_parts, attack_parts


def collect_dataset(
    files,
    total_benign,
    total_attack,
    chunk_size
):
    # Collect approximately equal contribution from files.
    per_file_b = max(
        1,
        total_benign // len(files)
    )

    per_file_a = max(
        1,
        total_attack // len(files)
    )

    benign_parts = []
    attack_parts = []

    for path in files:
        b, a = sample_file(
            path,
            per_file_b,
            per_file_a,
            chunk_size
        )

        benign_parts.extend(b)
        attack_parts.extend(a)

        del b, a
        gc.collect()

    benign = pd.concat(
        benign_parts,
        ignore_index=True
    )

    attack = pd.concat(
        attack_parts,
        ignore_index=True
    )

    # Correct to requested totals
    if len(benign) > total_benign:
        benign = benign.sample(
            n=total_benign,
            random_state=SEED
        )

    if len(attack) > total_attack:
        attack = attack.sample(
            n=total_attack,
            random_state=SEED
        )

    benign["__target__"] = 0
    attack["__target__"] = 1

    data = pd.concat(
        [benign, attack],
        ignore_index=True
    )

    data = data.sample(
        frac=1,
        random_state=SEED
    ).reset_index(drop=True)

    del benign_parts, attack_parts, benign, attack
    gc.collect()

    return data


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--data-dir",
        required=True
    )

    parser.add_argument(
        "--device",
        default="gpu"
    )

    parser.add_argument(
        "--benign",
        type=int,
        default=500000
    )

    parser.add_argument(
        "--attack",
        type=int,
        default=500000
    )

    parser.add_argument(
        "--chunk-size",
        type=int,
        default=50000
    )

    parser.add_argument(
        "--iterations",
        type=int,
        default=500
    )

    args = parser.parse_args()

    print("=" * 72)
    print("NETRAGRAPH — CIC-DDoS2019 BINARY GPU TRAINING")
    print("=" * 72)

    files = []

    for root, dirs, names in os.walk(args.data_dir):
        for name in names:
            if name.lower().endswith(".csv"):
                files.append(
                    os.path.join(root, name)
                )

    files.sort()

    print(f"\nFiles discovered: {len(files)}")

    for f in files:
        print(" -", os.path.relpath(f, args.data_dir))

    # ---------------------------------------------------------
    # Collect balanced dataset
    # ---------------------------------------------------------

    print("\n[1] Building controlled dataset...")
    print(
        f"Target: {args.benign:,} BENIGN + "
        f"{args.attack:,} ATTACK"
    )

    data = collect_dataset(
        files,
        args.benign,
        args.attack,
        args.chunk_size
    )

    print("\nFinal dataset:", data.shape)

    print(
        "Distribution:",
        data["__target__"].value_counts().to_dict()
    )

    # ---------------------------------------------------------
    # Remove rows with invalid targets/features
    # ---------------------------------------------------------

    data = data.dropna(
        subset=["__target__"]
    )

    X = data.drop(
        columns=["__target__"]
    )

    y = data["__target__"].astype(np.int8)

    # Median imputation using complete training data.
    # This is acceptable for the controlled benchmark.
    medians = X.median()

    X = X.fillna(medians)

    # ---------------------------------------------------------
    # Train/test split
    # ---------------------------------------------------------

    from sklearn.model_selection import train_test_split

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.20,
        random_state=SEED,
        stratify=y
    )

    print("\nTraining:", X_train.shape)
    print("Testing :", X_test.shape)

    print("\nFeatures:", len(X_train.columns))
    print("Categorical: []")

    # ---------------------------------------------------------
    # CatBoost
    # ---------------------------------------------------------

    print("\n[2] Starting CatBoost...")

    task_type = "GPU" if args.device.lower() == "gpu" else "CPU"

    model = CatBoostClassifier(
        iterations=args.iterations,
        depth=8,
        learning_rate=0.08,
        loss_function="Logloss",
        eval_metric="AUC",
        task_type=task_type,
        random_seed=SEED,
        verbose=50,
        allow_writing_files=False,
        thread_count=-1,
        l2_leaf_reg=5,
        random_strength=1,
        auto_class_weights=None,
        od_type="Iter",
        od_wait=50,
    )

    start = time.time()

    model.fit(
        X_train,
        y_train,
        eval_set=(X_test, y_test),
        use_best_model=True
    )

    elapsed = time.time() - start

    print("\nTraining time:", round(elapsed, 2), "seconds")

    # ---------------------------------------------------------
    # Evaluation
    # ---------------------------------------------------------

    print("\n" + "=" * 72)
    print("CIC-DDoS2019 EVALUATION")
    print("=" * 72)

    probabilities = model.predict_proba(X_test)[:, 1]
    predictions = (probabilities >= 0.5).astype(np.int8)

    accuracy = accuracy_score(y_test, predictions)
    precision = precision_score(
        y_test,
        predictions,
        zero_division=0
    )
    recall = recall_score(
        y_test,
        predictions,
        zero_division=0
    )
    f1 = f1_score(
        y_test,
        predictions,
        zero_division=0
    )

    roc = roc_auc_score(
        y_test,
        probabilities
    )

    pr = average_precision_score(
        y_test,
        probabilities
    )

    tn, fp, fn, tp = confusion_matrix(
        y_test,
        predictions
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

    print("\nClassification Report:")
    print(
        classification_report(
            y_test,
            predictions,
            target_names=["BENIGN", "ATTACK"],
            digits=4,
            zero_division=0
        )
    )

    # ---------------------------------------------------------
    # Feature importance
    # ---------------------------------------------------------

    importance = pd.DataFrame({
        "feature": X_train.columns,
        "importance": model.get_feature_importance()
    }).sort_values(
        "importance",
        ascending=False
    )

    print("\nTOP 25 FEATURES")
    print("=" * 72)
    print(
        importance.head(25).to_string(
            index=False
        )
    )

    # ---------------------------------------------------------
    # Save artifact
    # ---------------------------------------------------------

    artifact = (
        "/content/NetraGraph/artifacts/"
        "network-anomaly-cicddos2019/v1"
    )

    os.makedirs(
        artifact,
        exist_ok=True
    )

    model.save_model(
        os.path.join(
            artifact,
            "model.cbm"
        )
    )

    metrics = {
        "dataset": "CIC-DDoS2019",
        "task": "binary",
        "training_rows": int(len(X_train)),
        "testing_rows": int(len(X_test)),
        "features": int(X_train.shape[1]),
        "accuracy": float(accuracy),
        "precision": float(precision),
        "recall": float(recall),
        "f1": float(f1),
        "roc_auc": float(roc),
        "pr_auc": float(pr),
        "fpr": float(fpr),
        "fnr": float(fnr),
        "tn": int(tn),
        "fp": int(fp),
        "fn": int(fn),
        "tp": int(tp),
        "training_seconds": float(elapsed),
    }

    with open(
        os.path.join(
            artifact,
            "metrics.json"
        ),
        "w"
    ) as f:
        json.dump(
            metrics,
            f,
            indent=2
        )

    with open(
        os.path.join(
            artifact,
            "feature_schema.json"
        ),
        "w"
    ) as f:
        json.dump(
            {
                "features": list(X_train.columns),
                "categorical_features": [],
                "dropped_columns": DROP_COLS + [LABEL],
            },
            f,
            indent=2
        )

    with open(
        os.path.join(
            artifact,
            "label_mapping.json"
        ),
        "w"
    ) as f:
        json.dump(
            {
                "0": "BENIGN",
                "1": "ATTACK"
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

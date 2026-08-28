"""Portable tabular trainer. Run with: python -m ml.training.train_all --data ..."""
from __future__ import annotations

import argparse
import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

from ml.config.environment import output_root
from ml.config.version import ensure_supported_ml_runtime
from ml.data.dataset_discovery import discover_files, fingerprint, read_records
from ml.data.feature_engineering import records_to_frame
from ml.data.preprocessing import build_preprocessor
from ml.data.schema_detection import schema_report
from ml.evaluation.evaluate_models import evaluate


def train(data_path: str | Path, model_name: str, target: str | None = None, version: str = "v1", output: str | Path | None = None) -> Path:
    ensure_supported_ml_runtime()
    data_path = Path(data_path)
    files = discover_files(data_path if data_path.is_dir() else data_path.parent)
    files = [file for file in files if file == data_path or data_path.is_dir()]
    records = [record for file in files for record in read_records(file)]
    report = schema_report(records, target)
    target_column = report["target_column"]
    frame, feature_names = records_to_frame(records, target_column)
    X, y = frame[feature_names], frame[target_column]

    from sklearn.ensemble import RandomForestClassifier
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import LabelEncoder
    import joblib

    label_encoder = LabelEncoder()
    encoded_y = label_encoder.fit_transform(y.astype(str))
    if len(set(encoded_y)) < 2:
        raise ValueError("Training requires at least two target classes")
    X_train, X_test, y_train, y_test = train_test_split(X, encoded_y, test_size=0.2, random_state=42, stratify=encoded_y)
    preprocessor = build_preprocessor(X_train, feature_names)
    X_train_transformed = preprocessor.fit_transform(X_train)
    X_test_transformed = preprocessor.transform(X_test)
    model = RandomForestClassifier(n_estimators=200, random_state=42, class_weight="balanced")
    model.fit(X_train_transformed, y_train)
    metrics = evaluate(model, X_test_transformed, y_test)

    destination = Path(output or output_root()) / model_name / version
    destination.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, destination / "model.joblib")
    joblib.dump(preprocessor, destination / "preprocessor.joblib")
    (destination / "feature_schema.json").write_text(json.dumps({"feature_names": feature_names, "dtypes": {name: str(X[name].dtype) for name in feature_names}, "target_column": target_column}, indent=2), encoding="utf-8")
    (destination / "label_mapping.json").write_text(json.dumps({str(index): label for index, label in enumerate(label_encoder.classes_)}, indent=2), encoding="utf-8")
    (destination / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    metadata = {
        "model_name": model_name, "model_type": "RandomForestClassifier", "model_version": version,
        "training_timestamp": datetime.now(timezone.utc).isoformat(),
        "framework_versions": {"python": platform.python_version(), "scikit-learn": __import__("sklearn").__version__, "joblib": joblib.__version__},
        "python_version": platform.python_version(), "dataset_name": data_path.name,
        "dataset_fingerprint": fingerprint(files), "target_column": target_column,
        "feature_names": feature_names, "class_labels": label_encoder.classes_.tolist(), "training_metrics": metrics,
    }
    (destination / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    (destination / "requirements_model.txt").write_text("scikit-learn==" + __import__("sklearn").__version__ + "\njoblib==" + joblib.__version__ + "\n", encoding="utf-8")
    training_report = {"dataset_name": data_path.name, "number_of_files_discovered": len(files), "rows_processed": len(frame), "columns_used": feature_names, "target_column": target_column, "preprocessing_steps": ["median imputation and standard scaling for numeric features", "most-frequent imputation and one-hot encoding for categorical features"], "train_test_split": {"test_size": 0.2, "random_state": 42}, "class_distribution": report["class_distribution"], "models_compared": ["RandomForestClassifier"], "best_model": "RandomForestClassifier", **metrics, "model_version": version}
    (destination / "training_report.json").write_text(json.dumps(training_report, indent=2), encoding="utf-8")
    return destination


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", required=True)
    parser.add_argument("--model-name", required=True)
    parser.add_argument("--target")
    parser.add_argument("--version", default="v1")
    parser.add_argument("--output")
    args = parser.parse_args()
    print(train(args.data, args.model_name, args.target, args.version, args.output))


if __name__ == "__main__":
    main()

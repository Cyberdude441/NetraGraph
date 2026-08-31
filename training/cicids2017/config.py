from pathlib import Path

DATASET_DIR = Path("/kaggle/input/cicids2017")

LABEL_COL = "Label"

DROP_COLUMNS = [
    "Label",
]

CATEGORICAL_COLUMNS = [
    "Protocol",
]

RANDOM_STATE = 42

BINARY_LABELS = {
    "Benign": 0,
}

ARTIFACT_DIR = Path("/content/NetraGraph/artifacts/network-anomaly-cicids2017/v1")

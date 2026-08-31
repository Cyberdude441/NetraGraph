from pathlib import Path
import pandas as pd

DATASET_DIR = Path("/kaggle/input/cicids2017")

def discover():
    files = sorted(DATASET_DIR.glob("*.parquet"))

    print("=" * 70)
    print("CIC-IDS2017 DATASET DISCOVERY")
    print("=" * 70)

    for f in files:
        df = pd.read_parquet(f, columns=["Label"])

        print(f"\\n{f.name}")
        print("Rows:", len(df))
        print("Labels:")
        print(df["Label"].value_counts().to_dict())

    return files

if __name__ == "__main__":
    discover()

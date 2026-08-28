"""Small, deterministic feature preparation helpers shared by training and inference."""
from __future__ import annotations


def records_to_frame(records, target_column: str):
    import pandas as pd
    frame = pd.DataFrame(records)
    if target_column not in frame:
        raise ValueError(f"Target column not found: {target_column}")
    feature_names = [column for column in frame.columns if column != target_column]
    return frame, feature_names

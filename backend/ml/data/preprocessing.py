"""Build the exact persisted tabular preprocessing used by inference."""
from __future__ import annotations


def build_preprocessor(frame, feature_names):
    from sklearn.compose import ColumnTransformer
    from sklearn.impute import SimpleImputer
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import OneHotEncoder, StandardScaler
    numeric = [name for name in feature_names if frame[name].dtype.kind in "biufc"]
    categorical = [name for name in feature_names if name not in numeric]
    transformers = []
    if numeric:
        transformers.append(("numeric", Pipeline([("imputer", SimpleImputer(strategy="median")), ("scaler", StandardScaler())]), numeric))
    if categorical:
        transformers.append(("categorical", Pipeline([("imputer", SimpleImputer(strategy="most_frequent")), ("encoder", OneHotEncoder(handle_unknown="ignore"))]), categorical))
    if not transformers:
        raise ValueError("No usable feature columns found")
    return ColumnTransformer(transformers=transformers, remainder="drop")

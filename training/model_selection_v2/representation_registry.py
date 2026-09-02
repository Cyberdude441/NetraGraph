"""
Representation Registry for NetraGraph Model Selection V2.
Encapsulates domain-specialized, versioned preprocessing pipelines with leakage protections.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, RobustScaler, StandardScaler

try:
    from training.model_selection_v2.config import RepresentationType
except ImportError:
    from config import RepresentationType


class BaseRepresentation(ABC):
    """Abstract base class for all domain-aware representation transformers."""

    def __init__(self, repr_type: RepresentationType, version: str):
        self.repr_type = repr_type
        self.version = version
        self.is_fitted = False
        self.feature_names_out: List[str] = []

    @abstractmethod
    def fit(self, df: pd.DataFrame) -> BaseRepresentation:
        pass

    @abstractmethod
    def transform(self, df: pd.DataFrame) -> np.ndarray:
        pass

    def fit_transform(self, df: pd.DataFrame) -> np.ndarray:
        return self.fit(df).transform(df)


class NetworkFlowV1Representation(BaseRepresentation):
    """
    NETWORK_FLOW_V1: Standardized numerical transformation for network flow intrusion and DDoS traffic.
    Cleans inf/nan, scales numerical vectors, and prunes potential identifier leakage.
    """

    DROPPED_LEAKAGE_COLS = {
        "flow_id", "source_ip", "destination_ip", "src_ip", "dst_ip",
        "timestamp", "date", "label", "signature", "attack",
    }

    def __init__(self):
        super().__init__(RepresentationType.NETWORK_FLOW_V1, version="1.0.0")
        self.scaler = RobustScaler()
        self.numeric_cols: List[str] = []

    def fit(self, df: pd.DataFrame) -> NetworkFlowV1Representation:
        valid_cols = [c for c in df.columns if str(c).lower().strip() not in self.DROPPED_LEAKAGE_COLS]
        num_df = df[valid_cols].select_dtypes(include=[np.number])
        self.numeric_cols = list(num_df.columns)
        if self.numeric_cols:
            clean_mat = np.nan_to_num(num_df.values, nan=0.0, posinf=1e6, neginf=-1e6)
            self.scaler.fit(clean_mat)
            self.feature_names_out = [f"flow_{c}" for c in self.numeric_cols]
        else:
            self.feature_names_out = ["flow_dummy"]
        self.is_fitted = True
        return self

    def transform(self, df: pd.DataFrame) -> np.ndarray:
        if not self.is_fitted:
            self.fit(df)
        if self.numeric_cols:
            # Handle missing columns gracefully
            sub_df = pd.DataFrame(index=df.index)
            for c in self.numeric_cols:
                sub_df[c] = df[c] if c in df.columns else 0.0
            clean_mat = np.nan_to_num(sub_df.values, nan=0.0, posinf=1e6, neginf=-1e6)
            return self.scaler.transform(clean_mat)
        return np.zeros((len(df), 1))


class MalwareMetadataV1Representation(BaseRepresentation):
    """
    MALWARE_METADATA_V1: Baseline representation with raw one-hot metadata encoding and timestamps.
    """

    CAT_COLS = ["reporter", "file_type_guess", "mime_type", "clamav"]
    NUM_COLS = ["vtpercent", "year", "month", "day", "hour", "dayofweek"]

    def __init__(self):
        super().__init__(RepresentationType.MALWARE_METADATA_V1, version="1.0.0")
        self.transformer: Optional[ColumnTransformer] = None

    def fit(self, df: pd.DataFrame) -> MalwareMetadataV1Representation:
        present_cat = [c for c in self.CAT_COLS if c in df.columns]
        present_num = [c for c in self.NUM_COLS if c in df.columns]
        transformers = []
        if present_cat:
            transformers.append(("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), present_cat))
        if present_num:
            transformers.append(("num", StandardScaler(), present_num))

        if transformers:
            self.transformer = ColumnTransformer(transformers=transformers)
            self.transformer.fit(df)
        self.is_fitted = True
        return self

    def transform(self, df: pd.DataFrame) -> np.ndarray:
        if not self.is_fitted:
            self.fit(df)
        if self.transformer:
            return self.transformer.transform(df)
        return np.zeros((len(df), 1))


class MalwareStructuralV2Representation(BaseRepresentation):
    """
    MALWARE_STRUCTURAL_V2: Research-grade structural representation for malware family classification.
    Incorporates:
    - Executable structural grouping (PE, Script, Archive, Document)
    - VirusTotal detection risk tiers (Low <=30%, Mid 30-70%, High >=70%)
    - SSDeep blocksize & double-chunk counts
    - Imphash frequency encoding (captures reusable API import structures)
    - TLSH distance prefix header
    - Deliberately drops non-generalizing temporal and reporter artifacts.
    """

    def __init__(self):
        super().__init__(RepresentationType.MALWARE_STRUCTURAL_V2, version="2.0.0")
        self.imphash_frequencies: Dict[str, int] = {}
        self.scaler = StandardScaler()

    def _engineer_features(self, df: pd.DataFrame) -> pd.DataFrame:
        feat_df = pd.DataFrame(index=df.index)

        # 1. Executable Grouping
        ftype = df["file_type_guess"].astype(str).str.lower() if "file_type_guess" in df.columns else pd.Series("unknown", index=df.index)
        feat_df["is_pe_executable"] = ftype.isin(["exe", "dll"]).astype(float)
        feat_df["is_script"] = ftype.isin(["vbs", "jar", "elf", "ps1", "sh"]).astype(float)
        feat_df["is_archive"] = ftype.isin(["zip", "iso", "rar", "7z", "tar"]).astype(float)
        feat_df["is_document"] = ftype.isin(["doc", "docx", "pdf", "xls", "rtf"]).astype(float)

        # 2. VirusTotal Risk Buckets
        vt = pd.to_numeric(df["vtpercent"], errors="coerce").fillna(50.0) if "vtpercent" in df.columns else pd.Series(50.0, index=df.index)
        feat_df["vt_tier_high"] = (vt >= 70.0).astype(float)
        feat_df["vt_tier_mid"] = ((vt >= 30.0) & (vt < 70.0)).astype(float)
        feat_df["vt_tier_low"] = (vt < 30.0).astype(float)
        feat_df["vtpercent_norm"] = (vt / 100.0).clip(0.0, 1.0)

        # 3. Imphash Frequency Encoding
        if "imphash" in df.columns:
            feat_df["imphash_freq"] = df["imphash"].map(self.imphash_frequencies).fillna(1.0).astype(float)
        else:
            feat_df["imphash_freq"] = 1.0

        # 4. SSDeep Structural Properties
        if "ssdeep" in df.columns:
            feat_df["ssdeep_blocksize"] = df["ssdeep"].apply(lambda s: float(str(s).split(":")[0]) if ":" in str(s) and str(s).split(":")[0].isdigit() else 0.0)
            feat_df["ssdeep_hash_len"] = df["ssdeep"].apply(lambda s: float(len(str(s).split(":")[1])) if ":" in str(s) and len(str(s).split(":")) > 1 else 0.0)
            feat_df["ssdeep_chunk_count"] = df["ssdeep"].apply(lambda s: float(len(str(s).split(":"))))
        else:
            feat_df["ssdeep_blocksize"] = 0.0
            feat_df["ssdeep_hash_len"] = 0.0
            feat_df["ssdeep_chunk_count"] = 0.0

        # 5. TLSH Structural Header
        if "tlsh" in df.columns:
            feat_df["tlsh_header"] = df["tlsh"].apply(lambda s: float(hash(str(s)[:4]) % 50))
        else:
            feat_df["tlsh_header"] = 0.0

        return feat_df

    def fit(self, df: pd.DataFrame) -> MalwareStructuralV2Representation:
        if "imphash" in df.columns:
            self.imphash_frequencies = df["imphash"].value_counts().to_dict()
        engineered = self._engineer_features(df)
        self.scaler.fit(engineered.values)
        self.feature_names_out = list(engineered.columns)
        self.is_fitted = True
        return self

    def transform(self, df: pd.DataFrame) -> np.ndarray:
        if len(df) == 0:
            return np.zeros((0, len(self.feature_names_out) or 13))
        if not self.is_fitted:
            self.fit(df)
        engineered = self._engineer_features(df)
        if hasattr(self.scaler, "mean_"):
            return self.scaler.transform(engineered.values)
        return engineered.values


class FallbackTabularV1Representation(BaseRepresentation):
    """
    FALLBACK_TABULAR_V1: Robust fallback representation for unknown/ambiguous input schemas.
    """

    def __init__(self):
        super().__init__(RepresentationType.FALLBACK_TABULAR_V1, version="1.0.0")
        self.scaler = StandardScaler()
        self.known_cols: List[str] = []

    def fit(self, df: pd.DataFrame) -> FallbackTabularV1Representation:
        num_df = df.select_dtypes(include=[np.number])
        self.known_cols = list(num_df.columns)
        if self.known_cols and len(df) > 0:
            clean_mat = np.nan_to_num(num_df.values, nan=0.0)
            self.scaler.fit(clean_mat)
            self.feature_names_out = self.known_cols
        else:
            self.feature_names_out = ["dummy_fallback"]
        self.is_fitted = True
        return self

    def transform(self, df: pd.DataFrame) -> np.ndarray:
        if len(df) == 0:
            return np.zeros((0, len(self.feature_names_out) or 1))
        if not self.is_fitted:
            self.fit(df)
        if self.known_cols and hasattr(self.scaler, "mean_"):
            sub_df = pd.DataFrame(index=df.index)
            for c in self.known_cols:
                sub_df[c] = df[c] if c in df.columns else 0.0
            clean_mat = np.nan_to_num(sub_df.values, nan=0.0)
            return self.scaler.transform(clean_mat)
        return np.zeros((len(df), 1))


class RepresentationRegistry:
    """Registry managing available representation pipelines."""

    def __init__(self):
        self._registry: Dict[RepresentationType, BaseRepresentation] = {
            RepresentationType.NETWORK_FLOW_V1: NetworkFlowV1Representation(),
            RepresentationType.MALWARE_METADATA_V1: MalwareMetadataV1Representation(),
            RepresentationType.MALWARE_STRUCTURAL_V2: MalwareStructuralV2Representation(),
            RepresentationType.FALLBACK_TABULAR_V1: FallbackTabularV1Representation(),
        }

    def get_representation(self, repr_type: RepresentationType) -> BaseRepresentation:
        if repr_type not in self._registry:
            return self._registry[RepresentationType.FALLBACK_TABULAR_V1]
        return self._registry[repr_type]

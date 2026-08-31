# CSE-CIC-IDS2018 Dedicated GPU Training & Research Pipeline

This directory contains a dedicated, reproducible, GPU-accelerated training pipeline for the **CSE-CIC-IDS2018 Dataset** (mounted at `/kaggle/input/ids-intrusion-csv` or `/content/cicids2018`).

---

## 🔒 Key Pipeline Architecture & Guardrails

1. **Automated Schema Harmonization (80 vs 84 Columns)**:
   - Most CSE-CIC-IDS2018 CSV files have 80 flow statistics.
   - `02-20-2018.csv` (and `02-21-2018.csv`) contain 84 columns with flow header metadata (`Flow ID`, `Src IP`, `Src Port`, `Dst IP`).
   - The pipeline automatically identifies and purges all identifier/leakage headers, stripping duplicate recurrent header rows and producing a uniform 78–79 feature matrix across all 10 daily CSV partitions.
2. **Infinite & Out-of-Range Float Sanitization**:
   - Replaces `Infinity` and `-Infinity` (frequent in `Flow Byts/s` and `Flow Pkts/s`) with `NaN`, and fits a median `SimpleImputer` + `StandardScaler`.
3. **Threshold Optimization & SOC Alert Noise Reduction**:
   - Sweeps decision thresholds ($\tau \in [0.01, 0.99]$) to find optimal F1 operating points and FPR-constrained thresholds (e.g. $FPR \le 0.1\%$).
4. **Complete Production Isolation**:
   - The resulting model artifact is packaged as `network-anomaly-cicids2018/v1`.
   - **Does not modify or activate** Models A–E.

---

## 🚀 Google Colab GPU Execution Guide

### Step 1: Open Google Colab with GPU Runtime
In Google Colab, select: **Runtime** -> **Change runtime type** -> **T4 GPU** (or V100/A100).

### Step 2: Clone Repository & Create Virtual Python ML Environment
```bash
!git clone https://github.com/Cyberdude441/NetraGraph.git /content/NetraGraph
%cd /content/NetraGraph

# Create dedicated Python ML environment if not already present
!python3 -m venv /content/netragraph-ml
!/content/netragraph-ml/bin/pip install -q -U pip
!/content/netragraph-ml/bin/pip install -q -r training/cicids2018/requirements.txt
```

### Step 3: Verify GPU & Hardware Acceleration
```bash
!/content/netragraph-ml/bin/python -c "
import sys; sys.path.insert(0, 'training/cicids2018')
from utils import detect_hardware, print_hardware_status
print_hardware_status(detect_hardware())
"
```

### Step 4: Run Data Preparation & Schema Audit
```bash
/content/netragraph-ml/bin/python training/cicids2018/prepare_data.py \
    --data-dir /content/cicids2018
```
*(On Kaggle, pass `--data-dir /kaggle/input/ids-intrusion-csv`).*

### Step 5: Train Binary Anomaly Detection Model (CatBoost GPU)
```bash
/content/netragraph-ml/bin/python training/cicids2018/train_binary.py \
    --data-dir /content/cicids2018 \
    --device gpu \
    --iterations 1200 \
    --depth 6 \
    --lr 0.05
```

### Step 6: Train Multi-Class Attack Taxonomy Model
```bash
/content/netragraph-ml/bin/python training/cicids2018/train_multiclass.py \
    --data-dir /content/cicids2018 \
    --device gpu \
    --iterations 1200
```

### Step 7: Evaluate Artifact & Threshold Forensics
```bash
/content/netragraph-ml/bin/python training/cicids2018/evaluate.py \
    --artifact artifacts/network-anomaly-cicids2018/v1
```

### Step 8: Run Cross-Dataset Model Validation
```bash
/content/netragraph-ml/bin/python training/cicids2018/cross_validate_models.py \
    --data-sample /content/cicids2018/02-14-2018.csv
```

---

## 📁 Artifact Export Contract

```text
artifacts/network-anomaly-cicids2018/v1/
├── model.joblib              # Trained CatBoost / Random Forest estimator
├── preprocessor.joblib       # Fitted ColumnTransformer (imputer + scaler + onehot)
├── feature_schema.json       # Feature names, dtypes, and task metadata
├── label_mapping.json        # {"0": "Benign", "1": "Attack"}
├── metrics.json              # Accuracy, F1, FPR, FNR, ROC-AUC, PR-AUC, Threshold Sweep
├── metadata.json             # Hardware provenance, training timestamp, framework versions
├── requirements_model.txt    # Pinned package requirements
└── training_report.json      # Forensic training report
```

---

## 🛠️ CLI Reference Summary

| Command | Description |
| :--- | :--- |
| `python training/cicids2018/prepare_data.py --data-dir <path>` | Ingests, aligns 80 vs 84 columns, sanitizes infinities, audits schema. |
| `python training/cicids2018/train_binary.py --data-dir <path> --device gpu` | Trains binary CatBoost GPU classifier and sweeps decision thresholds. |
| `python training/cicids2018/train_multiclass.py --data-dir <path> --device gpu` | Trains 15-class attack taxonomy classifier. |
| `python training/cicids2018/evaluate.py --artifact <path>` | Evaluates accuracy, FPR, FNR, and confusion matrix. |
| `python training/cicids2018/cross_validate_models.py --data-sample <path>` | Evaluates Model B transferability against CIC-IDS2018 flows. |

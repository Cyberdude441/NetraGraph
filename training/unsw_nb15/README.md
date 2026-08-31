# UNSW-NB15 Dedicated GPU Training & Research Environment

This directory contains a dedicated, reproducible, GPU-accelerated training pipeline for the **UNSW-NB15 Network Intrusion Dataset**. It is designed for Google Colab GPU instances (e.g., NVIDIA T4, V100, A100) or local CUDA workstations.

---

## 🔒 Key Design Principles & Guardrails

1. **Isolation from Production (Models A–E)**:
   - The resulting model artifact is exported under `network-anomaly-unsw/v1`.
   - It **does not overwrite** or modify production Model B (`network-intrusion/v1`).
   - It is not activated in production routing until explicitly promoted.
2. **Memory & RAM Safety**:
   - The official CSV files (`UNSW_NB15_training-set.csv` and `UNSW_NB15_testing-set.csv`) are preferred.
   - If a ZIP archive is provided, the pipeline audits and extracts **only the CSV files**, completely ignoring bulky raw PCAP packet dumps.
3. **Data Leakage Shield**:
   - Explicitly removes flow identifiers (`id`, `srcip`, `dstip`, `sport`, `dsport`) and secondary targets (`attack_cat`) from the binary training matrix.
   - Performs train/test hash overlap checks before fitting estimators.
4. **Cybersecurity-Centric Evaluation**:
   - Emphasizes **False Positive Rate (FPR)** (SOC alert fatigue) and **False Negative Rate (FNR)** (missed intrusions) in addition to Accuracy, F1, and ROC-AUC.

---

## 🚀 Google Colab Quickstart (Step-by-Step)

### Step 1: Open Google Colab & Select GPU Runtime
In Google Colab, go to: **Runtime** -> **Change runtime type** -> Select **T4 GPU** (or V100/A100).

### Step 2: Clone NetraGraph Repository
```bash
!git clone https://github.com/Cyberdude441/NetraGraph.git /content/NetraGraph
%cd /content/NetraGraph
```

### Step 3: Install Training Dependencies
```bash
!pip install -q -r training/unsw_nb15/requirements.txt
```

### Step 4: Verify GPU & CUDA Acceleration
```bash
python -c "
import sys; sys.path.insert(0, 'training/unsw_nb15')
from utils import detect_hardware, print_hardware_status
print_hardware_status(detect_hardware())
"
```

### Step 5: Supply Your UNSW-NB15 Dataset
Upload or mount your dataset into `/content/UNSW-NB15`.

Expected directory structure (any of the following formats):
```text
/content/UNSW-NB15/
├── UNSW_NB15_training-set.csv   # (Preferred official train split: ~175k rows)
└── UNSW_NB15_testing-set.csv    # (Preferred official test split: ~82k rows)
```
*Or raw 4-part CSVs:*
```text
/content/UNSW-NB15/
├── UNSW-NB15_1.csv
├── UNSW-NB15_2.csv
├── UNSW-NB15_3.csv
└── UNSW-NB15_4.csv
```
*Or a single ZIP file containing CSVs:*
```text
/content/UNSW-NB15/UNSW-NB15.zip
```

### Step 6: Run Data Validation & Leakage Audit
```bash
python training/unsw_nb15/prepare_data.py --data-dir /content/UNSW-NB15
```

### Step 7: Train the Model (CatBoost GPU)
```bash
python training/unsw_nb15/train.py \
    --data-dir /content/UNSW-NB15 \
    --device gpu \
    --iterations 1000 \
    --depth 6 \
    --lr 0.05
```

### Step 8: Evaluate Artifact & Cybersecurity Metrics
```bash
python training/unsw_nb15/evaluate.py \
    --artifact artifacts/network-anomaly-unsw/v1 \
    --test-data /content/UNSW-NB15/UNSW_NB15_testing-set.csv
```

### Step 9: Run Cross-Dataset Validation of Model B
Evaluate existing production Model B (NSL-KDD) against UNSW-NB15:
```bash
python training/unsw_nb15/cross_validate_model_b.py \
    --unsw-data /content/UNSW-NB15/UNSW_NB15_testing-set.csv
```

---

## 📁 Artifact Export Contract

When training finishes, a NetraGraph-compliant bundle is generated:
```text
artifacts/network-anomaly-unsw/v1/
├── model.joblib              # Trained CatBoost / Random Forest estimator
├── preprocessor.joblib       # Fitted ColumnTransformer (imputer + scaler + onehot)
├── feature_schema.json       # Feature names, dtypes, categorical indices
├── label_mapping.json        # {"0": "normal", "1": "attack"}
├── metrics.json              # Accuracy, F1, FPR, FNR, ROC-AUC, Confusion Matrix
├── metadata.json             # Hardware provenance, training timestamp, framework versions
├── requirements_model.txt    # Pinned dependency requirements
└── training_report.json      # Complete forensic training report
```

---

## 🛠️ CLI Reference Summary

| Command | Description |
| :--- | :--- |
| `python training/unsw_nb15/prepare_data.py --data-dir <path>` | Audits schema, distributions, and leakage. |
| `python training/unsw_nb15/train.py --data-dir <path> --device gpu` | Trains model with CatBoost GPU and exports artifact. |
| `python training/unsw_nb15/evaluate.py --artifact <path>` | Generates confusion matrix and FPR/FNR analysis. |
| `python training/unsw_nb15/cross_validate_model_b.py --unsw-data <path>` | Evaluates Model B transferability on UNSW-NB15. |

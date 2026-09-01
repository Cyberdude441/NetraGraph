# NetraGraph Multi-Algorithm ML Benchmark

A standardized, reproducible multi-algorithm benchmark for cybersecurity machine learning on NetraGraph.

## Evaluated Algorithms
1. **Random Forest** (Scikit-Learn)
2. **XGBoost** (Extreme Gradient Boosting)
3. **LightGBM** (Light Gradient Boosting Machine)
4. **CatBoost** (Categorical Boosting)

## Evaluated Datasets
1. **CSE-CIC-IDS2018** (`cicids2018`) - Network intrusion and volumetric attack detection
2. **CIC-IDS2017** (`cicids2017`) - Network flow behavioral anomaly detection
3. **CIC-DDoS2019** (`cicddos2019`) - Volumetric and protocol-specific DDoS flow classification
4. **UNSW-NB15** (`unsw`) - Modern synthetic and real attack network flow classification
5. **MalwareBazaar** (`malwarebazaar`) - Malware family signature classification

## Strict Fairness & Scientific Guardrails
- **Single Fixed Split**: Every algorithm is trained and evaluated on the exact same stratified 80/20 train/test split.
- **Identical Features**: All four algorithms consume the exact same preprocessed feature matrix with full leakage audit (IPs, Ports, Timestamps stripped).
- **Fixed Seed**: Reproducible random seed (`42`).
- **No Test-Set Tuning**: Zero hyperparameter optimization on the test split.
- **Hardware Fallbacks**: Automatic GPU acceleration when available with graceful CPU fallback.

## Running the Benchmark

```bash
# Run all datasets
python training/benchmark/benchmark_runner.py

# Run a specific dataset
python training/benchmark/benchmark_runner.py --dataset cicids2018
python training/benchmark/benchmark_runner.py --dataset cicids2017
python training/benchmark/benchmark_runner.py --dataset cicddos2019
python training/benchmark/benchmark_runner.py --dataset unsw
python training/benchmark/benchmark_runner.py --dataset malwarebazaar
```

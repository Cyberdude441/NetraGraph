# NetraGraph Model Training and Deployment

NetraGraph models are trained independently of the running backend. Every artifact is a versioned bundle containing the classifier, fitted preprocessor, exact feature schema, labels, metrics, metadata, and pinned model requirements.

## Supported ML runtime

The official ML runtime is **Python >=3.11,<3.13**, meaning Python 3.11 or 3.12. Python 3.14 can continue to run non-ML backend and frontend functionality, but the pinned scientific ML stack does not support it. The ML package prints this message when invoked on an unsupported interpreter:

```text
NetraGraph ML requires Python 3.11 or 3.12.
Python 3.14 is currently not supported for the pinned scientific ML stack.
```

On Windows, run `./scripts/setup_ml_environment.ps1`. On macOS/Linux, run `./scripts/setup_ml_environment.sh`.

## Local training

From the repository root:

```powershell
./scripts/setup_ml_environment.ps1
$env:PYTHONPATH = "backend"
\.venv-ml\Scripts\python.exe -m ml.training.train_intrusion --data backend/datasets --model-name intrusion --target label --output artifacts
```

Use `train_phishing_url`, `train_phishing_email`, or `train_nlp` with the corresponding model name. Omit `--target` only when the loader can detect a conventional target name such as `label`, `target`, or `is_malicious`.

## A. Google Colab

1. Open the matching notebook in `notebooks/`.
2. Run the self-contained setup cell; it installs `requirements/requirements-colab.txt`, mounts Google Drive when prompted, and can upload a source ZIP containing only `backend/ml`.
3. Set the dataset directory, then run discovery and preprocessing.
4. Train the model independently from Drive, Colab temporary storage, or uploaded ZIP files; the notebook does not start NetraGraph.
5. Evaluate the model and inspect `training_report.json`.
6. Export the complete `model_name/v1` bundle.
7. Download the generated artifact ZIP, or copy it to Drive.
8. In NetraGraph, upload the ZIP to `POST /api/ml/models/import`.

## B. Kaggle

1. Add the dataset as a Kaggle Input dataset.
2. Open the matching NetraGraph notebook and run all cells. Provide the portable `backend/ml` source ZIP as notebook input if the source is not already present.
3. The loader recursively discovers files under `/kaggle/input` without assuming Kaggle filenames.
4. Train and evaluate independently.
5. The bundle and ZIP are saved under `/kaggle/working/artifacts/`.
6. Download or version the output artifact.
7. Import the ZIP into NetraGraph with the model import endpoint.

## C. Local deployment

1. Install backend dependencies from `requirements/requirements-backend.txt` and start the backend.
2. Upload the artifact ZIP to `POST /api/ml/models/import`.
3. The backend extracts safely, checks all required files, validates metadata/schema, loads both persisted objects, and runs a smoke prediction.
4. Activate a version with `POST /api/ml/models/{name}/{version}/activate`.
5. List versions with `GET /api/ml/models` or `GET /api/ml/models/{name}`.
6. Predict with `POST /api/ml/predict/intrusion`, `/phishing-url`, or `/phishing-email`.
7. Each response carries model version, artifact hash, confidence, timestamp, and `analyst_verification_required: true` for traceability.

## Artifact contract

Required files: `model.joblib`, `preprocessor.joblib`, `feature_schema.json`, `label_mapping.json`, `metrics.json`, `metadata.json`, and `requirements_model.txt`. Versions are immutable and are stored under `backend/models/registry/<model_name>/<version>/`; an imported version is activated only after validation succeeds. Multiple versions are supported, with at most one active version per model name.

The current graph and cyber intelligence pipelines remain unchanged. Risk fusion is available in `backend/ml/inference/risk_fusion.py` for consumers that want to attach prediction evidence to graph intelligence records.

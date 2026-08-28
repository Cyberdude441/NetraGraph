#!/usr/bin/env bash
set -euo pipefail

PYTHON_BIN=""
for candidate in python3.12 python3.11; do
  if command -v "$candidate" >/dev/null 2>&1; then PYTHON_BIN="$candidate"; break; fi
done
if [[ -z "$PYTHON_BIN" ]] && command -v uv >/dev/null 2>&1; then
  PYTHON_BIN="$(uv python find 3.12)"
fi
if [[ -z "$PYTHON_BIN" ]]; then
  echo "NetraGraph ML requires Python 3.11 or 3.12."
  echo "Python 3.14 is currently not supported for the pinned scientific ML stack."
  exit 1
fi
"$PYTHON_BIN" -m venv .venv-ml
.venv-ml/bin/python -m pip install --upgrade pip
.venv-ml/bin/python -m pip install -r requirements/requirements-backend.txt
.venv-ml/bin/python -m pip install -r requirements/requirements-training.txt
.venv-ml/bin/python -c "import pandas, numpy, sklearn, joblib; print('Verified pandas', pandas.__version__, 'numpy', numpy.__version__, 'scikit-learn', sklearn.__version__, 'joblib', joblib.__version__)"
echo "ML environment ready. Activate with: source .venv-ml/bin/activate"
echo "Set PYTHONPATH for training with: export PYTHONPATH=backend"

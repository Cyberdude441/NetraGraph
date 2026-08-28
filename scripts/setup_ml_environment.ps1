$ErrorActionPreference = 'Stop'
$pythonPath = $null
if (Get-Command py -ErrorAction SilentlyContinue) {
	foreach ($candidate in @('3.12', '3.11')) {
		try {
			$found = & py -$candidate -c "import sys; print(sys.executable)" 2>$null
			if ($LASTEXITCODE -eq 0 -and $found) { $pythonPath = $found.Trim(); break }
		} catch {
			continue
		}
	}
}
if (-not $pythonPath -and (Get-Command uv -ErrorAction SilentlyContinue)) {
	$pythonPath = (& uv python find 3.12 2>$null).Trim()
}
if (-not $pythonPath) { Write-Error "NetraGraph ML requires Python 3.11 or 3.12.`nPython 3.14 is currently not supported for the pinned scientific ML stack." }
& $pythonPath -m venv .venv-ml
& .\.venv-ml\Scripts\python.exe -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) { throw "pip upgrade failed" }
& .\.venv-ml\Scripts\python.exe -m pip install -r requirements/requirements-backend.txt
if ($LASTEXITCODE -ne 0) { throw "Backend dependency installation failed" }
& .\.venv-ml\Scripts\python.exe -m pip install -r requirements/requirements-training.txt
if ($LASTEXITCODE -ne 0) { throw "Training dependency installation failed" }
& .\.venv-ml\Scripts\python.exe -c "import pandas, numpy, sklearn, joblib; print('Verified pandas', pandas.__version__, 'numpy', numpy.__version__, 'scikit-learn', sklearn.__version__, 'joblib', joblib.__version__)"
if ($LASTEXITCODE -ne 0) { throw "ML package verification failed" }
Write-Host "ML environment ready. Activate with: .\.venv-ml\Scripts\Activate.ps1"
Write-Host "Set PYTHONPATH for training with: `$env:PYTHONPATH = 'backend'"

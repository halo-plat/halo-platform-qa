# Halo Test Lab GUI launcher (Windows PowerShell)
# Uses venv interpreter directly to avoid Activation/ExecutionPolicy issues.

$venvPy = ".\.venv\Scripts\python.exe"

if (!(Test-Path $venvPy)) {
  Write-Host "Creating venv..."
  python -m venv .venv
  if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

Write-Host "Installing/updating dependencies..."
& $venvPy -m pip install -r requirements.txt | Out-Host
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "Launching GUI..."
& $venvPy -m halo_test_lab.gui
exit $LASTEXITCODE

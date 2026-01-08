param(
  [string]$VenvDir = "halo-test-lab-win11\.venv"
)
$ErrorActionPreference = "Stop"

python -m venv $VenvDir
$py = Join-Path $VenvDir "Scripts\python.exe"

& $py -m pip install -U pip
& $py -m pip install -r (Join-Path $PSScriptRoot "..\requirements-win11.txt")

Write-Host ("VENV_READY=" + (Resolve-Path $VenvDir))
Write-Host ("ACTIVATE=" + (Join-Path $VenvDir "Scripts\Activate.ps1"))
param(
  [string]$GatewayBaseUrl = "http://127.0.0.1:8080"
)

$ErrorActionPreference = "Stop"
$repo = Resolve-Path (Join-Path $PSScriptRoot "..")
$env:HALO_GATEWAY_BASE_URL = $GatewayBaseUrl

New-Item -ItemType Directory -Force (Join-Path $repo "artifacts") | Out-Null

pytest -q `
  --junitxml (Join-Path $repo "artifacts\junit.xml") `
  --html (Join-Path $repo "artifacts\report.html") --self-contained-html `
  --json-report --json-report-file (Join-Path $repo "artifacts\report.json")

python (Join-Path $repo "tools\qa_assess.py") `
  $repo `
  (Join-Path $repo "artifacts") `
  (Join-Path $repo "artifacts\security_assessment.md") `
  (Join-Path $repo "artifacts\privacy_assessment.md") `
  (Join-Path $repo "artifacts\links.json")

python (Join-Path $repo "tools\qa_summarize.py") `
  (Join-Path $repo "artifacts\report.json") `
  (Join-Path $repo "artifacts\executive.md") `
  (Join-Path $repo "artifacts\engineering.json") `
  (Join-Path $repo "artifacts\index.html") `
  (Join-Path $repo "artifacts\links.json")

Write-Host ("ARTIFACTS_DIR=" + (Join-Path $repo "artifacts"))
Write-Host "GUI: python -m http.server 7777 --directory artifacts"
param(
  [string]$GatewayBaseUrl = "http://127.0.0.1:8080",
  [switch]$StartGatewayStub = $true,
  [string]$IntegrationRepo = "D:\HaloProject\repos\core\halo-platform-integration"
)

$ErrorActionPreference = "Stop"
$repo = Resolve-Path (Join-Path $PSScriptRoot "..")

if ($StartGatewayStub) {
  & (Join-Path $repo "scripts\sim_gateway_stub.ps1") start -IntegrationRepo $IntegrationRepo
}

try {
  & (Join-Path $repo "scripts\qa_run.ps1") -GatewayBaseUrl $GatewayBaseUrl
} finally {
  if ($StartGatewayStub) {
    & (Join-Path $repo "scripts\sim_gateway_stub.ps1") stop
  }
}

Write-Host "LAB_OK=1"
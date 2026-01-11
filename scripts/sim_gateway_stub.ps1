param(
  [ValidateSet("start","stop","status")]
  [string]$Action = "status",

  [string]$IntegrationRepo = "D:\HaloProject\repos\core\halo-platform-integration",
  [Alias("Host")][string]$BindHost = "127.0.0.1",
  [int]$Port = 8080,

  [string]$PythonExe = "python"
)

$ErrorActionPreference = "Stop"

$repo = Resolve-Path (Join-Path $PSScriptRoot "..")
$pidFile = Join-Path $repo "artifacts\gateway_stub.pid"
$logOut  = Join-Path $repo "artifacts\gateway_stub.out.log"
$logErr  = Join-Path $repo "artifacts\gateway_stub.err.log"

function Is-Running([int]$gwPid) {
  try { Get-Process -Id $gwPid -ErrorAction Stop | Out-Null; return $true } catch { return $false }
}

function Wait-Health([string]$BaseUrl, [int]$Seconds=10) {
  $deadline = (Get-Date).AddSeconds($Seconds)
  while ((Get-Date) -lt $deadline) {
    try {
      $r = Invoke-WebRequest -UseBasicParsing -TimeoutSec 2 -Uri ($BaseUrl + "/health")
      if ($r.StatusCode -eq 200) { return $true }
    } catch {}
    Start-Sleep -Milliseconds 250
  }
  return $false
}

$baseUrl = "http://$BindHost`:$Port"

if ($Action -eq "status") {
  if (Test-Path $pidFile) {
    $gwPid = [int](Get-Content $pidFile -Raw)
    if (Is-Running $gwPid) {
      Write-Host "GATEWAY_STUB_STATUS=RUNNING PID=$gwPid URL=$baseUrl"
      exit 0
    }
  }
  Write-Host "GATEWAY_STUB_STATUS=STOPPED URL=$baseUrl"
  exit 0
}

if ($Action -eq "stop") {
  if (Test-Path $pidFile) {
    $gwPid = [int](Get-Content $pidFile -Raw)
    if (Is-Running $gwPid) {
      Stop-Process -Id $gwPid -Force
      Start-Sleep -Milliseconds 250
    }
    Remove-Item -Force $pidFile -ErrorAction SilentlyContinue
  }
  Write-Host "GATEWAY_STUB_STOPPED=1"
  exit 0
}

# start
if (Test-Path $pidFile) {
  $gwPid = [int](Get-Content $pidFile -Raw)
  if (Is-Running $gwPid) {
    Write-Host "GATEWAY_STUB_ALREADY_RUNNING PID=$gwPid URL=$baseUrl"
    exit 0
  } else {
    Remove-Item -Force $pidFile -ErrorAction SilentlyContinue
  }
}

if (-not (Test-Path $IntegrationRepo)) {
  throw "IntegrationRepo not found: $IntegrationRepo"
}

$serverPy = Join-Path $IntegrationRepo "gateway-stub\app\server.py"
if (-not (Test-Path $serverPy)) {
  throw "gateway stub server not found: $serverPy"
}

# clear logs
New-Item -ItemType File -Force $logOut | Out-Null
New-Item -ItemType File -Force $logErr | Out-Null

$env:HOST = $BindHost
$env:PORT = "$Port"

$p = Start-Process -FilePath $PythonExe `
  -ArgumentList @($serverPy) `
  -WorkingDirectory $IntegrationRepo `
  -PassThru -NoNewWindow `
  -RedirectStandardOutput $logOut `
  -RedirectStandardError  $logErr

Set-Content -Path $pidFile -Value $p.Id -Encoding ascii

if (-not (Wait-Health $baseUrl 12)) {
  Write-Host "GATEWAY_STUB_HEALTH=FAIL PID=$($p.Id) URL=$baseUrl"
  Write-Host "STDOUT_LOG=$logOut"
  Write-Host "STDERR_LOG=$logErr"
  exit 2
}

Write-Host "GATEWAY_STUB_STARTED PID=$($p.Id) URL=$baseUrl"
Write-Host "STDOUT_LOG=$logOut"
Write-Host "STDERR_LOG=$logErr"



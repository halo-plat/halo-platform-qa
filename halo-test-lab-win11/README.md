# Halo Test Lab (Win11) — GUI Orchestrator for Automated Testing

This repository provides a **Windows 11 desktop GUI** that orchestrates Halo Platform test automation:
- **Regression / E2E smoke** via `pytest`
- **Performance & Load** via `k6`
- Run manifests (build SHA, env, suites, timings), logs, and machine-readable outputs (JUnit/XML, JSON)

The GUI is intentionally thin: it **selects, runs, and reports** test suites to keep execution repeatable and audit-friendly.

## Quickstart (Win11)
1. Ensure **Python 3.12+** is installed.
2. Unblock scripts (first time only, after ZIP extraction):
   - `powershell -ExecutionPolicy Bypass -File .\tools\unblock_all.ps1`
3. Launch the GUI:
   - `.un_gui.ps1`

## Installing k6 (Load/Perf)
Install via winget:
- `winget install --id GrafanaLabs.k6 -e --source winget`

If `k6` is installed but not found on PATH, set `k6_exe` in your config YAML (recommended) instead of rewriting PATH.

## Environment profiles
Profiles live in `configs/*.yaml` and define:
- `base_url` and `health_url`
- authentication placeholders (client_id, api_key)
- optional tool paths (e.g., `k6_exe`)

## Local health stub (for controlled runs)
Start a simple local `/health` endpoint:
- `.\.venv\Scripts\python.exe .\examples\health_stub.py`
Then set:
- `base_url: http://127.0.0.1:8000`
- `health_url: http://127.0.0.1:8000/health`

## Governance note
This tool is designed to map cleanly to STVP/RTM:
- Test cases should carry IDs (e.g., `TC-CONV-001`) in names or markers.
- Runs produce evidence artifacts that can be archived.

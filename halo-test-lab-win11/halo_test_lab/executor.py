from __future__ import annotations
import json
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Optional

@dataclass
class RunResult:
    name: str
    exit_code: int
    stdout_path: Path
    stderr_path: Path
    artifact_paths: List[Path]

def _run(cmd: List[str], cwd: Path, out_dir: Path, name: str, env: Optional[Dict[str, str]] = None) -> RunResult:
    out_dir.mkdir(parents=True, exist_ok=True)
    stdout_path = out_dir / f"{name}.stdout.log"
    stderr_path = out_dir / f"{name}.stderr.log"

    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)

    with stdout_path.open("w", encoding="utf-8") as so, stderr_path.open("w", encoding="utf-8") as se:
        p = subprocess.Popen(cmd, cwd=str(cwd), stdout=so, stderr=se, text=True, env=merged_env)
        code = p.wait()

    return RunResult(name=name, exit_code=code, stdout_path=stdout_path, stderr_path=stderr_path, artifact_paths=[stdout_path, stderr_path])

def run_pytest(repo_root: Path, out_dir: Path, marker: str = "e2e", extra_env: Optional[Dict[str, str]] = None) -> RunResult:
    junit = out_dir / "pytest-junit.xml"
    cmd = [sys.executable, "-m", "pytest", "-m", marker, "--junitxml", str(junit), "-q"]
    rr = _run(cmd, cwd=repo_root, out_dir=out_dir, name="pytest", env=extra_env)
    rr.artifact_paths.append(junit)
    return rr

def _find_k6(k6_exe: str | None = None) -> str:
    # 1) explicit config path
    if k6_exe:
        return k6_exe
    # 2) PATH
    w = shutil.which("k6")
    if w:
        return w
    # 3) common MSI locations
    pf = os.environ.get("ProgramFiles", r"C:\Program Files")
    candidates = [
        os.path.join(pf, "k6", "k6.exe"),
        os.path.join(pf, "k6", "bin", "k6.exe"),
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    raise FileNotFoundError("k6 executable not found (set PATH or set k6_exe in config YAML)")

def run_k6(repo_root: Path, out_dir: Path, script: Path, extra_env: Optional[Dict[str, str]] = None, k6_exe: str | None = None) -> RunResult:
    summary = out_dir / "k6-summary.json"
    exe = _find_k6(k6_exe)
    cmd = [exe, "run", str(script), "--summary-export", str(summary)]
    rr = _run(cmd, cwd=repo_root, out_dir=out_dir, name="k6", env=extra_env)
    rr.artifact_paths.append(summary)
    return rr

def write_run_manifest(out_dir: Path, manifest: dict) -> Path:
    path = out_dir / "run-manifest.json"
    path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return path

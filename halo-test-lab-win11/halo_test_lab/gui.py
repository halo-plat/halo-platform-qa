from __future__ import annotations
import sys
from pathlib import Path
from datetime import datetime
from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import (
    QApplication, QComboBox, QCheckBox, QFileDialog, QGridLayout, QGroupBox, QHBoxLayout,
    QLabel, QLineEdit, QMainWindow, QMessageBox, QPushButton, QPlainTextEdit, QVBoxLayout, QWidget
)

from .config import load_env_config
from .executor import run_pytest, run_k6, write_run_manifest

REPO_ROOT = Path(__file__).resolve().parents[1]

class RunnerThread(QThread):
    log = Signal(str)
    done = Signal(int, str)

    def __init__(self, env_path: Path, do_pytest: bool, do_k6: bool, k6_script: Path | None):
        super().__init__()
        self.env_path = env_path
        self.do_pytest = do_pytest
        self.do_k6 = do_k6
        self.k6_script = k6_script

    def run(self) -> None:
        ts = datetime.now().strftime("%Y%m%d-%H%M%S")
        out_dir = REPO_ROOT / "runs" / ts
        out_dir.mkdir(parents=True, exist_ok=True)

        env = load_env_config(self.env_path)
        # Prefer explicit health_url; otherwise fall back to base_url (user chooses what it means).
        health_url = env.health_url or env.base_url

        extra_env = {
            "HALO_BASE_URL": env.base_url,
            "HALO_HEALTH_URL": health_url,
            "HALO_CLIENT_ID": env.client_id,
            "HALO_API_KEY": env.api_key,
        }

        manifest = {
            "timestamp": ts,
            "env": env.__dict__,
            "repo_root": str(REPO_ROOT),
            "suites": [],
        }

        exit_code = 0

        try:
            self.log.emit(f"[Run] Output dir: {out_dir}")
            self.log.emit(f"[Env] {env.name} => base_url={env.base_url}")
            self.log.emit(f"[Env] health_url={health_url}")

            if self.do_pytest:
                self.log.emit("[Suite] pytest (E2E/Regression) starting...")
                rr = run_pytest(REPO_ROOT, out_dir / "pytest", marker="e2e", extra_env=extra_env)
                manifest["suites"].append({
                    "name": "pytest",
                    "exit_code": rr.exit_code,
                    "artifacts": [str(p) for p in rr.artifact_paths]
                })
                self.log.emit(f"[Suite] pytest done (exit={rr.exit_code})")
                exit_code = max(exit_code, rr.exit_code)

            if self.do_k6:
                if not self.k6_script:
                    raise RuntimeError("k6 script not selected")
                self.log.emit("[Suite] k6 (Load/Perf) starting...")
                rr = run_k6(REPO_ROOT, out_dir / "k6", script=self.k6_script, extra_env=extra_env, k6_exe=env.k6_exe)
                manifest["suites"].append({
                    "name": "k6",
                    "exit_code": rr.exit_code,
                    "artifacts": [str(p) for p in rr.artifact_paths]
                })
                self.log.emit(f"[Suite] k6 done (exit={rr.exit_code})")
                exit_code = max(exit_code, rr.exit_code)

            mpath = write_run_manifest(out_dir, manifest)
            self.log.emit(f"[Manifest] {mpath}")
            self.done.emit(exit_code, str(out_dir))
        except Exception as e:
            self.log.emit(f"[Error] {e}")
            self.done.emit(1, str(out_dir))

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Halo Test Lab (Win11)")

        self.env_combo = QComboBox()
        self._load_envs()

        self.pytest_cb = QCheckBox("Run pytest (E2E / Regression)")
        self.pytest_cb.setChecked(True)

        self.k6_cb = QCheckBox("Run k6 (Load / Performance)")
        self.k6_cb.setChecked(True)

        self.k6_path = QLineEdit(str(REPO_ROOT / "examples" / "k6" / "basic.js"))
        self.k6_browse = QPushButton("Browse…")
        self.k6_browse.clicked.connect(self._browse_k6)

        self.run_btn = QPushButton("Run selected suites")
        self.run_btn.clicked.connect(self._run)

        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)

        layout = QVBoxLayout()

        env_box = QGroupBox("Environment")
        env_l = QHBoxLayout()
        env_l.addWidget(QLabel("Profile:"))
        env_l.addWidget(self.env_combo)
        env_box.setLayout(env_l)

        suite_box = QGroupBox("Suites")
        grid = QGridLayout()
        grid.addWidget(self.pytest_cb, 0, 0, 1, 2)
        grid.addWidget(self.k6_cb, 1, 0, 1, 2)
        grid.addWidget(QLabel("k6 script:"), 2, 0)
        grid.addWidget(self.k6_path, 2, 1)
        grid.addWidget(self.k6_browse, 2, 2)
        suite_box.setLayout(grid)

        layout.addWidget(env_box)
        layout.addWidget(suite_box)
        layout.addWidget(self.run_btn)
        layout.addWidget(QLabel("Run log"))
        layout.addWidget(self.log)

        w = QWidget()
        w.setLayout(layout)
        self.setCentralWidget(w)

        self.worker: RunnerThread | None = None

    def _load_envs(self):
        self.env_combo.clear()
        cfg_dir = REPO_ROOT / "configs"
        cfg_dir.mkdir(exist_ok=True)
        for p in sorted(cfg_dir.glob("*.yaml")):
            self.env_combo.addItem(p.stem, str(p))

        if self.env_combo.count() == 0:
            default = cfg_dir / "staging.yaml"
            default.write_text(
                "name: staging\n"
                "base_url: https://staging.example/api\n"
                "health_url: https://staging.example/api/health\n"
                "client_id: YOUR_CLIENT\n"
                "api_key: YOUR_KEY\n"
                "timeout_s: 30\n"
                "# Optional (if k6 isn't on PATH):\n"
                "# k6_exe: C:/Program Files/k6/k6.exe\n",
                encoding="utf-8"
            )
            self.env_combo.addItem(default.stem, str(default))

    def _browse_k6(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select k6 script", str(REPO_ROOT), "JavaScript (*.js)")
        if path:
            self.k6_path.setText(path)

    def _append(self, msg: str):
        self.log.appendPlainText(msg)

    def _run(self):
        env_path = Path(self.env_combo.currentData())
        do_pytest = self.pytest_cb.isChecked()
        do_k6 = self.k6_cb.isChecked()
        k6_script = Path(self.k6_path.text()) if do_k6 else None

        self.run_btn.setEnabled(False)
        self._append("=== Starting run ===")
        self.worker = RunnerThread(env_path, do_pytest, do_k6, k6_script)
        self.worker.log.connect(self._append)
        self.worker.done.connect(self._done)
        self.worker.start()

    def _done(self, code: int, out_dir: str):
        self.run_btn.setEnabled(True)
        self._append(f"=== Completed (exit={code}) ===")
        self._append(f"Artifacts: {out_dir}")
        if code != 0:
            QMessageBox.warning(self, "Run completed with failures", f"Exit code: {code}\nSee: {out_dir}")
        else:
            QMessageBox.information(self, "Run completed", f"All selected suites passed.\nSee: {out_dir}")

def main():
    app = QApplication(sys.argv)
    mw = MainWindow()
    mw.resize(900, 650)
    mw.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()

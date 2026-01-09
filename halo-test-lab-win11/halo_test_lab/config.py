from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import yaml

@dataclass(frozen=True)
class EnvConfig:
    name: str
    base_url: str
    client_id: str
    api_key: str
    timeout_s: int = 30
    # Optional explicit health URL (recommended to avoid ambiguity about "/api" etc.)
    health_url: str | None = None
    # Optional explicit path to k6 executable (useful when PATH is not reliable)
    k6_exe: str | None = None

def load_env_config(path: Path) -> EnvConfig:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return EnvConfig(
        name=data.get("name", path.stem),
        base_url=data["base_url"],
        client_id=data.get("client_id", ""),
        api_key=data.get("api_key", ""),
        timeout_s=int(data.get("timeout_s", 30)),
        health_url=data.get("health_url"),
        k6_exe=data.get("k6_exe"),
    )

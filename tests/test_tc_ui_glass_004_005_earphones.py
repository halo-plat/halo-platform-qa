import sys
from pathlib import Path

from fastapi.testclient import TestClient


def _load_backend_app():
    # backend repo in sibling folder
    backend_path = Path(r"D:\Halo Project\dev\halo-platform-backend").resolve()
    sys.path.insert(0, str(backend_path))
    from app.main import app  # noqa: E402
    return app


def test_tc_ui_glass_004_audio_output_routing_override_to_earbuds():
    app = _load_backend_app()
    client = TestClient(app)

    sid = "tc-ui-glass-004"
    r1 = client.post("/api/v1/conversation/message", json={"session_id": sid, "user_utterance": "use earbuds"})
    assert r1.status_code == 200
    j1 = r1.json()
    assert j1["audio_route_applied"] == "paired_device"
    assert "confirm" in j1["audio_cues"]


def test_tc_ui_glass_005_audio_cues_session_start_present():
    app = _load_backend_app()
    client = TestClient(app)

    sid = "tc-ui-glass-005"
    r = client.post("/api/v1/conversation/message", json={"session_id": sid, "user_utterance": "hello"})
    assert r.status_code == 200
    j = r.json()
    assert "session_start" in j["audio_cues"]

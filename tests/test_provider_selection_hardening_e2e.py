import os
import sys
from pathlib import Path

from fastapi.testclient import TestClient


def _load_backend_app():
    # QA repo: ...\halo-platform-qa\tests\...
    # Backend repo sibling: ...\halo-platform-backend
    backend_root = Path(__file__).resolve().parents[1].parent / "halo-platform-backend"
    sys.path.insert(0, str(backend_root))
    from app.main import app  # noqa: E402
    return app


def test_news_eco_does_not_switch_provider_default_echo():
    os.environ["HALO_AI_DEFAULT_PROVIDER"] = "echo"
    os.environ.pop("PERPLEXITY_API_KEY", None)

    app = _load_backend_app()
    client = TestClient(app)

    r = client.post("/api/v1/conversation/message", json={"session_id": "s-hard-1", "user_utterance": "news eco"})
    assert r.status_code == 200
    j = r.json()

    assert j["ai_provider_requested"] == "echo"
    assert j["ai_provider_applied"] == "echo"
    assert j["ai_routing_reason"].startswith("default_policy:")


def test_usa_eco_forces_echo_override_even_if_default_is_perplexity():
    os.environ["HALO_AI_DEFAULT_PROVIDER"] = "perplexity"
    os.environ.pop("PERPLEXITY_API_KEY", None)

    app = _load_backend_app()
    client = TestClient(app)

    r = client.post("/api/v1/conversation/message", json={"session_id": "s-hard-2", "user_utterance": "usa eco"})
    assert r.status_code == 200
    j = r.json()

    assert j["ai_provider_requested"] == "echo"
    assert j["ai_provider_applied"] == "echo"
    assert j["ai_routing_reason"].startswith("explicit_override:")


def test_passa_a_perplexity_requests_perplexity_even_without_key_but_falls_back():
    os.environ["HALO_AI_DEFAULT_PROVIDER"] = "echo"
    os.environ.pop("PERPLEXITY_API_KEY", None)

    app = _load_backend_app()
    client = TestClient(app)

    r = client.post("/api/v1/conversation/message", json={"session_id": "s-hard-3", "user_utterance": "passa a perplexity"})
    assert r.status_code == 200
    j = r.json()

    assert j["ai_provider_requested"] == "perplexity"
    assert j["ai_provider_applied"] == "echo"
    assert "degraded_" in j["ai_routing_reason"]


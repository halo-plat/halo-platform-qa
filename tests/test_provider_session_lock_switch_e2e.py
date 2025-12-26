import os
import time
import uuid
import requests


BASE_URL = os.getenv("HALO_BACKEND_URL", "http://127.0.0.1:8000")
ENDPOINT = f"{BASE_URL}/api/v1/conversation/message"


def post(session_id: str, user_utterance: str) -> dict:
    r = requests.post(
        ENDPOINT,
        json={"session_id": session_id, "user_utterance": user_utterance},
        headers={"Content-Type": "application/json; charset=utf-8"},
        timeout=60,
    )
    r.raise_for_status()
    return r.json()


def test_provider_session_lock_and_switch_e2e():
    # Uvicorn deve essere già up su 127.0.0.1:8000
    session_id = f"s-e2e-{uuid.uuid4().hex[:10]}"

    # 1) default_policy -> perplexity, e DEVE anche lockare la sessione
    r1 = post(session_id, "ciao")
    assert r1["ai_provider_requested"] == "perplexity"
    assert r1["ai_provider_applied"] == "perplexity"
    assert r1["ai_routing_reason"].startswith("default_policy:")
    assert ("perplexity_chat_completions" in r1["ai_routing_reason"]) or ("degraded_perplexity_error" in r1["ai_routing_reason"])

    # 2) follow-up -> session_locked -> perplexity
    r2 = post(session_id, "ciao")
    assert r2["ai_provider_requested"] == "perplexity"
    assert r2["ai_provider_applied"] == "perplexity"
    assert r2["ai_routing_reason"].startswith("session_locked:")
    assert ("perplexity_chat_completions" in r2["ai_routing_reason"]) or ("degraded_perplexity_error" in r2["ai_routing_reason"])

    # 3) explicit_override -> echo (usa eco) + confirm cue
    r3 = post(session_id, "usa eco")
    assert r3["ai_provider_requested"] == "echo"
    assert r3["ai_provider_applied"] == "echo"
    assert r3["ai_routing_reason"].startswith("explicit_override:")
    assert "echo_stub" in r3["ai_routing_reason"]
    assert "confirm" in (r3.get("audio_cues") or [])

    # 4) follow-up -> session_locked -> echo
    r4 = post(session_id, "ciao")
    assert r4["ai_provider_requested"] == "echo"
    assert r4["ai_provider_applied"] == "echo"
    assert r4["ai_routing_reason"].startswith("session_locked:")
    assert "echo_stub" in r4["ai_routing_reason"]

    # 5) explicit_override -> perplexity (use perplexity) + confirm cue
    r5 = post(session_id, "use perplexity")
    assert r5["ai_provider_requested"] == "perplexity"
    assert r5["ai_provider_applied"] == "perplexity"
    assert r5["ai_routing_reason"].startswith("explicit_override:")
    assert ("perplexity_chat_completions" in r5["ai_routing_reason"]) or ("degraded_perplexity_error" in r5["ai_routing_reason"])
    assert "confirm" in (r5.get("audio_cues") or [])

    # 6) follow-up -> session_locked -> perplexity
    r6 = post(session_id, "ciao")
    assert r6["ai_provider_requested"] == "perplexity"
    assert r6["ai_provider_applied"] == "perplexity"
    assert r6["ai_routing_reason"].startswith("session_locked:")
    assert ("perplexity_chat_completions" in r6["ai_routing_reason"]) or ("degraded_perplexity_error" in r6["ai_routing_reason"])





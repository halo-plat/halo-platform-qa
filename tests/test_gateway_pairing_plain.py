import os, json, time, base64
import requests
import pytest

BASE = os.environ.get("HALO_GATEWAY_BASE_URL", "http://127.0.0.1:8080")

def test_health():
    r = requests.get(BASE + "/health", timeout=10)
    assert r.status_code == 200

def test_pairing_plain_happy_path():
    req = {
        "device_id": "dev-qa-001",
        "device_pubkey": "pk-test",
        "nonce": "n-" + str(int(time.time())),
        "ts": "2026-01-07T00:00:00Z",
    }
    r1 = requests.post(BASE + "/pairing/request", json=req, timeout=10)
    assert r1.status_code == 200
    j1 = r1.json()
    assert "pairing_code" in j1 and "pairing_session_id" in j1

    r2 = requests.post(
        BASE + "/pairing/confirm",
        json={"pairing_code": j1["pairing_code"], "pairing_session_id": j1["pairing_session_id"]},
        headers={"Authorization": "Bearer test-token"},
        timeout=10,
    )
    assert r2.status_code == 200
    assert r2.json().get("status") == "confirmed"

    r3 = requests.post(
        BASE + "/pairing/provision",
        json={"pairing_session_id": j1["pairing_session_id"], "proof_of_possession": "pop-test"},
        timeout=10,
    )
    assert r3.status_code == 201
    j3 = r3.json()
    assert "device_access_token" in j3

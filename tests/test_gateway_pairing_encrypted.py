import os, json, time, base64, datetime
import requests
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

BASE = os.environ.get("HALO_GATEWAY_BASE_URL", "http://127.0.0.1:8080")

def b64ud(s: str) -> bytes:
    s = (s or "").strip()
    s += "=" * ((4 - (len(s) % 4)) % 4)
    return base64.urlsafe_b64decode(s.encode("ascii"))

def b64ue(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).decode("ascii").rstrip("=")

def aad(method: str, path: str, sid: str, seq: int) -> bytes:
    return f"{method}|{path}|{sid}|{seq}".encode("utf-8")

def utc_ts() -> str:
    # sufficiente per test; warning deprecazione non blocca
    return datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z")

def derive_key(priv: X25519PrivateKey, gw_pub_raw: bytes, salt: bytes, sid: str) -> bytes:
    from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PublicKey as _X25519PublicKey
    shared = priv.exchange(_X25519PublicKey.from_public_bytes(gw_pub_raw))
    from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PublicKey
    shared = priv.exchange(X25519PublicKey.from_public_bytes(gw_pub_raw))
    info = ("halo-pairing-v1|" + sid).encode("utf-8")  # server-side HKDF info corrente nello stub
    hkdf = HKDF(algorithm=hashes.SHA256(), length=32, salt=salt, info=info)
    return hkdf.derive(shared)

def encrypt_env(aes_key: bytes, kid: str, method: str, path: str, sid: str, seq: int, payload_obj: dict) -> dict:
    a = aad(method, path, sid, seq)
    nonce = os.urandom(12)
    pt = json.dumps(payload_obj, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ct = AESGCM(aes_key).encrypt(nonce, pt, a)
    return {
        "v": 1,
        "alg": "A256GCM",
        "kid": kid,
        "nonce_b64url": b64ue(nonce),
        "aad_b64url": b64ue(a),
        "ct_b64url": b64ue(ct),
        "seq": seq,
        "ts": utc_ts(),
    }

def decrypt_env(aes_key: bytes, method: str, path: str, sid: str, env: dict) -> dict:
    seq = int(env["seq"])
    a = aad(method, path, sid, seq)
    nonce = b64ud(env["nonce_b64url"])
    ct = b64ud(env["ct_b64url"])
    pt = AESGCM(aes_key).decrypt(nonce, ct, a)
    return json.loads(pt.decode("utf-8"))

def test_pairing_encrypted_confirm_and_provision():
    priv = X25519PrivateKey.generate()
    pub_raw = priv.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
    device_pubkey_b64url = b64ue(pub_raw)

    req = {
        "device_id": "dev-qa-enc-001",
        "device_pubkey": device_pubkey_b64url,
        "nonce": "n-" + str(int(time.time())),
        "ts": "2026-01-07T00:00:00Z",
    }
    r1 = requests.post(BASE + "/pairing/request", json=req, timeout=10)
    assert r1.status_code == 200
    j1 = r1.json()
    assert "crypto" in j1

    sid = j1["pairing_session_id"]
    code = j1["pairing_code"]
    c = j1["crypto"]
    assert c.get("alg") == "A256GCM"
    assert c.get("kid")
    assert c.get("gateway_pubkey_b64url")
    assert c.get("hkdf_salt_b64url")

    gw_pub = b64ud(c["gateway_pubkey_b64url"])
    salt = b64ud(c["hkdf_salt_b64url"])
    aes_key = derive_key(priv, gw_pub, salt, sid)

    # confirm (encrypted request -> encrypted response)
    env_req = encrypt_env(aes_key, c["kid"], "POST", "/pairing/confirm", sid, 1, {"pairing_code": code})
    r2 = requests.post(
        BASE + "/pairing/confirm",
        json={"pairing_session_id": sid, "payload_enc": env_req},
        headers={"Authorization": "Bearer test-token"},
        timeout=10,
    )
    assert r2.status_code == 200
    env_resp = r2.json().get("payload_enc")
    assert env_resp and env_resp.get("kid") == c["kid"]
    dec = decrypt_env(aes_key, "POST", "/pairing/confirm", sid, env_resp)
    assert dec.get("status") == "confirmed"

    # provision (encrypted request -> encrypted response)
    env_req2 = encrypt_env(aes_key, c["kid"], "POST", "/pairing/provision", sid, 2, {"proof_of_possession": "pop-test"})
    r3 = requests.post(BASE + "/pairing/provision", json={"pairing_session_id": sid, "payload_enc": env_req2}, timeout=10)
    assert r3.status_code == 201
    env_resp2 = r3.json().get("payload_enc")
    assert env_resp2
    dec2 = decrypt_env(aes_key, "POST", "/pairing/provision", sid, env_resp2)
    assert "device_access_token" in dec2

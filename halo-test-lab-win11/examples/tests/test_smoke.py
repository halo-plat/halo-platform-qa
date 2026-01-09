import os
import httpx
import pytest

@pytest.mark.e2e
def test_health_smoke():
    # Minimal E2E smoke: calls HALO_HEALTH_URL. Replace with real auth + endpoints when ready.
    url = os.getenv("HALO_HEALTH_URL", "https://staging.example/api/health")
    with httpx.Client(timeout=10) as c:
        r = c.get(url)
    assert r.status_code in (200, 204)

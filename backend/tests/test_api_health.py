from fastapi.testclient import TestClient

from app.api import router
from fastapi import FastAPI


def _client() -> TestClient:
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


def test_health_endpoint():
    r = _client().get("/api/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert "zones" in data


def test_zones_endpoint_returns_list():
    r = _client().get("/api/zones")
    assert r.status_code == 200
    assert isinstance(r.json(), list)

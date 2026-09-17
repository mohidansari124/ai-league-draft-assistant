import json
import httpx
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services import explanations

client = TestClient(app)

@pytest.fixture(autouse=True)
def no_real_ai(monkeypatch):
    monkeypatch.setenv("EXPLANATION_PROVIDER", "template")
    monkeypatch.setenv("STATS_PROVIDER", "disabled")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

def test_catalog_and_health():
    assert client.get("/api/health").json()["status"] == "ok"
    response = client.get("/api/champions")
    assert response.status_code == 200
    assert len(response.json()["champions"]) == 173
    assert "Riot" in response.json()["dataVersion"]

@pytest.mark.parametrize("payload", [
    {"role": "invalid", "championPool": ["Ornn"]},
    {"role": "top", "championPool": []},
    {"role": "top", "championPool": ["Ornn", "Ornn"]},
    {"role": "top", "championPool": ["Ornn"], "allies": ["Garen"], "enemies": ["Garen"]},
    {"role": "top", "championPool": ["Ornn"], "laneOpponent": "Darius"},
    {"role": "top", "championPool": ["Ornn"], "comfort": {"Ornn": 6}},
    {"role": "top", "championPool": ["Ornn"], "comfort": {"Garen": 3}},
    {"role": "top", "championPool": ["NotReal"]},
    {"role": "top", "championPool": ["Ornn"], "comfort": {"Ornn": True}},
    {"role": "jungle", "championPool": ["Vi"], "enemies": ["Darius"], "laneOpponent": "Darius"},
    {"role": "top", "championPool": ["Ornn"], "enemies": ["Darius", "Darius"]},
])
def test_invalid_requests_return_422(payload):
    assert client.post("/api/analyze", json=payload).status_code == 422

def test_no_key_returns_template():
    response = client.post("/api/analyze", json={"role": "top", "championPool": ["Ornn"]})
    assert response.status_code == 200
    assert response.json()["explanationMode"] == "template"

class FakeClient:
    def __init__(self, *args, **kwargs): pass
    async def __aenter__(self): return self
    async def __aexit__(self, *args): pass
    async def post(self, *args, **kwargs):
        raise httpx.ConnectError("Test outage")

def test_ai_outage_falls_back_without_changing_scores(monkeypatch):
    payload = {"role": "top", "championPool": ["Ornn"]}
    baseline = client.post("/api/analyze", json=payload).json()
    monkeypatch.setenv("EXPLANATION_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "test-only-placeholder")
    monkeypatch.setattr(explanations.httpx, "AsyncClient", FakeClient)
    data = client.post("/api/analyze", json=payload).json()
    assert data["recommendations"] == baseline["recommendations"]
    assert any("unavailable" in w for w in data["warnings"])

def test_ai_success_changes_only_prose(monkeypatch):
    class SuccessClient(FakeClient):
        async def post(self, *args, **kwargs):
            return httpx.Response(200, request=httpx.Request("POST", "https://api.openai.com/v1/responses"), json={"output": [{"content": [{"type": "output_text", "text": json.dumps({"Ornn": "Ornn adds frontline and crowd control according to the provided sample factors."})}]}]})
    payload = {"role": "top", "championPool": ["Ornn"]}
    baseline = client.post("/api/analyze", json=payload).json()["recommendations"][0]
    monkeypatch.setenv("EXPLANATION_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "test-only-placeholder")
    monkeypatch.setattr(explanations.httpx, "AsyncClient", SuccessClient)
    data = client.post("/api/analyze", json=payload).json()
    assert data["explanationMode"] == "openai"
    result = data["recommendations"][0]
    for key in baseline:
        if key not in ("explanation", "explanationSource"):
            assert baseline[key] == result[key]

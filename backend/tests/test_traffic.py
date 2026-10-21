from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route
from starlette.testclient import TestClient
from app.services.traffic import TrafficLimits


def test_public_limits_bound_analysis_and_leave_reads_available(monkeypatch):
    monkeypatch.setenv("PUBLIC_TRAFFIC_LIMITS", "true")
    async def respond(request): return JSONResponse({"ok": True})
    app = TrafficLimits(Starlette(routes=[Route("/api/analyze", respond, methods=["POST"]), Route("/api/health", respond)]))
    with TestClient(app) as client:
        for _ in range(20): assert client.post("/api/analyze").status_code == 200
        limited = client.post("/api/analyze")
        assert limited.status_code == 429 and limited.headers["retry-after"] == "60"
        assert client.get("/api/health").status_code == 200
        monkeypatch.setattr("app.services.traffic.time.monotonic", lambda: app.windows["analysis"][-1] + 61)
        assert client.post("/api/analyze").status_code == 200


def test_local_mode_does_not_limit(monkeypatch):
    monkeypatch.delenv("PUBLIC_TRAFFIC_LIMITS", raising=False)
    async def respond(request): return JSONResponse({"ok": True})
    with TestClient(TrafficLimits(Starlette(routes=[Route("/api/analyze", respond, methods=["POST"])]))) as client:
        for _ in range(25): assert client.post("/api/analyze").status_code == 200

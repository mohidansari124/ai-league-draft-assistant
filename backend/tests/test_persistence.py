import json
from fastapi.testclient import TestClient
from app.main import app
from app.database import connection

def test_saved_draft_survives_new_client_and_connection():
    first = TestClient(app)
    payload = {"name":"ADC lane", "draft":{"role":"adc", "championPool":["Draven","Twitch"], "allies":["", "Vi", "", "Lulu"], "enemies":["", "", "", "Jhin"], "laneOpponent":"Jhin", "comfort":{"Draven":5}}}
    saved = first.post("/api/drafts",json=payload)
    assert saved.status_code == 201
    assert "HttpOnly" in saved.headers["set-cookie"]
    with connection() as db:
        assert db.execute("SELECT COUNT(*) FROM drafts").fetchone()[0] == 1
    second = TestClient(app)
    second.cookies.update(first.cookies)
    rows = second.get("/api/drafts").json()
    assert rows[0]["draft"] == payload["draft"]
    assert second.delete("/api/drafts/"+rows[0]["id"]).status_code == 200
    assert first.get("/api/drafts").json() == []

def test_other_browser_cannot_read_or_delete_draft():
    first, other = TestClient(app), TestClient(app)
    row = first.post("/api/drafts",json={"name":"Private", "draft":{"role":"adc","championPool":["Ashe"]}}).json()
    assert other.get("/api/drafts").json() == []
    assert other.delete("/api/drafts/"+row["id"]).status_code == 404
    assert len(first.get("/api/drafts").json()) == 1

def test_draft_validation_and_sql_parameterization():
    client = TestClient(app)
    assert client.post("/api/drafts",json={"name":"   ","draft":{"role":"adc","championPool":["Ashe"]}}).status_code == 422
    assert client.post("/api/drafts",json={"name":"bad","draft":{"role":"adc","championPool":["Fake"]}}).status_code == 422
    assert client.post("/api/drafts",json={"name":"bad","draft":{"role":"adc","championPool":["Ashe"],"enemies":["Jhin"]*6}}).status_code == 422
    name = "Robert'); DROP TABLE drafts;--"
    assert client.post("/api/drafts",json={"name":name,"draft":{"role":"adc","championPool":["Ashe"]}}).status_code == 201
    assert client.get("/api/drafts").json()[0]["name"] == name

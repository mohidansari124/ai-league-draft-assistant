from datetime import datetime, timezone, timedelta
import pytest
from pydantic import ValidationError
from app.database import import_observations, observations_for
from app.models import AnalyzeRequest
from app.services.onetricks import Observation, evidence_for
from app.services.catalog import load_metadata

def record(**changes):
    return {"champion":"Draven","opponent":"Jhin","region":"Unknown","patch":None,"sourceUrl":"https://www.onetricks.gg/champions/counter/Draven","observedAt":datetime.now(timezone.utc).isoformat(),"acquisition":"reviewed public page","notes":"Test fixture; not real provider data.","perspective":"opponent","winRate":.44,"games":500,"goldDiff15":-1000,**changes}

def request(): return AnalyzeRequest(role="adc",championPool=["Draven"],enemies=["Jhin"],laneOpponent="Jhin")

def test_import_idempotency_perspective_and_unknown_patch():
    row = Observation.model_validate(record()).model_dump(mode="json")
    import_observations([row,row])
    assert len(observations_for("Draven","Jhin")) == 1
    evidence = evidence_for("Draven",request())["records"][0]
    assert evidence["winRate"] == .56
    assert evidence["goldDiff15"] == 1000
    assert not evidence["patchMatches"] and not evidence["usedForScoring"]
    assert evidence["build"] is None

@pytest.mark.parametrize("changes", [{"champion":"Jinx"},{"opponent":"Unknown"},{"role":"top"},{"winRate":1.1},{"games":True},{"winRate":float("nan")},{"sourceUrl":"https://evil.example/"},{"sourceUrl":"https://www.onetricks.gg/champions/counter/Ashe"},{"sourceUrl":"https://www.onetricks.gg/champions/counter/Draven?matchup=Ashe"},{"sourceUrl":"https://www.onetricks.gg/champions/counter/Draven?role=top"},{"observedAt":(datetime.now(timezone.utc)+timedelta(days=2)).isoformat()}])
def test_bad_imports_rejected(changes):
    with pytest.raises(ValidationError): Observation.model_validate(record(**changes))

def test_matchup_build_requires_explicit_scope_and_adequate_sample():
    patch = ".".join(load_metadata()["version"].split(".")[:2])
    data = record(perspective="champion",patch=patch,build={"items":["Infinity Edge"],"games":150},sourceUrl="https://www.onetricks.gg/champions/builds/Draven?matchup=Jhin&role=bot")
    observation = Observation.model_validate(data)
    import_observations([observation.model_dump(mode="json")])
    assert evidence_for("Draven",request())["records"][0]["buildEligible"]
    with pytest.raises(ValidationError): Observation.model_validate({**data,"sourceUrl":"https://www.onetricks.gg/champions/builds/Draven"})
    with pytest.raises(ValidationError): Observation.model_validate({**data,"perspective":"opponent"})

def test_old_build_reference_only_and_no_cross_matchup_leak():
    row=record(perspective="champion",patch="1.1",observedAt=(datetime.now(timezone.utc)-timedelta(days=10)).isoformat(),build={"items":["Infinity Edge"],"games":150},sourceUrl="https://www.onetricks.gg/champions/builds/Draven?matchup=Jhin&role=bot")
    import_observations([Observation.model_validate(row).model_dump(mode="json")])
    evidence=evidence_for("Draven",request())["records"][0]
    assert evidence["freshness"] == "stale" and not evidence["buildEligible"]
    other=AnalyzeRequest(role="adc",championPool=["Draven"],enemies=["Ashe"],laneOpponent="Ashe")
    assert evidence_for("Draven",other)["records"] == []

def test_evidence_does_not_change_scores(monkeypatch):
    from fastapi.testclient import TestClient
    from app.main import app
    monkeypatch.setenv("STATS_PROVIDER","disabled")
    monkeypatch.setenv("EXPLANATION_PROVIDER","template")
    client=TestClient(app)
    before=client.post("/api/analyze",json=request().model_dump()).json()
    import_observations([Observation.model_validate(record()).model_dump(mode="json")])
    after=client.post("/api/analyze",json=request().model_dump()).json()
    assert before["recommendations"][0]["score"] == after["recommendations"][0]["score"]
    assert len(after["recommendations"][0]["onetricks"]["records"]) == 1

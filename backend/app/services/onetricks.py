"""Validated, attributed Onetricks observations; no anti-bot bypass or inferred builds."""
from datetime import datetime, timezone, timedelta
from typing import Literal
from urllib.parse import urlparse, parse_qs
from pydantic import BaseModel, ConfigDict, Field, AwareDatetime, model_validator
from app.database import observations_for
from app.models import RunePage
from app.services.adc_advice import FOCUSED_POOL
from app.services.catalog import champions_by_name, load_metadata

class MatchupBuild(BaseModel):
    model_config = ConfigDict(extra="forbid")
    items: list[str] = Field(min_length=1, max_length=6)
    runes: RunePage | None = None
    games: int = Field(ge=1, strict=True)

class Observation(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    champion: str
    opponent: str
    role: Literal["adc"] = "adc"
    patch: str | None = Field(default=None, pattern=r"^\d+\.\d+$")
    region: str = Field(min_length=1, max_length=100)
    cohort: Literal["high-elo champion specialists"] = "high-elo champion specialists"
    sourceUrl: str
    observedAt: AwareDatetime
    acquisition: Literal["reviewed public page", "authorized export"]
    notes: str = Field(max_length=600)
    perspective: Literal["champion", "opponent"]
    winRate: float | None = Field(default=None, ge=0, le=1)
    games: int | None = Field(default=None, ge=1, strict=True)
    goldDiff15: float | None = None
    build: MatchupBuild | None = None

    @model_validator(mode="after")
    def validate_scope(self):
        catalog = champions_by_name()
        if self.champion not in FOCUSED_POOL or self.opponent not in catalog or self.champion == self.opponent:
            raise ValueError("Expected a focused ADC champion and a different known opponent.")
        url = urlparse(self.sourceUrl)
        expected = catalog[self.champion]["id"]
        if url.scheme != "https" or url.netloc != "www.onetricks.gg" or url.fragment or url.username:
            raise ValueError("Source must be an HTTPS www.onetricks.gg page.")
        if url.path not in (f"/champions/counter/{expected}", f"/champions/builds/{expected}"):
            raise ValueError("Source URL must match the selected champion.")
        query = parse_qs(url.query)
        if query.get("matchup") and query["matchup"] != [catalog[self.opponent]["id"]]:
            raise ValueError("Source matchup does not match opponent.")
        if query.get("role") and query["role"] != ["bot"]:
            raise ValueError("Source role must be bot.")
        if (self.winRate is None) != (self.games is None):
            raise ValueError("Match win rate and game count must be supplied together.")
        if self.winRate is None and self.build is None:
            raise ValueError("An observation needs matchup statistics or a build.")
        if self.goldDiff15 is not None and self.winRate is None:
            raise ValueError("Gold difference requires a matchup sample.")
        if self.observedAt > datetime.now(timezone.utc) + timedelta(minutes=5):
            raise ValueError("Observation cannot be dated in the future.")
        if self.build:
            if self.perspective != "champion" or self.patch is None:
                raise ValueError("Builds require champion perspective and a known patch.")
            if not url.path.startswith("/champions/builds/") or query.get("matchup") != [catalog[self.opponent]["id"]] or query.get("role") != ["bot"]:
                raise ValueError("Build source must explicitly identify the bot matchup.")
            if any(not item.strip() or len(item)>100 for item in self.build.items):
                raise ValueError("Invalid item name.")
            if self.build.runes and (len(self.build.runes.runes)!=5 or len(self.build.runes.shards)!=3):
                raise ValueError("Rune pages require five minor runes and three shards.")
        return self

def evidence_for(champion, request):
    if request.role != "adc" or champion not in FOCUSED_POOL:
        return None
    cid = champions_by_name()[champion]["id"]
    records = observations_for(champion, request.laneOpponent) if request.laneOpponent else []
    normalized = []
    patch = ".".join((load_metadata().get("version") or "").split(".")[:2])
    for raw in records:
        observation = Observation.model_validate(raw)
        r = observation.model_dump(mode="json")
        r["reportedPerspective"] = r.pop("perspective")
        if observation.perspective == "opponent":
            if r["winRate"] is not None: r["winRate"] = round(1-r["winRate"], 6)
            if r["goldDiff15"] is not None: r["goldDiff15"] = -r["goldDiff15"]
        age = datetime.now(timezone.utc) - observation.observedAt
        r["freshness"] = "stale" if age > timedelta(days=7) else "recent review"
        r["patchMatches"] = observation.patch is not None and observation.patch == patch
        r["buildEligible"] = bool(observation.build and observation.build.games >= 100 and r["patchMatches"] and age <= timedelta(days=7))
        r["usedForScoring"] = False
        normalized.append(r)
    return {"source":"Onetricks.gg", "status":"imported" if records else "unavailable", "opponent":request.laneOpponent,
        "buildUrl":f"https://www.onetricks.gg/champions/builds/{cid}",
        "counterUrl":f"https://www.onetricks.gg/champions/counter/{cid}", "records":normalized,
        "notice":"Reviewed snapshots, not a live feed. Specialist-player outcomes are not comparable to all-rank averages; they do not change your draft score. Matchup builds appear only when explicitly imported for this opponent."}

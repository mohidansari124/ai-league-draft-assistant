from typing import Literal
from pydantic import BaseModel, Field, StrictInt, model_validator

Role = Literal["top", "jungle", "mid", "adc", "support"]

class AnalyzeRequest(BaseModel):
    role: Role
    championPool: list[str] = Field(min_length=1, max_length=250)
    allies: list[str] = Field(default_factory=list, max_length=4)
    enemies: list[str] = Field(default_factory=list, max_length=5)
    laneOpponent: str | None = None
    comfort: dict[str, StrictInt] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_draft(self):
        for field in ("championPool", "allies", "enemies"):
            values = getattr(self, field)
            if len(values) != len(set(values)):
                raise ValueError(f"{field} cannot contain duplicate champions.")
        if set(self.allies) & set(self.enemies):
            raise ValueError("A champion cannot appear on both teams.")
        if self.laneOpponent and self.laneOpponent not in self.enemies:
            raise ValueError("Lane opponent must be on the enemy team.")
        if self.role == "jungle" and self.laneOpponent:
            raise ValueError("Use the enemy team for jungle threats; junglers have no lane opponent.")
        if any(type(v) is not int or not 1 <= v <= 5 for v in self.comfort.values()):
            raise ValueError("Comfort values must be integers from 1 to 5.")
        if set(self.comfort) - set(self.championPool):
            raise ValueError("Comfort can only be set for champions in your pool.")
        return self

class Factor(BaseModel):
    key: str
    label: str
    points: float
    maximum: int
    reason: str

class Matchup(BaseModel):
    opponent: str | None
    rating: str
    known: bool
    explanation: str
    source: str = "sample"
    winRate: float | None = None
    games: int | None = None

class BuildItem(BaseModel):
    name: str
    reason: str

class RunePage(BaseModel):
    primary: str
    secondary: str
    keystone: str
    runes: list[str]
    shards: list[str]

class ChampionStatistics(BaseModel):
    source: str
    sourceUrl: str
    role: str
    patch: str | None
    tier: str
    region: str
    queue: str
    winRate: float
    games: int
    fetchedAt: str
    sourceUpdatedAt: str | None = None
    status: str
    usedForScoring: bool = False

class AdviceSource(BaseModel):
    title: str
    url: str

class AdviceNote(BaseModel):
    title: str
    text: str
    sources: list[AdviceSource]

class AdcAdvice(BaseModel):
    identity: str
    reviewedAt: str
    basis: str
    opponentCovered: bool
    coverage: str
    notes: list[AdviceNote]
    decisions: list[str]
    limitations: str

class Recommendation(BaseModel):
    champion: str
    score: float
    rank: int = 0
    factors: list[Factor]
    explanation: str
    matchup: Matchup
    runes: RunePage
    coreItems: list[BuildItem]
    situationalItems: list[BuildItem]
    gamePlan: list[str]
    explanationSource: str = "template"
    statistics: ChampionStatistics | None = None
    buildSource: str = "Sample guide"
    runeSource: str = "Sample guide"
    traitSource: str = "curated sample"
    adcAdvice: AdcAdvice | None = None
    onetricks: dict | None = None

class Composition(BaseModel):
    traits: dict[str, float]
    physicalShare: float | None
    strengths: list[str]
    needs: list[str]
    unratedChampions: list[str] = Field(default_factory=list)

class AnalysisResponse(BaseModel):
    recommendations: list[Recommendation]
    composition: Composition
    warnings: list[str]
    excluded: list[str]
    dataVersion: str
    scoringVersion: str = "2.0"
    explanationMode: str = "template"
    statisticsMode: str = "heuristic"


class SavedDraftInput(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    draft: dict

    @model_validator(mode="after")
    def check_draft(self):
        from app.services.catalog import champions_by_name
        self.name = self.name.strip()
        if not self.name:
            raise ValueError("Give your draft a name.")
        # Preserve empty UI role slots in storage; validate the compact API form.
        if set(self.draft) - {"role", "championPool", "allies", "enemies", "laneOpponent", "comfort"}:
            raise ValueError("Unknown draft field.")
        compact = dict(self.draft)
        for key, limit in (("allies",4),("enemies",5)):
            value = compact.get(key, [])
            if not isinstance(value,list) or len(value)>limit or any(not isinstance(n,str) for n in value):
                raise ValueError("Invalid team slots.")
            compact[key] = [n for n in value if n]
        request = AnalyzeRequest.model_validate(compact)
        names = set(request.championPool + request.allies + request.enemies)
        if names - champions_by_name().keys():
            raise ValueError("Unknown champion in saved draft.")
        self.draft = {**request.model_dump(), "allies":self.draft.get("allies",[]), "enemies":self.draft.get("enemies",[])}
        return self

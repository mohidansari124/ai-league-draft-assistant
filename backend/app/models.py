from typing import Literal
from pydantic import BaseModel, Field, StrictInt, model_validator

Role = Literal["top", "jungle", "mid", "adc", "support"]

class AnalyzeRequest(BaseModel):
    role: Role
    championPool: list[str] = Field(min_length=1, max_length=40)
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

class BuildItem(BaseModel):
    name: str
    reason: str

class RunePage(BaseModel):
    primary: str
    secondary: str
    keystone: str
    runes: list[str]
    shards: list[str]

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

class Composition(BaseModel):
    traits: dict[str, float]
    physicalShare: float | None
    strengths: list[str]
    needs: list[str]

class AnalysisResponse(BaseModel):
    recommendations: list[Recommendation]
    composition: Composition
    warnings: list[str]
    excluded: list[str]
    dataVersion: str
    scoringVersion: str = "1.0"
    explanationMode: str = "template"

import os
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.staticfiles import StaticFiles
import hashlib
import secrets
import re
from app import database
from app.services.traffic import TrafficLimits
from app.services.onetricks import evidence_for
from fastapi.middleware.cors import CORSMiddleware
from app.models import AnalyzeRequest, AnalysisResponse, SavedDraftInput
from app.services.catalog import public_catalog, champions_by_name
from app.services.opgg import fetch_pool_stats
from app.services.scoring import analyze
from app.services.explanations import add_explanations

load_dotenv(Path(__file__).resolve().parents[2] / ".env")
app = FastAPI(title="Draftwise — AI League Draft Assistant", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=[s.strip() for s in os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")], allow_credentials=True, allow_methods=["GET", "POST", "DELETE"], allow_headers=["Content-Type"])

app.add_middleware(TrafficLimits)

@app.get("/api/health")
def health():
    return {"status": "ok", "scoringVersion": "2.0"}

@app.get("/api/champions")
def champions():
    return public_catalog()

@app.post("/api/analyze", response_model=AnalysisResponse)
async def analyze_draft(request: AnalyzeRequest):
    try:
        # Validate locally before making any external request.
        analyze(request)
        catalog = champions_by_name()
        eligible = [name for name in request.championPool if request.role in catalog[name]["roles"] and name not in request.allies + request.enemies]
        statistics, warnings = await fetch_pool_stats(eligible, request.role)
        result = analyze(request, statistics, statistics_requested=os.getenv("STATS_PROVIDER", "opgg") == "opgg")
        result.warnings.extend(warnings)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    for recommendation in result.recommendations:
        recommendation.onetricks = evidence_for(recommendation.champion, request)
    return await add_explanations(result)


def draft_owner(request: Request, response: Response, create=False):
    token = request.cookies.get("draftwise_owner", "")
    if not re.fullmatch(r"[0-9a-f]{64}", token):
        if not create: return None
        token = secrets.token_hex(32)
        response.set_cookie("draftwise_owner", token, httponly=True, samesite="strict", secure=os.getenv("COOKIE_SECURE", "false").lower()=="true", max_age=60*60*24*365, path="/api")
    return hashlib.sha256(token.encode()).hexdigest()

@app.get("/api/drafts")
def saved_drafts(request: Request, response: Response):
    owner = draft_owner(request, response)
    response.headers["Cache-Control"] = "no-store"
    return database.list_drafts(owner) if owner else []

@app.post("/api/drafts", status_code=201)
def save_draft(payload: SavedDraftInput, request: Request, response: Response):
    owner = draft_owner(request, response, create=True)
    response.headers["Cache-Control"] = "no-store"
    try:
        return database.save_draft(owner, payload.name, payload.draft)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

@app.delete("/api/drafts/{identifier}")
def delete_draft(identifier: str, request: Request, response: Response):
    owner = draft_owner(request, response)
    if not owner or not database.delete_draft(owner, identifier):
        raise HTTPException(status_code=404, detail="Draft not found.")
    return {"deleted":True}

# The production container serves the compiled React application on the API origin.
# API routes above retain precedence; this application has no client-side URL routes.
frontend_dist = Path(os.getenv("FRONTEND_DIST", str(Path(__file__).resolve().parents[2] / "frontend" / "dist")))
if frontend_dist.is_dir():
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="frontend")

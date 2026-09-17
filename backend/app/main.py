import os
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.models import AnalyzeRequest, AnalysisResponse
from app.services.catalog import public_catalog
from app.services.scoring import analyze
from app.services.explanations import add_explanations

load_dotenv(Path(__file__).resolve().parents[2] / ".env")
app = FastAPI(title="Draftwise — AI League Draft Assistant", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=[s.strip() for s in os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")], allow_methods=["GET", "POST"], allow_headers=["Content-Type"])

@app.get("/api/health")
def health():
    return {"status": "ok", "scoringVersion": "1.0"}

@app.get("/api/champions")
def champions():
    return public_catalog()

@app.post("/api/analyze", response_model=AnalysisResponse)
async def analyze_draft(request: AnalyzeRequest):
    try:
        result = analyze(request)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return await add_explanations(result)

"""Optional AI changes prose only. Ranking, factors and builds remain deterministic."""
import json
import os
import httpx
from app.models import AnalysisResponse

async def add_explanations(analysis: AnalysisResponse) -> AnalysisResponse:
    if os.getenv("EXPLANATION_PROVIDER", "template") != "openai" or not os.getenv("OPENAI_API_KEY"):
        return analysis
    facts = [{"champion": r.champion, "score": r.score, "factors": [f.model_dump() for f in r.factors], "matchup": r.matchup.model_dump()} for r in analysis.recommendations]
    try:
        async with httpx.AsyncClient(timeout=12) as client:
            response = await client.post("https://api.openai.com/v1/responses", headers={"Authorization": "Bearer " + os.environ["OPENAI_API_KEY"]}, json={
                "model": os.getenv("OPENAI_MODEL", "gpt-4.1-mini"), "store": False,
                "instructions": "Explain educational League draft scores using ONLY the supplied facts. Do not add statistics, claim patch accuracy, change scores, or guarantee outcomes. Return a JSON object mapping each exact champion name to one concise paragraph. State matchup uncertainty where supplied.",
                "input": json.dumps(facts), "text": {"format": {"type": "json_object"}}, "max_output_tokens": 700})
            response.raise_for_status()
            output = response.json()
            text = "".join(c.get("text", "") for o in output.get("output", []) for c in o.get("content", []) if c.get("type") == "output_text")
            paragraphs = json.loads(text)
            if not isinstance(paragraphs, dict) or any(not isinstance(paragraphs.get(r.champion), str) or not 20 <= len(paragraphs[r.champion]) <= 2000 for r in analysis.recommendations):
                raise ValueError("Invalid explanation response")
        for result in analysis.recommendations:
            result.explanation = paragraphs[result.champion]
            result.explanationSource = "openai"
        analysis.explanationMode = "openai"
    except (httpx.HTTPError, ValueError, KeyError, TypeError, AttributeError):
        analysis.warnings.append("AI explanations were unavailable. Deterministic explanations are shown; scores are unchanged.")
    return analysis

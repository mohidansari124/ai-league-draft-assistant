"""Small, attributed advice library. Never supplies statistical scoring inputs."""
import json
from functools import lru_cache
from app.services.catalog import DATA_DIR

FOCUSED_POOL = ("Draven", "Twitch", "Caitlyn", "Ashe")

@lru_cache
def library():
    return json.loads((DATA_DIR / "adc_advice.json").read_text(encoding="utf-8"))

def source(name, kind):
    slug = name.lower().replace("'", "").replace(" ", "")
    return {"title": f"Mobalytics: {name} {kind}", "url": f"https://mobalytics.gg/lol/champions/{slug}/{kind}"}

def advice_for(name, request):
    if request.role != "adc" or name not in FOCUSED_POOL:
        return None
    data = library()
    profile = data["profiles"][name]
    notes = [{"title": "Your lane plan", "text": profile["lane"], "sources": [source(name, "guide")]}]
    opponent = request.laneOpponent
    covered = opponent in data["opponents"] and opponent != name
    if covered:
        notes.append({"title": f"Against {opponent}", "text": data["opponents"][opponent], "sources": [source(opponent, "counters")]})
    for enemy in request.enemies:
        if enemy in data["threats"]:
            notes.append({"title": f"Enemy threat: {enemy}", "text": data["threats"][enemy], "sources": [source(enemy, "counters")]})
    notes.append({"title": "After lane", "text": profile["teamfight"], "sources": [source(name, "guide")]})
    # This is explicit app-authored decision guidance, not attributed matchup build data.
    decisions = [profile["decision"],
        "The displayed OP.GG items and runes describe this champion's ADC games overall, not this particular opponent. Keep their source label in mind when adapting the build.",
        "Check both supports before choosing aggression or sustain. This library does not yet recommend matchup-specific item orders or rune substitutions."]
    return {"identity": profile["identity"], "reviewedAt": data["reviewedAt"], "basis": data["basis"],
            "opponentCovered": covered, "coverage": f"Mechanics notes for {opponent}; combined with your champion's plan, not a separately validated pair guide." if covered else "No reviewed opponent notes for this selection. Showing your champion's general plan only.",
            "notes": notes, "decisions": decisions,
            "limitations": "Supports and wave state can change the lane. These summaries do not change the score or establish a winning matchup. No live community feed is connected."}

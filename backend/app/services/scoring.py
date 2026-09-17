"""Pure, deterministic scoring. All ratings are educational sample heuristics."""
from app.models import AnalyzeRequest, AnalysisResponse, Composition, Factor, Matchup, Recommendation
from app.services.catalog import champions_by_name, load_catalog, load_guides

WEIGHTS = {"comfort": 15, "matchup": 20, "frontline": 10, "engage": 7, "peel": 7,
           "balance": 10, "control": 7, "scaling": 7, "synergy": 7, "threats": 10}
TARGETS = {"frontline": 4, "engage": 4, "peel": 4, "control": 5, "scaling": 7}
LABELS = {"comfort": "Champion comfort", "matchup": "Lane matchup", "frontline": "Frontline",
          "engage": "Engage", "peel": "Carry protection", "balance": "Damage balance",
          "control": "Crowd control", "scaling": "Scaling", "synergy": "Ally synergy", "threats": "Enemy threats"}

def clamp(value):
    return max(0.0, min(1.0, value))

def composition(champions):
    totals = {key: sum(c["traits"][key] for c in champions) for key in TARGETS}
    strengths = [LABELS[k] for k, target in TARGETS.items() if totals[k] >= target]
    needs = [LABELS[k] for k, target in TARGETS.items() if totals[k] < target]
    return Composition(traits=totals, physicalShare=(sum(c["physicalShare"] for c in champions) / len(champions) if champions else None), strengths=strengths, needs=needs)

def matchup_for(name, opponent):
    if not opponent:
        return Matchup(opponent=None, rating="Not selected", known=False, explanation="No lane opponent selected. Matchup contributes a neutral 10 / 20 points.")
    data = load_catalog()["matchups"].get(f"{name}|{opponent}")
    if not data:
        return Matchup(opponent=opponent, rating="Unrated", known=False, explanation=f"No curated matchup entry for {name} into {opponent}. Neutral 10 / 20 points; this is not evidence of an even lane.")
    rating = "Favorable" if data["value"] > .25 else "Difficult" if data["value"] < -.25 else "Close"
    return Matchup(opponent=opponent, rating=rating, known=True, explanation=data["text"])

def situational_items(champion, enemies, core):
    if not enemies:
        return [{"name": "Boots choice", "reason": "Choose defensive boots after enemy damage and crowd control are known."}]
    physical = sum(c["physicalShare"] for c in enemies) / len(enemies)
    archetype = champion["archetype"]
    durable = archetype in ("tank", "tank-support", "fighter", "ap-fighter")
    items = []
    if physical >= .6:
        items.append({"name": "Plated Steelcaps", "reason": "Enemy sample profiles lean toward physical damage; consider these especially against basic attacks. They do not stop true damage."})
    else:
        items.append({"name": "Mercury’s Treads", "reason": "Consider magic resistance and tenacity against magic damage and reducible crowd control. Tenacity does not shorten knock-ups."})
    if any("healing" in c["tags"] for c in enemies):
        name = "Thornmail" if archetype in ("tank", "tank-support") else "Morellonomicon" if champion["physicalShare"] < .4 else "Mortal Reminder" if archetype == "marksman" else "Chempunk Chainsword"
        items.append({"name": name, "reason": "Enemy profiles include healing. Coordinate an anti-heal purchase with your team; check how the item applies it."})
    if any("dive" in c["tags"] for c in enemies):
        name = "Zhonya’s Hourglass" if archetype in ("mage", "ap-fighter", "ap-assassin") else "Guardian Angel" if archetype in ("marksman", "ad-assassin", "fighter") else "Locket of the Iron Solari" if archetype == "enchanter" else "Randuin’s Omen"
        items.append({"name": name, "reason": "Enemy divers can reach your backline. Consider a defensive purchase when their burst or critical strikes are the main threat."})
    if physical < .4 and durable:
        items.append({"name": "Force of Nature", "reason": "Consider additional magic resistance against sustained magic damage."})
    core_names = {item["name"] for item in core}
    return [item for item in items if item["name"] not in core_names]

def analyze(request: AnalyzeRequest) -> AnalysisResponse:
    catalog, by_name, guides = load_catalog(), champions_by_name(), load_guides()
    unknown = (set(request.championPool) | set(request.allies) | set(request.enemies)) - by_name.keys()
    if unknown:
        raise ValueError("Unsupported champions: " + ", ".join(sorted(unknown)))
    taken = set(request.allies + request.enemies)
    excluded = [name for name in request.championPool if name in taken or request.role not in by_name[name]["roles"]]
    candidates = [by_name[name] for name in request.championPool if name not in excluded]
    if not candidates:
        raise ValueError("No available champions fit this role. Add an unpicked champion supported in your selected role.")
    allies, enemies = [by_name[n] for n in request.allies], [by_name[n] for n in request.enemies]
    comp = composition(allies)
    results = []
    for c in candidates:
        factors = []
        def add(key, value, reason):
            factors.append(Factor(key=key, label=LABELS[key], points=round(clamp(value) * WEIGHTS[key], 2), maximum=WEIGHTS[key], reason=reason))
        comfort = request.comfort.get(c["name"], 3)
        add("comfort", comfort / 5, f"Your comfort rating is {comfort} / 5. Unrated champions default to 3.")
        matchup = matchup_for(c["name"], request.laneOpponent)
        entry = catalog["matchups"].get(f"{c['name']}|{request.laneOpponent}", {"value": 0})
        add("matchup", (entry["value"] + 1) / 2, matchup.explanation)
        for key, target in TARGETS.items():
            need = clamp((target - comp.traits[key]) / target)
            # Half credit is neutral. Only an unmet team need earns a trait bonus.
            add(key, .5 + .5 * need * c["traits"][key] / 3,
                f"Allies supply {comp.traits[key]:g} / {target} target units; {c['name']} adds {c['traits'][key]} / 3. " + ("Existing picks already cover this need." if need == 0 else "Filling this gap earns additional credit."))
        share = (sum(a["physicalShare"] for a in allies) + c["physicalShare"]) / (len(allies) + 1)
        add("balance", 1 - abs(share - .5) * 2, f"Estimated team damage profile with this pick: {share:.0%} physical, {1-share:.0%} magic. Equal champion weighting; not a damage forecast.")
        synergies = []
        for ally in allies:
            tip = catalog["synergies"].get(f"{c['name']}|{ally['name']}") or catalog["synergies"].get(f"{ally['name']}|{c['name']}")
            if tip: synergies.append(tip)
        add("synergy", min(1, .5 + .25 * len(synergies)), " ".join(synergies) if synergies else "No curated pair synergy found. Neutral credit; absence is not a weakness.")
        threat_fit = .5
        reasons = []
        if enemies:
            physical = sum(e["physicalShare"] for e in enemies) / len(enemies)
            if physical >= .6 and "armor" in c["tags"]:
                threat_fit += .3; reasons.append("Armor-oriented kit fits the physical-heavy enemy profiles; it does not counter true damage.")
            if any("dive" in e["tags"] for e in enemies):
                threat_fit += .2 * c["traits"]["peel"] / 3; reasons.append(f"Peel rating {c['traits']['peel']} / 3 helps answer enemy divers.")
            if any(e["traits"]["frontline"] == 3 for e in enemies) and "isolate" in c["tags"]:
                threat_fit += .15; reasons.append("Isolation can disrupt a frontline-led fight if used at the right time.")
        add("threats", threat_fit, " ".join(reasons) or "No specific threat interaction found in the sample rules. Neutral credit.")
        guide = guides[c["name"]]
        notable = sorted([f for f in factors if f.key != "matchup"], key=lambda f: f.points / f.maximum, reverse=True)[:2]
        explanation = f"{c['name']} fits this draft through {notable[0].label.lower()} and {notable[1].label.lower()}. {notable[0].reason} " + (synergies[0] if synergies else notable[1].reason)
        plan = [matchup.explanation if request.laneOpponent else "Track enemy positions and avoid committing without vision. Use early time to secure safe farm and information."]
        plan.append("Coordinate initiation with your team, then use crowd control to create space for allied damage." if c["traits"]["engage"] >= 2 else "Play around your team's initiation and preserve your defensive cooldowns before committing damage.")
        plan.append("Protect your carry and contest objectives together once lanes converge." if c["traits"]["peel"] >= 2 else "Fight from a safe angle around objectives; adapt between side-lane pressure and grouping based on your team's position.")
        results.append(Recommendation(champion=c["name"], score=round(sum(f.points for f in factors), 2), factors=factors, explanation=explanation, matchup=matchup, runes=guide["runes"], coreItems=guide["coreItems"], situationalItems=situational_items(c, enemies, guide["coreItems"]), gamePlan=plan))
    results.sort(key=lambda r: (-r.score, r.champion))
    for i, result in enumerate(results[:3], 1): result.rank = i
    warnings = [catalog["notice"], "Scores describe draft fit, not win probability. Recommendations are suggestions, not guaranteed outcomes."]
    if len(allies) < 4 or len(enemies) < 5: warnings.append("Partial draft: scores may change as more champions are picked.")
    if excluded: warnings.append("Excluded already-picked or role-incompatible pool champions: " + ", ".join(excluded))
    if len(results) < 3: warnings.append(f"Only {len(results)} eligible champion(s) available; showing all eligible picks.")
    return AnalysisResponse(recommendations=results[:3], composition=comp, warnings=warnings, excluded=excluded, dataVersion=catalog["version"])

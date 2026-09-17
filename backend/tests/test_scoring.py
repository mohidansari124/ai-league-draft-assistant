import pytest
from app.models import AnalyzeRequest
from app.services.scoring import analyze, WEIGHTS
from app.services.catalog import champions_by_name

DEMO = dict(role="top", championPool=["Ornn", "Garen", "Malphite", "Mordekaiser"], allies=["Jarvan IV", "Orianna", "Jinx", "Lulu"], enemies=["Darius", "Lee Sin", "Zed", "Samira", "Nautilus"], laneOpponent="Darius")

def test_demo_is_deterministic_ranked_and_explained():
    a = analyze(AnalyzeRequest(**DEMO))
    assert a == analyze(AnalyzeRequest(**DEMO))
    assert len(a.recommendations) == 3
    assert [r.rank for r in a.recommendations] == [1, 2, 3]
    assert [r.score for r in a.recommendations] == sorted([r.score for r in a.recommendations], reverse=True)
    for r in a.recommendations:
        assert r.champion in DEMO["championPool"]
        assert 0 <= r.score <= 100
        assert r.score == round(sum(f.points for f in r.factors), 2)
        assert sum(f.maximum for f in r.factors) == sum(WEIGHTS.values()) == 100
        assert r.matchup.known and r.matchup.opponent == "Darius"
        assert r.explanation and r.gamePlan and len(r.coreItems) == 3
        assert len(r.runes.runes) == 5 and len(r.runes.shards) == 3

def test_comfort_changes_only_comfort_points():
    low = analyze(AnalyzeRequest(role="top", championPool=["Ornn"], comfort={"Ornn": 1})).recommendations[0]
    high = analyze(AnalyzeRequest(role="top", championPool=["Ornn"], comfort={"Ornn": 5})).recommendations[0]
    assert high.score - low.score == pytest.approx(12)
    assert low.factors[1:] == high.factors[1:]

def test_unknown_matchup_is_neutral_and_honest():
    result = analyze(AnalyzeRequest(role="top", championPool=["Ornn"], enemies=["Camille"], laneOpponent="Camille")).recommendations[0]
    assert not result.matchup.known
    assert result.matchup.rating == "Unrated"
    assert next(f.points for f in result.factors if f.key == "matchup") == 10

def test_picked_and_wrong_role_champions_are_excluded():
    response = analyze(AnalyzeRequest(role="top", championPool=["Ornn", "Garen", "Jinx"], allies=["Garen"]))
    assert [r.champion for r in response.recommendations] == ["Ornn"]
    assert set(response.excluded) == {"Garen", "Jinx"}
    assert any("Only 1" in w for w in response.warnings)

def test_no_eligible_champions_errors():
    with pytest.raises(ValueError, match="No available"):
        analyze(AnalyzeRequest(role="top", championPool=["Jinx"]))

def test_unknown_champion_errors():
    with pytest.raises(ValueError, match="Unsupported"):
        analyze(AnalyzeRequest(role="top", championPool=["MadeUp"]))

def test_frontline_gap_rewards_tank_more_than_fighter():
    result = analyze(AnalyzeRequest(role="top", championPool=["Ornn", "Garen"], allies=["Jinx", "Lulu", "Orianna"]))
    values = {r.champion: next(f.points for f in r.factors if f.key == "frontline") for r in result.recommendations}
    assert values["Ornn"] > values["Garen"]

def test_physical_threats_reward_armor_profile():
    base = dict(role="top", championPool=["Malphite"])
    physical = analyze(AnalyzeRequest(**base, enemies=["Jinx", "Zed", "Darius"])).recommendations[0]
    magical = analyze(AnalyzeRequest(**base, enemies=["Orianna", "Lux", "Syndra"])).recommendations[0]
    points = lambda r: next(f.points for f in r.factors if f.key == "threats")
    assert points(physical) > points(magical)
    assert any(i.name == "Plated Steelcaps" for i in physical.situationalItems)

def test_draft_order_does_not_change_ranking():
    a = analyze(AnalyzeRequest(**DEMO))
    b = analyze(AnalyzeRequest(**{**DEMO, "championPool": list(reversed(DEMO["championPool"]))}))
    assert a.recommendations == b.recommendations

@pytest.mark.parametrize("role", ["top", "jungle", "mid", "adc", "support"])
def test_all_roles_have_complete_guides(role):
    pool = [name for name, c in champions_by_name().items() if role in c["roles"]]
    response = analyze(AnalyzeRequest(role=role, championPool=pool))
    assert len(response.recommendations) == 3
    assert all(0 <= r.score <= 100 for r in response.recommendations)
    assert all(len(r.runes.runes) == 5 for r in response.recommendations)

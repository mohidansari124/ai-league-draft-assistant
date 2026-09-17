import pytest
from app.models import AnalyzeRequest
from app.services.adc_advice import advice_for, library, FOCUSED_POOL
from app.services.scoring import analyze

@pytest.mark.parametrize("name", FOCUSED_POOL)
def test_each_adc_has_grounded_advice_without_invented_statistics(name):
    request = AnalyzeRequest(role="adc", championPool=[name], enemies=["Jhin", "Nautilus"], laneOpponent="Jhin")
    result = analyze(request, statistics_requested=True).recommendations[0]
    assert result.adcAdvice.opponentCovered
    assert any(n.title == "Enemy threat: Nautilus" for n in result.adcAdvice.notes)
    assert all(n.sources for n in result.adcAdvice.notes)
    assert result.matchup.winRate is None
    assert next(f.points for f in result.factors if f.key == "matchup") == 10

@pytest.mark.parametrize("name", FOCUSED_POOL)
def test_all_reviewed_opponents_have_correct_source_and_perspective(name):
    for opponent in library()["opponents"]:
        if opponent == name: continue
        request = AnalyzeRequest(role="adc", championPool=[name], enemies=[opponent], laneOpponent=opponent)
        advice = advice_for(name, request)
        assert advice["opponentCovered"]
        assert advice["notes"][1]["title"] == f"Against {opponent}"
        assert advice["notes"][1]["sources"][0]["url"].endswith("/counters")

@pytest.mark.parametrize("opponent", [None, "Ziggs"])
def test_missing_coverage_is_explicit(opponent):
    request = AnalyzeRequest(role="adc", championPool=["Draven"], enemies=[opponent] if opponent else [], laneOpponent=opponent)
    advice = advice_for("Draven", request)
    assert not advice["opponentCovered"]
    assert "No reviewed opponent notes" in advice["coverage"]
    assert len(advice["notes"]) == 2

def test_only_focused_adc_pool_gets_four_results():
    result = analyze(AnalyzeRequest(role="adc",championPool=list(FOCUSED_POOL)))
    assert len(result.recommendations) == 4
    assert {r.rank for r in result.recommendations} == {1,2,3,4}
    other = analyze(AnalyzeRequest(role="adc",championPool=[*FOCUSED_POOL, "Jinx"]))
    assert len(other.recommendations) == 3

def test_picked_champion_still_excluded():
    result = analyze(AnalyzeRequest(role="adc",championPool=list(FOCUSED_POOL),enemies=["Ashe"],laneOpponent="Ashe"))
    assert len(result.recommendations) == 3
    assert "Ashe" in result.excluded
    assert all(r.adcAdvice.opponentCovered for r in result.recommendations)

def test_advice_is_role_gated():
    assert advice_for("Ashe", AnalyzeRequest(role="support",championPool=["Ashe"])) is None
    assert advice_for("Jinx", AnalyzeRequest(role="adc",championPool=["Jinx"])) is None

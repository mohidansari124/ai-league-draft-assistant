import asyncio
import json
from datetime import datetime, timezone, timedelta
import pytest
from app.services import opgg
from app.services.catalog import champions_by_name, load_metadata
from app.services.scoring import analyze, empirical_fit
from app.models import AnalyzeRequest


def stats(name="Ornn", **changes):
    return {"champion":name,"role":"top","source":"OP.GG","sourceUrl":"https://op.gg/lol/champions/ornn/build/top","patch":".".join(load_metadata()["version"].split(".")[:2]),"tier":"all","region":"Provider default (not exposed)","queue":"ranked","winRate":.54,"games":5000,"fetchedAt":datetime.now(timezone.utc).isoformat(),"sourceUpdatedAt":None,"status":"live","matchups":{},"coreItems":None,"runes":None,**changes}


def test_compact_parser_decodes_nested_data_without_execution():
    data=opgg.decode_compact('class Response: data\nclass Row: name,rate\n\nResponse([Row("Ornn",0.51),Row("Kai\\\'Sa",0.5)])'.replace('\\\'','\''))
    assert data["data"][0] == {"name":"Ornn","rate":.51}


@pytest.mark.parametrize("text", ['__import__("os").system("whoami")','class Data: x\nData(open("secret"))','class Data: x\nData([v for v in []])','class Data: x\nData(1,2)'])
def test_compact_parser_rejects_executable_or_invalid_expressions(text):
    with pytest.raises((ValueError,SyntaxError)):opgg.decode_compact(text)


def test_provider_data_actually_changes_the_ranking():
    request=AnalyzeRequest(role="mid",championPool=["Akali","Akshan"])
    good=analyze(request,{"Akali":stats("Akali",role="mid",winRate=.55),"Akshan":stats("Akshan",role="mid",winRate=.45)},True)
    bad=analyze(request,{"Akali":stats("Akali",role="mid",winRate=.45),"Akshan":stats("Akshan",role="mid",winRate=.55)},True)
    assert good.recommendations[0].champion == "Akali"
    assert bad.recommendations[0].champion == "Akshan"


def test_weak_counter_rate_is_from_selected_champion_perspective():
    raw={"champion":"ORNN","position":"TOP","data":{"summary":{"positions":[{"name":"TOP","stats":{"play":1000,"win_rate":.51}}]},"weak_counters":[{"champion_name":"Darius","play":500,"my_win_rate":.42,"counter_win_rate":.58}],"trends":{"win":{"version":"16.18"}}}}
    normalized=opgg.normalize(raw,"Ornn","top",datetime.now(timezone.utc).isoformat())
    assert normalized["matchups"]["Darius"]["winRate"] == .42
    result=analyze(AnalyzeRequest(role="top",championPool=["Ornn"],enemies=["Darius"],laneOpponent="Darius"),{"Ornn":normalized},True).recommendations[0]
    assert result.matchup.source == "OP.GG"
    assert next(f.points for f in result.factors if f.key == "matchup") < 10


@pytest.mark.parametrize("changes",[{"patch":"1.1"},{"patch":None},{"games":99}])
def test_wrong_patch_and_small_samples_get_neutral_credit(changes):
    result=analyze(AnalyzeRequest(role="top",championPool=["Ornn"]),{"Ornn":stats(**changes)},True).recommendations[0]
    assert not result.statistics.usedForScoring
    assert next(f.points for f in result.factors if f.key == "performance") == 5
    assert not result.buildSource.startswith("OP.GG")


def test_low_sample_is_shrunk_toward_neutral():
    assert .5 < empirical_fit(.55,100) < empirical_fit(.55,10000)


def test_missing_live_matchup_does_not_use_old_sample_as_real_data():
    result=analyze(AnalyzeRequest(role="top",championPool=["Ornn"],enemies=["Darius"],laneOpponent="Darius"),{"Ornn":stats()},True).recommendations[0]
    assert not result.matchup.known
    assert result.matchup.source == "unavailable"
    assert next(f.points for f in result.factors if f.key == "matchup") == 10


def test_every_roster_champion_can_be_selected_and_analyzed():
    champions=champions_by_name()
    assert len(champions)==173
    for name,c in champions.items():
        response=analyze(AnalyzeRequest(role=c["roles"][0],championPool=[name]))
        r=response.recommendations[0]
        assert r.champion==name and 0 <= r.score <= 100
        assert sum(f.maximum for f in r.factors)==100
        if c["traitSource"]=="unrated":
            assert not r.coreItems
            assert all(f.points==f.maximum/2 for f in r.factors if f.key in ("frontline","engage","peel","control","scaling","balance"))


def test_unknown_allied_traits_do_not_become_zero_strength():
    r=analyze(AnalyzeRequest(role="top",championPool=["Ornn"],allies=["Akali"]))
    assert r.composition.unratedChampions==["Akali"]
    assert r.composition.physicalShare is None
    assert not r.composition.needs
    assert next(f.points for f in r.recommendations[0].factors if f.key=="frontline")==4


def test_cache_prevents_repeated_requests_and_expiry_refetches(tmp_path,monkeypatch):
    monkeypatch.setattr(opgg,"CACHE_DIR",tmp_path)
    calls=[]
    async def fake_call(*args):
        calls.append(args)
        return {"champion":"ORNN","position":"TOP","data":{"summary":{"positions":[{"name":"TOP","stats":{"play":500,"win_rate":.51}}]}}}
    monkeypatch.setattr(opgg,"call_tool",fake_call)
    first=asyncio.run(opgg.get_champion_stats("Ornn","top"))
    second=asyncio.run(opgg.get_champion_stats("Ornn","top"))
    assert len(calls)==1 and first["status"]=="live" and second["status"]=="cached"
    file=next(tmp_path.glob('*.json'));data=json.loads(file.read_text());data['fetchedAt']=(datetime.now(timezone.utc)-timedelta(days=1)).isoformat();file.write_text(json.dumps(data))
    asyncio.run(opgg.get_champion_stats("Ornn","top"))
    assert len(calls)==2


def test_provider_failure_is_explicit_and_does_not_break_analysis(monkeypatch):
    monkeypatch.setenv("STATS_PROVIDER","opgg")
    async def fail(*args):raise ValueError("Malformed provider data")
    monkeypatch.setattr(opgg,"get_champion_stats",fail)
    result,warnings=asyncio.run(opgg.fetch_pool_stats(["Ornn"],"top"))
    assert result=={} and "unavailable" in warnings[0]


def test_provider_identity_mismatch_is_rejected():
    with pytest.raises(ValueError):opgg.normalize({"champion":"GAREN","position":"TOP"},"Ornn","top","now")


def test_provider_canonical_punctuation_alias_is_accepted():
    raw={"champion":"KAISA","position":"ADC","data":{"summary":{"positions":[{"name":"ADC","stats":{"play":500,"win_rate":.51}}]}}}
    assert opgg.normalize(raw,"Kai'Sa","adc","now")["champion"] == "Kai'Sa"

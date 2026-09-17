"""OP.GG's documented public MCP interface; no private website endpoints.

Provider text uses declarative compact objects. Parse a restricted AST; never eval it.
"""
import ast
import asyncio
import hashlib
import json
import math
import os
import re
from datetime import datetime, timezone
from pathlib import Path
import httpx

ENDPOINT = "https://mcp-api.op.gg/mcp"
CACHE_DIR = Path(__file__).resolve().parents[3] / ".cache" / "opgg"
TTL_SECONDS = 21600
ROLES = ("top", "jungle", "mid", "adc", "support")
FIELDS = ["champion", "position", "data.summary.positions[].{name,stats}",
          "data.trends.win.{created_at,version}",
          "data.strong_counters[].{champion_id,champion_name,my_win_rate,play}",
          "data.weak_counters[].{champion_id,champion_name,my_win_rate,play}",
          "data.core_items.{ids_names[],play,win}",
          "data.runes.{primary_page_name,primary_rune_names[],secondary_page_name,secondary_rune_names[],stat_mod_ids[],play,win}"]

def decode_compact(text):
    if len(text) > 2_000_000:
        raise ValueError("Provider payload too large")
    try:
        value = json.loads(text)
        if isinstance(value, dict): return value
    except json.JSONDecodeError:
        pass
    schemas, expressions = {}, []
    for line in text.splitlines():
        if line.startswith("class "):
            match = re.fullmatch(r"class ([A-Za-z][A-Za-z0-9_]*): ?(.*)", line)
            if not match: raise ValueError("Invalid compact schema")
            fields = [f.strip() for f in match[2].split(",") if f.strip()]
            if any(not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*", f) for f in fields): raise ValueError("Invalid field")
            schemas[match[1]] = fields
        elif line.strip(): expressions.append(line)
    tree = ast.parse(chr(10).join(expressions), mode="eval")
    budget = 100000
    def convert(node, depth=0):
        nonlocal budget
        budget -= 1
        if budget < 0 or depth > 40: raise ValueError("Provider payload too complex")
        if isinstance(node, ast.Constant) and isinstance(node.value, (str, int, float, bool, type(None))): return node.value
        if isinstance(node, ast.List): return [convert(v, depth+1) for v in node.elts]
        if isinstance(node, ast.Dict): return {convert(k, depth+1): convert(v, depth+1) for k,v in zip(node.keys,node.values)}
        if isinstance(node, ast.Name) and node.id in ("null", "true", "false"): return {"null": None, "true": True, "false": False}[node.id]
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub) and isinstance(node.operand, ast.Constant) and type(node.operand.value) in (int,float): return -node.operand.value
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in schemas and not node.keywords:
            fields = schemas[node.func.id]
            if len(fields) != len(node.args): raise ValueError("Compact field count mismatch")
            return dict(zip(fields, [convert(v, depth+1) for v in node.args]))
        raise ValueError("Unsupported provider expression")
    result = convert(tree.body)
    if not isinstance(result, dict): raise ValueError("Expected provider object")
    return result

def decode_rpc(response):
    response.raise_for_status()
    if "text/event-stream" in response.headers.get("content-type", ""):
        messages = [json.loads(line[5:].strip()) for line in response.text.splitlines() if line.startswith("data:")]
        envelope = next(m for m in messages if "result" in m or "error" in m)
    else: envelope = response.json()
    if envelope.get("error") or envelope.get("result", {}).get("isError"):
        raise ValueError("OP.GG returned a tool error")
    result = envelope["result"]
    if isinstance(result.get("structuredContent"), dict): return result["structuredContent"]
    return decode_compact(chr(10).join(c["text"] for c in result.get("content", []) if c.get("type") == "text"))

async def call_tool(name, arguments):
    async with httpx.AsyncClient(timeout=8) as client:
        response = await client.post(ENDPOINT, headers={"Accept": "application/json, text/event-stream"}, json={"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": name, "arguments": arguments}})
    return decode_rpc(response)

def champion_token(name):
    special = {"Wukong": "WUKONG", "Nunu & Willump": "NUNU", "Renata Glasc": "RENATA_GLASC"}
    return special.get(name, re.sub(r"[^A-Z0-9]+", "_", name.upper()).strip("_"))

def probability(value):
    if isinstance(value, bool) or not isinstance(value, (int,float)) or not math.isfinite(value) or not 0 <= value <= 1: raise ValueError("Invalid win rate")
    return float(value)

def games(value):
    if type(value) is not int or value < 0: raise ValueError("Invalid sample count")
    return value

def normalize(raw, champion, role, fetched_at):
    from app.services.catalog import champions_by_name
    identity = lambda value: re.sub(r"[^A-Z0-9]", "", str(value).upper())
    profile = champions_by_name().get(champion, {})
    accepted = {identity(champion_token(champion)), identity(champion), identity(profile.get("id", champion))}
    if raw.get("position", "").lower() != role or identity(raw.get("champion")) not in accepted:
        raise ValueError("Provider champion/role mismatch")
    data = raw["data"]
    positions = data.get("summary", {}).get("positions", [])
    position = next((p for p in positions if p.get("name", "").lower() == role), None)
    if position is None: raise ValueError("No statistics for requested role")
    stats = position["stats"]
    n = games(stats["play"])
    if n == 0: raise ValueError("Empty role sample")
    trend = data.get("trends", {}).get("win") or {}
    patch = trend.get("version")
    if not isinstance(patch, str) or not re.fullmatch(r"\d+\.\d+(?:\.\d+)?",patch): patch = None
    result = {"champion": champion, "role": role, "source": "OP.GG", "sourceUrl": "https://op.gg/lol/champions/" + ({"Wukong":"wukong"}.get(champion,profile.get("id",champion).lower())) + "/build/" + role,
              "patch": patch, "tier": "all", "region": "Provider default (not exposed)", "queue": "ranked", "games": n, "winRate": probability(stats["win_rate"]),
              "fetchedAt": fetched_at, "sourceUpdatedAt": trend.get("created_at"), "status": "live", "matchups": {}, "coreItems": None, "runes": None}
    # Both counter collections expose my_win_rate from the selected champion's perspective.
    for counter in data.get("strong_counters", []) + data.get("weak_counters", []):
        try:
            opponent = counter["champion_name"]
            result["matchups"][opponent] = {"games": games(counter["play"]), "winRate": probability(counter["my_win_rate"])}
        except (KeyError, TypeError, ValueError): continue
    core = data.get("core_items") or {}
    if isinstance(core.get("ids_names"),list) and core.get("play",0) >= 100 and len(core["ids_names"]) >= 1 and all(isinstance(s,str) for s in core["ids_names"]):
        result["coreItems"] = [{"name": name, "reason": f"OP.GG observed core combination ({core['play']:,} games). Completion is affected by game length and gold; this is not a causal item win-rate estimate."} for name in core["ids_names"]]
    rune = data.get("runes") or {}
    primary, secondary = rune.get("primary_rune_names", []), rune.get("secondary_rune_names", [])
    shards = {5001:"Health scaling",5002:"Armor",5003:"Magic resistance",5005:"Attack speed",5007:"Ability haste",5008:"Adaptive force",5010:"Move speed",5011:"Health",5013:"Tenacity and slow resist"}
    if rune.get("play",0) >= 100 and len(primary)==4 and len(secondary)==2 and all(isinstance(s,str) for s in primary+secondary):
        result["runes"] = {"primary":rune["primary_page_name"], "secondary":rune["secondary_page_name"],"keystone":primary[0],"runes":primary[1:]+secondary,"shards":[shards.get(v,f"Shard {v}") for v in rune.get("stat_mod_ids", [])]}
    return result

async def get_champion_stats(champion, role):
    key = hashlib.sha256(f"v1:{champion}:{role}:all".encode()).hexdigest()
    path = CACHE_DIR / (key + ".json")
    now = datetime.now(timezone.utc)
    try:
        cached = json.loads(path.read_text(encoding="utf-8"))
        age = (now - datetime.fromisoformat(cached["fetchedAt"])).total_seconds()
        if 0 <= age < TTL_SECONDS:
            return {**cached, "status": "cached"}
    except (OSError, ValueError, KeyError, TypeError): pass
    raw = await call_tool("lol_get_champion_analysis", {"game_mode":"ranked", "champion":champion_token(champion), "position":role, "tier":"all", "lang":"en_US", "desired_output_fields":FIELDS})
    result = normalize(raw, champion, role, now.isoformat())
    try:
        CACHE_DIR.mkdir(parents=True,exist_ok=True)
        temporary = path.with_suffix(".tmp")
        temporary.write_text(json.dumps(result),encoding="utf-8")
        temporary.replace(path)
    except OSError: pass
    return result

async def fetch_pool_stats(names, role):
    if os.getenv("STATS_PROVIDER", "opgg") != "opgg": return {}, ["Live statistics are disabled. Heuristic fallback is active."]
    semaphore = asyncio.Semaphore(4)
    results, failed = {}, []
    async def fetch(name):
        async with semaphore:
            try: results[name] = await get_champion_stats(name, role)
            except (httpx.HTTPError, ValueError, KeyError, TypeError, AttributeError, IndexError, StopIteration, SyntaxError, RecursionError): failed.append(name)
    tasks = [asyncio.create_task(fetch(name)) for name in names]
    done, pending = await asyncio.wait(tasks, timeout=18) if tasks else (set(),set())
    for task in pending: task.cancel()
    if pending: await asyncio.gather(*pending, return_exceptions=True)
    missing = sorted(set(names) - results.keys())
    warnings = ["OP.GG statistics unavailable for: " + ", ".join(missing) + ". Neutral statistical credit and labeled fallback guides are used."] if missing else []
    return results, warnings

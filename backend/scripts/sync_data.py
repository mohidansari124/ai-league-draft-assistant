"""Refresh Riot roster/assets and observed role mappings. Run from repo root."""
import argparse
import asyncio
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import httpx

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))
from app.services.catalog import DATA_DIR
from app.services.data_dragon import DataDragonService
from app.services.opgg import call_tool, ROLES


def write_json(path, value):
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding="utf-8")
    temporary.replace(path)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", help="Pin a Data Dragon version; default is latest published.")
    args = parser.parse_args()
    service = DataDragonService(args.version)
    raw = service.fetch_json("champion")["data"]
    items = service.fetch_json("item")["data"]
    if len(raw) < 100: raise ValueError("Unexpectedly small roster; refusing to replace snapshot")
    roles_path = DATA_DIR / "roles.json"
    role_data = json.loads(roles_path.read_text(encoding="utf-8"))
    try:
        result = asyncio.run(call_tool("lol_list_lane_meta_champions", {"position":"all", "desired_output_fields":[f"data.positions.{role}[].{{champion,role_rate}}" for role in ROLES]}))
        roles = {}
        for role, rows in result["data"]["positions"].items():
            for row in rows:
                if row["role_rate"] >= .1: roles.setdefault(row["champion"], []).append(role)
        if len(roles) >= 100: role_data["roles"] = roles
    except (httpx.HTTPError, ValueError, KeyError, TypeError):
        print("OP.GG role refresh unavailable; retaining the previous role map.")
    catalog_path = DATA_DIR / "champions.json"
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    previous = {c["name"]: c for c in catalog["champions"]}
    roster = []
    for c in raw.values():
        name = c["name"]
        profile = previous.get(name, {"archetype":c["tags"][0].lower(),"physicalShare":None,"traits":{k:None for k in ("frontline","engage","peel","control","scaling")},"tags":[],"traitSource":"unrated"})
        roles = role_data["roles"].get(name, profile.get("roles", list(ROLES)))
        roster.append({**profile,"id":c["id"],"key":c["key"],"name":name,"roles":roles,"roleSource":"OP.GG observed roles" if name in role_data["roles"] else "fallback; role data unavailable"})
    catalog["champions"] = sorted(roster,key=lambda c:c["name"])
    catalog["version"] = f"Riot {service.version} roster + heuristic traits v1"
    metadata = {"version":service.version,"source":service.base_url,"champions":{c["id"]:{"name":c["name"],"title":c["title"]} for c in raw.values()},"items":{k:{"name":v["name"],"gold":v["gold"]["total"]} for k,v in items.items()}}
    portraits = ROOT / "frontend/public/portraits"
    portraits.mkdir(parents=True,exist_ok=True)
    def download(c):
        (portraits / (c["id"]+".png")).write_bytes(service.fetch_portrait(c["id"]))
    with ThreadPoolExecutor(max_workers=6) as pool: list(pool.map(download,roster))
    write_json(roles_path,role_data)
    write_json(DATA_DIR / "riot_metadata.json",metadata)
    write_json(catalog_path,catalog)
    print(f"Updated {len(roster)} champions to Riot {service.version}. Restart the backend to reload the snapshot.")

if __name__ == "__main__": main()

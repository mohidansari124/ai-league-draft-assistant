"""Run from repo root: .venv/Scripts/python backend/scripts/sync_data.py"""
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))
from app.services.catalog import champions_by_name, DATA_DIR
from app.services.data_dragon import DataDragonService

if __name__ == "__main__":
    service = DataDragonService()
    champions = champions_by_name()
    raw = service.fetch_json("champion")["data"]
    items = service.fetch_json("item")["data"]
    metadata = {"version": service.version, "source": service.base_url, "champions": {c["id"]: {"name": raw[c["id"]]["name"], "title": raw[c["id"]]["title"]} for c in champions.values()}, "items": {key: {"name": value["name"], "gold": value["gold"]["total"]} for key, value in items.items()}}
    (DATA_DIR / "riot_metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    portraits = ROOT / "frontend" / "public" / "portraits"
    portraits.mkdir(parents=True, exist_ok=True)
    def download(c):
        path = portraits / (c["id"] + ".png")
        path.write_bytes(service.fetch_portrait(c["id"]))
    with ThreadPoolExecutor(max_workers=6) as pool:
        list(pool.map(download, champions.values()))
    print(f"Saved {len(champions)} portraits and Riot static metadata from {service.version}. Scoring data unchanged.")

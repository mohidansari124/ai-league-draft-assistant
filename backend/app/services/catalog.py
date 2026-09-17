import json
from functools import lru_cache
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[1] / "data"

@lru_cache
def load_catalog():
    """Local catalog is the sole scoring input; external metadata never supplies traits."""
    return json.loads((DATA_DIR / "champions.json").read_text(encoding="utf-8"))

@lru_cache
def load_guides():
    return json.loads((DATA_DIR / "guides.json").read_text(encoding="utf-8"))

@lru_cache
def load_metadata():
    path = DATA_DIR / "riot_metadata.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {"version": None, "champions": {}}

def champions_by_name():
    return {c["name"]: c for c in load_catalog()["champions"]}

def public_catalog():
    catalog, metadata = load_catalog(), load_metadata()
    return {"dataVersion": catalog["version"], "metadataVersion": metadata["version"],
            "notice": catalog["notice"], "champions": [
                {**c, "title": metadata["champions"].get(c["id"], {}).get("title", c["archetype"]),
                 "portrait": f"/portraits/{c['id']}.png"} for c in catalog["champions"]]}

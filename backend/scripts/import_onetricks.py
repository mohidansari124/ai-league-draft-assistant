"""Import a reviewed/authorized JSON observation batch into SQLite (operator only)."""
import argparse
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parents[2] / ".env")
from app.database import import_observations
from app.services.onetricks import Observation

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", type=Path)
    args = parser.parse_args()
    raw = json.loads(args.file.read_text(encoding="utf-8"))
    if not isinstance(raw,list) or not 1 <= len(raw) <= 1000:
        raise SystemExit("Expected a list of 1 to 1000 observations.")
    records = [Observation.model_validate(r).model_dump(mode="json") for r in raw]
    import_observations(records)
    print(f"Validated {len(records)} records; persisted idempotently.")

if __name__ == "__main__": main()

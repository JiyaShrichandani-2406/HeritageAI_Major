"""Validate data/raw/places/*.csv and write data/processed/nearby_places.json (Member 3).

Run from backend/:  python -m app.ingestion.import_places
Exits non-zero if any row is invalid, so bad data never reaches the API.
"""
import csv
import json
import sys
from pathlib import Path

from backend.app.models.place import CATEGORIES

ROOT = Path(__file__).resolve().parents[3]
RAW_DIR = ROOT / "data" / "raw" / "places"
OUT_FILE = ROOT / "data" / "processed" / "nearby_places.json"
REQUIRED = ("id", "name", "category", "latitude", "longitude", "address", "source_url")


def validate_row(row: dict, line: int, seen: set) -> tuple:
    errors = [f"missing {f}" for f in REQUIRED if not (row.get(f) or "").strip()]
    if errors:
        return None, [f"line {line}: {e}" for e in errors]
    pid = row["id"].strip()
    if pid in seen:
        errors.append(f"duplicate id '{pid}'")
    if row["category"].strip() not in CATEGORIES:
        errors.append(f"invalid category '{row['category']}'")
    lat = lon = 0.0
    try:
        lat, lon = float(row["latitude"]), float(row["longitude"])
        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
            errors.append("coordinates out of range")
    except ValueError:
        errors.append("latitude/longitude not numeric")
    if not row["source_url"].strip().startswith(("http://", "https://")):
        errors.append("source_url must be http(s)")
    if errors:
        return None, [f"line {line}: {e}" for e in errors]
    return {
        "id": pid, "name": row["name"].strip(), "category": row["category"].strip(),
        "latitude": lat, "longitude": lon, "address": row["address"].strip(),
        "source_url": row["source_url"].strip(),
    }, []


def main() -> int:
    places, errors, seen = [], [], set()
    for csv_file in sorted(RAW_DIR.glob("*.csv")):
        with csv_file.open(encoding="utf-8", newline="") as fh:
            for i, row in enumerate(csv.DictReader(fh), start=2):
                place, errs = validate_row(row, i, seen)
                if errs:
                    errors += [f"{csv_file.name} {e}" for e in errs]
                else:
                    seen.add(place["id"])
                    places.append(place)
    if errors:
        print("Import failed:\n  " + "\n  ".join(errors))
        return 1
    places.sort(key=lambda p: p["id"])
    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUT_FILE.write_text(json.dumps(places, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {len(places)} places to {OUT_FILE}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

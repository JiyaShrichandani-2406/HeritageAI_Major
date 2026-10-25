import json
import shutil
from datetime import datetime
from pathlib import Path

existing_path = Path("data/processed/nearby_places.json")
new_path = Path("data/processed/member2_place_records.json")

required = {
    "id", "name", "category", "latitude",
    "longitude", "address", "source_url"
}

existing = json.loads(existing_path.read_text(encoding="utf-8-sig"))
new = json.loads(new_path.read_text(encoding="utf-8-sig"))

if not isinstance(existing, list) or not isinstance(new, list):
    raise SystemExit("STOP: Both files must contain JSON lists.")

if len(existing) != 11:
    raise SystemExit(f"STOP: Expected 11 original records; found {len(existing)}.")

if len(new) != 8:
    raise SystemExit(f"STOP: Expected 8 new records; found {len(new)}.")

for label, records in [("Existing", existing), ("New", new)]:
    for i, record in enumerate(records):
        missing = required - record.keys()
        if missing:
            raise SystemExit(
                f"STOP: {label} record {i} is missing: {sorted(missing)}"
            )
        if not record["address"] or not record["source_url"]:
            raise SystemExit(f"STOP: {label} record {i} has an empty address or source.")

existing_ids = [r["id"] for r in existing]
new_ids = [r["id"] for r in new]

if len(existing_ids) != len(set(existing_ids)):
    raise SystemExit("STOP: Duplicate IDs already exist in the original dataset.")

duplicates = set(existing_ids) & set(new_ids)
if duplicates:
    raise SystemExit(f"STOP: These IDs already exist: {sorted(duplicates)}")

if len(new_ids) != len(set(new_ids)):
    raise SystemExit("STOP: Duplicate IDs found in the new records.")

combined = existing + new

if len(combined) != 19:
    raise SystemExit("STOP: Final record count is not 19.")

backup = existing_path.with_name(
    f"nearby_places.pre_member2_{datetime.now():%Y%m%d_%H%M%S}.json"
)
shutil.copy2(existing_path, backup)

temp_path = existing_path.with_suffix(".tmp")
temp_path.write_text(
    json.dumps(combined, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8"
)
temp_path.replace(existing_path)

print("Merge successful.")
print("Original records preserved:", len(existing))
print("New records added:", len(new))
print("Final record count:", len(combined))
print("Backup created:", backup)
print("Updated file:", existing_path)
print("Categories:", sorted({r["category"] for r in combined}))

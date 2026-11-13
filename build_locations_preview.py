import json
from pathlib import Path
from collections import defaultdict

DATA = Path("data/processed")
heritage_file = DATA / "heritage.json"
nearby_file = DATA / "nearby_places.json"

for file in [heritage_file, nearby_file]:
    if not file.exists():
        raise FileNotFoundError(f"Required file not found: {file}")

with heritage_file.open("r", encoding="utf-8-sig") as f:
    heritage = json.load(f)

with nearby_file.open("r", encoding="utf-8-sig") as f:
    nearby = json.load(f)

if not isinstance(heritage, list) or not isinstance(nearby, list):
    raise ValueError("Expected both source JSON files to contain a list.")

cities = [
    {
        "id": "city-agra",
        "name": "Agra",
        "state": "Uttar Pradesh",
        "country": "India",
        "type": "city"
    },
    {
        "id": "city-fatehpur-sikri",
        "name": "Fatehpur Sikri",
        "state": "Uttar Pradesh",
        "country": "India",
        "type": "city"
    },
    {
        "id": "city-bharatpur",
        "name": "Bharatpur",
        "state": "Rajasthan",
        "country": "India",
        "type": "city"
    }
]

locations = {}
conflicts = []

def parent_for(record):
    city = str(record.get("city", "")).strip().lower()
    name = str(record.get("name", "")).strip().lower()
    address = str(record.get("address", "")).strip().lower()

    if "fatehpur sikri" in city or "fatehpur sikri" in name:
        return "city-fatehpur-sikri"

    if "bharatpur" in city or "keoladeo" in name or "bharatpur" in address:
        return "city-bharatpur"

    return "city-agra"

def add_record(record, source):
    location_id = record.get("id")
    if not location_id:
        conflicts.append(f"{source}: Record has no ID: {record.get('name')}")
        return

    location_id = str(location_id)
    parent_id = parent_for(record)

    if location_id not in locations:
        locations[location_id] = {
            "id": location_id,
            "name": record.get("name"),
            "type": "place",
            "parent_id": parent_id,
            "latitude": record.get("latitude"),
            "longitude": record.get("longitude"),
            "sources": [source],
            "heritage_data": None,
            "nearby_data": None
        }

    item = locations[location_id]

    if item["name"] != record.get("name"):
        conflicts.append(
            f"{location_id}: Name differs: "
            f"{item['name']} vs {record.get('name')}"
        )

    old_lat = item.get("latitude")
    old_lon = item.get("longitude")
    new_lat = record.get("latitude")
    new_lon = record.get("longitude")

    if (old_lat is not None and new_lat is not None and
        old_lon is not None and new_lon is not None and
        (old_lat != new_lat or old_lon != new_lon)):
        conflicts.append(
            f"{location_id}: Coordinate difference: "
            f"existing=({old_lat}, {old_lon}), "
            f"{source}=({new_lat}, {new_lon})"
        )

    if source not in item["sources"]:
        item["sources"].append(source)

    if source == "heritage":
        item["heritage_data"] = record
        if new_lat is not None and new_lon is not None:
            item["latitude"] = new_lat
            item["longitude"] = new_lon
    else:
        item["nearby_data"] = record
        if item["latitude"] is None and new_lat is not None:
            item["latitude"] = new_lat
            item["longitude"] = new_lon

for record in heritage:
    add_record(record, "heritage")

for record in nearby:
    add_record(record, "nearby_places")

preview = {
    "cities": cities,
    "locations": list(locations.values())
}

Path("locations_preview.json").write_text(
    json.dumps(preview, indent=2, ensure_ascii=False),
    encoding="utf-8"
)

Path("location_conflicts.txt").write_text(
    "\n".join(conflicts) if conflicts else "No conflicts detected.",
    encoding="utf-8"
)

print("Preview generation completed.")
print(f"Heritage records read: {len(heritage)}")
print(f"Nearby-place records read: {len(nearby)}")
print(f"Unique places in preview: {len(locations)}")
print(f"Potential conflicts found: {len(conflicts)}")
print("Created: locations_preview.json")
print("Created: location_conflicts.txt")

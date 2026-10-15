"""Validate data/processed/heritage.json and export it for the RAG pipeline.

The RAG loader (backend/app/rag/document_loader.py) reads .txt files from
data/raw/heritage/. This script turns each monument in heritage.json into one
such file, so heritage.json stays the single place where the data is edited.

Run from the repository root:
    python -m backend.app.ingestion.import_heritage

Afterwards the vector store must be rebuilt (Member 5's script):
    python -m scripts.rebuild_vector_store
"""

import json
import sys
from typing import Any

from backend.app.repositories.monument_repository import HERITAGE_FILE

# data/processed/heritage.json -> data/raw/heritage/
RAG_DOCUMENTS_DIR = HERITAGE_FILE.parents[1] / "raw" / "heritage"


def monument_to_text(record: dict[str, Any]) -> str:
    """Build a document in the 'KEY: value' format that document_loader.py reads.

    The loader takes TITLE, CATEGORY, SOURCE URL and LAST VERIFIED from these
    header lines and indexes the whole text.
    """
    name = record["name"]
    location = f"{record['city']}, {record['state']}, {record['country']}"
    sources = record["sources"]

    lines = [
        f"DOCUMENT ID: {record['id']}",
        f"TITLE: {name}",
        "CATEGORY: Monument",
        f"LOCATION: {location}",
        f"SOURCE URL: {sources[0]['url']}",
        f"LAST VERIFIED: {record.get('last_verified') or 'Not verified'}",
    ]

    # The loader keeps one source URL per document; extra sources stay in the text.
    for extra in sources[1:]:
        lines.append(f"ADDITIONAL SOURCE URL: {extra['url']}")

    lines += [
        "",
        "CONTENT:",
        "",
        f"{name} is located in {location}. {record['summary']}",
        "",
        f"History of {name}. {record['history']}",
        "",
        f"Architecture of {name}. {record['architecture']}",
        "",
    ]

    return "\n".join(lines)


def main() -> int:
    # Imported here so monument_to_text() can be used without pydantic installed.
    from backend.app.schemas.monument import MonumentResponse

    with HERITAGE_FILE.open(encoding="utf-8") as file:
        records = json.load(file)

    problems = 0
    seen_ids: set[str] = set()

    for index, record in enumerate(records, start=1):
        label = record.get("id", f"record {index}")

        try:
            monument = MonumentResponse(**record)
        except Exception as error:
            print(f"INVALID {label}: {error}")
            problems += 1
            continue

        if monument.id in seen_ids:
            print(f"INVALID {label}: duplicate id")
            problems += 1
        seen_ids.add(monument.id)

        for source in monument.sources:
            if not source.url.startswith(("http://", "https://")):
                print(f"INVALID {label}: source URL is not a web link: {source.url}")
                problems += 1

        if "example.org" in monument.sources[0].url:
            print(f"INVALID {label}: placeholder source URL")
            problems += 1

        if not monument.images:
            print(f"WARNING {label}: no images added yet")

        if not monument.last_verified:
            print(f"WARNING {label}: last_verified not set, exported as 'Not verified'")

    if problems:
        print(f"{problems} problem(s) found. Nothing was exported.")
        return 1

    RAG_DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)

    for record in records:
        path = RAG_DOCUMENTS_DIR / f"{record['id']}.txt"
        path.write_text(monument_to_text(record), encoding="utf-8")
        print(f"Exported {path.name}")

    if (RAG_DOCUMENTS_DIR / "sample_monument_a.txt").exists():
        print(
            "NOTE: sample_monument_a.txt is unverified test data. "
            "Agree with Member 5 before removing it."
        )

    print(f"Exported {len(records)} document(s) to {RAG_DOCUMENTS_DIR}.")
    print("Next: rebuild the vector store with: python -m scripts.rebuild_vector_store")
    return 0


if __name__ == "__main__":
    sys.exit(main())

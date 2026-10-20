
from pathlib import Path


# Find the HeritageAI_Major project root
PROJECT_ROOT = Path(__file__).resolve().parents[3]

# Folder containing your sample documents
DATA_DIR = PROJECT_ROOT / "data" / "raw" / "heritage"


def load_documents():
    documents = []

    if not DATA_DIR.exists():
        raise FileNotFoundError(
            f"Heritage data folder not found: {DATA_DIR}"
        )

    for file_path in DATA_DIR.glob("*.txt"):
        text = file_path.read_text(encoding="utf-8").strip()

        # Skip empty documents
        if not text:
            continue

        metadata = {}
        additional_source_urls = []

        # Extract metadata from lines such as TITLE: Taj Mahal
        for line in text.splitlines():
            if ":" in line:
                key, value = line.split(":", 1)
                normalized_key = key.strip().lower().replace(" ", "_")
                normalized_value = value.strip()
                if normalized_key == "additional_source_url":
                    additional_source_urls.append(normalized_value)
                else:
                    metadata[normalized_key] = normalized_value

        documents.append({
            "title": metadata.get("title", file_path.stem),
            "text": text,
            "source_url": metadata.get("source_url", ""),
            "source_urls": [
                metadata.get("source_url", ""),
                *additional_source_urls,
            ],
            "category": metadata.get("category", "unknown"),
            "last_verified": metadata.get(
                "last_verified", "Not verified"
            ),
            "file_name": file_path.name,
        })

    return documents


if __name__ == "__main__":
    docs = load_documents()

    print(f"\nDocuments loaded: {len(docs)}")

    for doc in docs:
        print("\n------------------------------")
        print("File:", doc["file_name"])
        print("Title:", doc["title"])
        print("Source:", doc["source_url"])
        print("Content preview:", doc["text"][:150])

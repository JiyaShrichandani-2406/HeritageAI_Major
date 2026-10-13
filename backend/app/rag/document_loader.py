
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

        # Extract metadata from lines such as TITLE: Taj Mahal
        for line in text.splitlines():
            if ":" in line:
                key, value = line.split(":", 1)
                metadata[key.strip().lower().replace(" ", "_")] = (
                    value.strip()
                )

        documents.append({
            "title": metadata.get("title", file_path.stem),
            "text": text,
            "source_url": metadata.get("source_url", ""),
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

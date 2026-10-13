
from pathlib import Path

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

from backend.app.rag.document_loader import load_documents
from backend.app.rag.text_splitter import split_text


# Project folders
PROJECT_ROOT = Path(__file__).resolve().parents[3]
VECTOR_STORE_DIR = PROJECT_ROOT / "data" / "vector_store"

# Embedding model
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


def build_vector_store():
    """Create embeddings and a FAISS index from loaded documents."""

    documents = load_documents()

    if not documents:
        raise ValueError("No documents found to index.")

    print("Loading embedding model...")
    model = SentenceTransformer(MODEL_NAME)

    chunks = []

    for document in documents:
        document_chunks = split_text(document["text"])

        for chunk in document_chunks:
            chunks.append({
                "text": chunk,
                "title": document["title"],
                "source_url": document["source_url"],
                "category": document["category"],
                "file_name": document["file_name"],
            })

    if not chunks:
        raise ValueError("No text chunks available to index.")

    texts = [chunk["text"] for chunk in chunks]

    print(f"Creating embeddings for {len(texts)} chunks...")

    embeddings = model.encode(
        texts,
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=True,
    )

    embeddings = np.asarray(embeddings, dtype="float32")

    # Normalized vectors allow inner product to measure cosine similarity.
    index = faiss.IndexFlatIP(embeddings.shape[1])
    index.add(embeddings)

    VECTOR_STORE_DIR.mkdir(parents=True, exist_ok=True)

    faiss.write_index(
        index,
        str(VECTOR_STORE_DIR / "heritage.index"),
    )

    # Save matching chunk information separately.
    import json

    with open(
        VECTOR_STORE_DIR / "chunks.json",
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(chunks, file, ensure_ascii=False, indent=2)

    print("\nVector store created successfully.")
    print("Total documents:", len(documents))
    print("Total chunks indexed:", len(chunks))
    print("Saved index:", VECTOR_STORE_DIR / "heritage.index")
    print("Saved chunk metadata:", VECTOR_STORE_DIR / "chunks.json")


if __name__ == "__main__":
    build_vector_store()

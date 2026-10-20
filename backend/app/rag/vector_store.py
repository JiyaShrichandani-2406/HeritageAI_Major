
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

from backend.app.core.config import get_settings
from backend.app.rag.document_loader import load_documents
from backend.app.rag.text_splitter import split_text


# Embedding model
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


def build_vector_store():
    """Create embeddings and a FAISS index from loaded documents."""

    vector_store_dir = get_settings().vector_store_dir
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
                "source_urls": document.get(
                    "source_urls",
                    [document["source_url"]],
                ),
                "category": document["category"],
                "last_verified": document.get(
                    "last_verified",
                    "Not verified",
                ),
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

    vector_store_dir.mkdir(parents=True, exist_ok=True)

    faiss.write_index(
        index,
        str(vector_store_dir / "heritage.index"),
    )

    # Save matching chunk information separately.
    import json

    with open(
        vector_store_dir / "chunks.json",
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(chunks, file, ensure_ascii=False, indent=2)

    print("\nVector store created successfully.")
    print("Total documents:", len(documents))
    print("Total chunks indexed:", len(chunks))
    print("Saved index:", vector_store_dir / "heritage.index")
    print("Saved chunk metadata:", vector_store_dir / "chunks.json")


if __name__ == "__main__":
    build_vector_store()

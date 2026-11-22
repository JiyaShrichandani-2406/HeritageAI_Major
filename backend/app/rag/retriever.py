import json
from functools import lru_cache

import faiss
import numpy as np

from backend.app.core.config import get_settings

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


class HeritageRetriever:
    def __init__(self):
        vector_store_dir = get_settings().vector_store_dir
        index_path = vector_store_dir / "heritage.index"
        chunks_path = vector_store_dir / "chunks.json"

        if not index_path.exists():
            raise FileNotFoundError(
                f"FAISS index not found: {index_path}. "
                "Run the vector-store builder first."
            )

        if not chunks_path.exists():
            raise FileNotFoundError(
                f"Chunk metadata not found: {chunks_path}"
            )

        print("Loading FAISS index...")
        self.index = faiss.read_index(str(index_path))

        with open(chunks_path, "r", encoding="utf-8") as file:
            self.chunks = json.load(file)

        # Import the embedding model only when a retriever is initialized.
        # fastembed uses an ONNX runtime, which keeps the backend small enough
        # to fit in 512 MB RAM (no PyTorch dependency).
        print("Loading embedding model...")
        from fastembed import TextEmbedding

        self.model = TextEmbedding(model_name=MODEL_NAME)

        if self.index.ntotal != len(self.chunks):
            raise ValueError(
                "Index and chunk metadata counts do not match."
            )

    def _embed(self, texts: list[str]) -> np.ndarray:
        # fastembed returns a generator of 1D numpy arrays, already L2-normalized
        # for sentence-transformers models — matching the previous behavior of
        # SentenceTransformer(..., normalize_embeddings=True).
        vectors = list(self.model.embed(texts))
        return np.asarray(vectors, dtype="float32")

    def search(self, question: str, top_k: int = 3):
        if not question or not question.strip():
            raise ValueError("Question cannot be empty.")

        if top_k < 1:
            raise ValueError("top_k must be at least 1.")

        query_embedding = self._embed([question.strip()])

        scores, indices = self.index.search(
            query_embedding,
            min(top_k, len(self.chunks)),
        )

        results = []

        for score, index_position in zip(scores[0], indices[0]):
            if index_position < 0:
                continue

            chunk = self.chunks[int(index_position)]

            results.append({
                **chunk,
                "relevance_score": float(score),
            })

        return results


if __name__ == "__main__":
    retriever = HeritageRetriever()

    question = input("Enter a heritage question: ")
    results = retriever.search(question, top_k=3)

    print("\nRetrieved chunks:")

    for number, result in enumerate(results, start=1):
        print(f"\n--- Result {number} ---")
        print("Title:", result["title"])
        print("Source:", result["source_url"])
        print("Similarity:", round(result["relevance_score"], 4))
        print("Text:", result["text"][:300])


@lru_cache(maxsize=1)
def get_retriever() -> HeritageRetriever:
    """Return the shared retriever instance for this process."""
    return HeritageRetriever()

import json
from types import SimpleNamespace

import numpy as np

from backend.app.rag import vector_store


def test_vector_store_builder_uses_configured_directory(
    monkeypatch, tmp_path
):
    configured_path = tmp_path / "configured-vector-store"
    written_index_paths = []

    class StubModel:
        def encode(self, texts, **kwargs):
            return np.array([[1.0, 0.0]], dtype="float32")

    class StubIndex:
        def __init__(self, dimensions):
            self.dimensions = dimensions

        def add(self, embeddings):
            self.embeddings = embeddings

    monkeypatch.setattr(
        vector_store,
        "get_settings",
        lambda: SimpleNamespace(vector_store_dir=configured_path),
    )
    monkeypatch.setattr(
        vector_store,
        "load_documents",
        lambda: [
            {
                "text": "Taj Mahal heritage",
                "title": "Taj Mahal",
                "source_url": "https://whc.unesco.org/en/list/252",
                "category": "Monument",
                "file_name": "taj-mahal.txt",
            }
        ],
    )
    monkeypatch.setattr(
        vector_store,
        "SentenceTransformer",
        lambda model_name: StubModel(),
    )
    monkeypatch.setattr(
        vector_store.faiss,
        "IndexFlatIP",
        lambda dimensions: StubIndex(dimensions),
    )
    monkeypatch.setattr(
        vector_store.faiss,
        "write_index",
        lambda index, path: written_index_paths.append(path),
    )

    vector_store.build_vector_store()

    assert written_index_paths == [
        str(configured_path / "heritage.index")
    ]
    assert json.loads(
        (configured_path / "chunks.json").read_text(encoding="utf-8")
    )[0]["title"] == "Taj Mahal"

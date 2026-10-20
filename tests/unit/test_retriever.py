import json
from types import SimpleNamespace

import pytest

from backend.app.rag import retriever as retriever_module
from backend.app.rag.retriever import HeritageRetriever


def test_retriever_uses_configured_vector_store_directory(
    monkeypatch, tmp_path
):
    configured_path = tmp_path / "configured-vector-store"
    configured_path.mkdir()
    (configured_path / "heritage.index").touch()
    (configured_path / "chunks.json").write_text(
        json.dumps([{"text": "heritage"}]),
        encoding="utf-8",
    )

    class StubIndex:
        ntotal = 1

    monkeypatch.setattr(
        retriever_module,
        "get_settings",
        lambda: SimpleNamespace(vector_store_dir=configured_path),
    )
    monkeypatch.setattr(
        retriever_module.faiss,
        "read_index",
        lambda path: (
            path == str(configured_path / "heritage.index")
            and StubIndex()
        ),
    )
    monkeypatch.setattr(
        retriever_module,
        "SentenceTransformer",
        lambda model_name: object(),
    )

    retriever = HeritageRetriever()

    assert retriever.chunks == [{"text": "heritage"}]
    assert isinstance(retriever.index, StubIndex)


@pytest.fixture(scope="module")
def retriever():
    """Load the existing FAISS index and embedding model once."""
    return HeritageRetriever()


def test_search_returns_results(retriever):
    """A valid heritage question should return retrieved chunks."""
    results = retriever.search(
        "Where is the Taj Mahal located?",
        top_k=3,
    )

    assert isinstance(results, list)
    assert len(results) > 0


def test_result_contains_expected_fields(retriever):
    """Each result should contain the fields used by the RAG pipeline."""
    results = retriever.search(
        "Taj Mahal location",
        top_k=1,
    )

    assert len(results) > 0

    result = results[0]

    assert "text" in result
    assert "title" in result
    assert "source_url" in result
    assert "relevance_score" in result
    assert isinstance(result["relevance_score"], float)


def test_top_k_limits_results(retriever):
    """The retriever should not return more than top_k results."""
    results = retriever.search(
        "Indian cultural heritage",
        top_k=2,
    )

    assert len(results) <= 2


def test_empty_question_raises_error(retriever):
    """An empty question should be rejected."""
    with pytest.raises(ValueError, match="Question cannot be empty"):
        retriever.search("   ")


def test_invalid_top_k_raises_error(retriever):
    """A top_k value below one should be rejected."""
    with pytest.raises(ValueError, match="top_k must be at least 1"):
        retriever.search("Taj Mahal", top_k=0)
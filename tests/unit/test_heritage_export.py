from backend.app.ingestion import import_heritage
from backend.app.rag import document_loader

RECORD = {
    "id": "taj-mahal",
    "name": "Taj Mahal",
    "city": "Agra",
    "state": "Uttar Pradesh",
    "country": "India",
    "summary": "Marble mausoleum built by Shah Jahan.",
    "history": "Construction began around 1632.",
    "architecture": "Mughal architecture with a central dome.",
    "sources": [
        {"title": "UNESCO", "url": "https://whc.unesco.org/en/list/252"},
        {"title": "Second source", "url": "https://example.com/second"},
    ],
}


def test_document_loader_reads_exported_file(tmp_path, monkeypatch):
    """The exported text must be parsed correctly by the RAG document loader."""
    text = import_heritage.monument_to_text(RECORD)
    (tmp_path / "taj-mahal.txt").write_text(text, encoding="utf-8")
    monkeypatch.setattr(document_loader, "DATA_DIR", tmp_path)

    documents = document_loader.load_documents()

    assert len(documents) == 1
    document = documents[0]
    assert document["title"] == "Taj Mahal"
    assert document["category"] == "Monument"
    assert document["source_url"] == "https://whc.unesco.org/en/list/252"
    assert document["last_verified"] == "Not verified"
    assert "History of Taj Mahal" in document["text"]


def test_exported_text_keeps_extra_sources_and_date():
    record = {**RECORD, "last_verified": "2026-10-20"}

    text = import_heritage.monument_to_text(record)

    assert "LAST VERIFIED: 2026-10-20" in text
    assert "ADDITIONAL SOURCE URL: https://example.com/second" in text

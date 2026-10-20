from backend.app.ai import answer_generator


class StubRetriever:
    def __init__(self, chunks):
        self.chunks = chunks

    def search(self, question, top_k):
        return self.chunks


def test_unrelated_retrieval_abstains_without_calling_llm(monkeypatch):
    monkeypatch.setattr(
        answer_generator,
        "get_retriever",
        lambda: StubRetriever(
            [
                {
                    "title": "Taj Mahal",
                    "category": "Monument",
                    "text": "The Taj Mahal is in Agra.",
                    "source_url": "https://whc.unesco.org/en/list/252",
                    "relevance_score": 0.084,
                }
            ]
        ),
    )
    monkeypatch.setattr(
        answer_generator,
        "generate_response",
        lambda prompt: (_ for _ in ()).throw(
            AssertionError("LLM should not run for irrelevant retrieval.")
        ),
    )

    result = answer_generator.generate_answer(
        "What is the price of bus tickets in Tokyo?"
    )

    assert result["grounded"] is False
    assert result["sources"] == []
    assert "relevance threshold" in result["message"]


def test_relevant_retrieval_is_used_for_answer(monkeypatch):
    monkeypatch.setattr(
        answer_generator,
        "get_retriever",
        lambda: StubRetriever(
            [
                {
                    "title": "Taj Mahal",
                    "category": "Monument",
                    "text": "The Taj Mahal was commissioned by Shah Jahan.",
                    "source_url": "https://whc.unesco.org/en/list/252",
                    "relevance_score": 0.668,
                }
            ]
        ),
    )
    monkeypatch.setattr(
        answer_generator,
        "generate_response",
        lambda prompt: "Shah Jahan commissioned the Taj Mahal.",
    )

    result = answer_generator.generate_answer(
        "Who commissioned the Taj Mahal?"
    )

    assert result["grounded"] is True
    assert result["sources"][0]["title"] == "Taj Mahal"

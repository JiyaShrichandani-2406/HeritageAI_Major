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
                    "source_urls": [
                        "https://whc.unesco.org/en/list/252",
                        "https://en.wikipedia.org/wiki/Taj_Mahal",
                    ],
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
    assert {source["url"] for source in result["sources"]} == {
        "https://whc.unesco.org/en/list/252",
        "https://en.wikipedia.org/wiki/Taj_Mahal",
    }


def test_weak_agreement_score_abstains(monkeypatch):
    monkeypatch.setattr(
        answer_generator,
        "get_retriever",
        lambda: StubRetriever(
            [
                {
                    "title": "Agra Fort",
                    "text": "A weakly matching result.",
                    "source_url": "https://agra.nic.in/tourist-place/agra-fort/",
                    "relevance_score": 0.509,
                }
            ]
        ),
    )
    monkeypatch.setattr(
        answer_generator,
        "generate_response",
        lambda prompt: (_ for _ in ()).throw(
            AssertionError("The LLM must not receive weakly relevant context.")
        ),
    )

    result = answer_generator.generate_answer(
        "What is the population of Tokyo?"
    )

    assert result["grounded"] is False
    assert result["sources"] == []


def test_duplicate_urls_across_titles_keep_the_best_source(monkeypatch):
    monkeypatch.setattr(
        answer_generator,
        "get_retriever",
        lambda: StubRetriever(
            [
                {
                    "title": "Taj Mahal",
                    "text": "The Taj Mahal is in Agra.",
                    "source_url": "https://whc.unesco.org/en/list/252/",
                    "relevance_score": 0.61,
                },
                {
                    "title": "Taj Mahal - duplicate",
                    "text": "The Taj Mahal is in Agra.",
                    "source_url": "https://whc.unesco.org/en/list/252",
                    "relevance_score": 0.72,
                },
            ]
        ),
    )
    monkeypatch.setattr(
        answer_generator,
        "generate_response",
        lambda prompt: "The Taj Mahal is in Agra.",
    )

    result = answer_generator.generate_answer("Where is the Taj Mahal?")

    matching = [
        source
        for source in result["sources"]
        if source["url"].rstrip("/") == "https://whc.unesco.org/en/list/252"
    ]
    assert len(matching) == 1
    assert matching[0]["title"] == "Taj Mahal - duplicate"
    assert matching[0]["relevance_score"] == 0.72

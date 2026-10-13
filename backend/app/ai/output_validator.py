
from urllib.parse import urlparse


ABSTENTION_ANSWER = (
    "I couldn't find enough information in the available "
    "heritage documents to answer this question."
)


def validate_output(result: dict) -> dict:
    """
    Validate the answer-generator result before returning it to a client.

    This checks response structure and source metadata.
    It does not independently prove factual correctness.
    """

    if not isinstance(result, dict):
        raise ValueError("Answer result must be a dictionary.")

    answer = result.get("answer")
    sources = result.get("sources")
    grounded = result.get("grounded")
    message = result.get("message", "")

    if not isinstance(answer, str) or not answer.strip():
        raise ValueError("Answer must be a non-empty string.")

    if not isinstance(sources, list):
        raise ValueError("Sources must be a list.")

    if not isinstance(grounded, bool):
        raise ValueError("Grounded must be a boolean.")

    if not isinstance(message, str):
        raise ValueError("Message must be a string.")

    validated_sources = []

    for source in sources:
        if not isinstance(source, dict):
            raise ValueError("Each source must be a dictionary.")

        title = source.get("title")
        url = source.get("url")
        score = source.get("relevance_score")

        if not isinstance(title, str) or not title.strip():
            raise ValueError("Each source must have a title.")

        if not isinstance(url, str) or not url.strip():
            raise ValueError("Each source must have a URL.")

        parsed_url = urlparse(url)

        if parsed_url.scheme not in ("http", "https") or not parsed_url.netloc:
            raise ValueError(f"Invalid source URL: {url}")

        if score is not None and (
            not isinstance(score, (int, float))
            or isinstance(score, bool)
            or not 0.0 <= score <= 1.0
        ):
            raise ValueError("Relevance score must be between 0 and 1.")

        validated_sources.append({
            "title": title.strip(),
            "url": url.strip(),
            "relevance_score": score,
        })

    # Abstentions must not claim to be grounded answers.
    if answer.strip() == ABSTENTION_ANSWER:
        grounded = False

    # An answer without retrieved sources cannot be marked grounded.
    if not validated_sources:
        grounded = False

    # Flag test URLs so callers can distinguish test data from verified sources.
    has_test_source = any(
        urlparse(source["url"]).hostname in (
            "example.org",
            "www.example.org",
        )
        for source in validated_sources
    )

    if has_test_source:
        message = (
            f"{message} WARNING: Test source detected; "
            "do not treat it as a verified heritage source."
        ).strip()

    return {
        "answer": answer.strip(),
        "sources": validated_sources,
        "grounded": grounded,
        "message": message,
    }


if __name__ == "__main__":
    sample_result = {
        "answer": "Agra, Uttar Pradesh, India.",
        "sources": [
            {
                "title": "Taj Mahal",
                "url": "https://example.org/test/taj-mahal",
                "relevance_score": 0.7043,
            }
        ],
        "grounded": True,
        "message": "Answer generated from retrieved context.",
    }

    validated = validate_output(sample_result)

    print("Validation successful.")
    print(validated)

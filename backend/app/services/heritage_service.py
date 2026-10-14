from backend.app.repositories.monument_repository import (
    find_monument,
    get_monument_by_id,
)
from backend.app.schemas.monument import MonumentResponse


def get_monument(monument_id: str) -> MonumentResponse:
    """Return one monument, or raise LookupError if it does not exist."""
    record = get_monument_by_id(monument_id)

    if record is None:
        raise LookupError(f"Monument '{monument_id}' was not found.")

    return MonumentResponse(**record)


def get_heritage_context(destination: str) -> str:
    """Return verified heritage text for a destination, or "" if none is stored.

    Intended for the itinerary generator (Member 6) and the RAG chatbot
    (Member 5), so their answers use the same verified facts and sources.
    """
    record = find_monument(destination)

    if record is None:
        return ""

    monument = MonumentResponse(**record)
    sources = "\n".join(f"- {source.title}: {source.url}" for source in monument.sources)

    return (
        f"{monument.name}, {monument.city}, {monument.state}, {monument.country}\n"
        f"Summary: {monument.summary}\n"
        f"History: {monument.history}\n"
        f"Architecture: {monument.architecture}\n"
        f"Sources:\n{sources}"
    )

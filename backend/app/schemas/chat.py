
from pydantic import BaseModel, Field, ConfigDict


class ChatRequest(BaseModel):
    """Data accepted by POST /api/v1/chat."""

    question: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="The user's heritage-related question",
    )

    session_id: str | None = Field(
        default=None,
        max_length=100,
        description="Optional conversation session identifier",
    )

    top_k: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Number of document chunks to retrieve",
    )


class ChatSource(BaseModel):
    """A source used to construct the chatbot response."""

    title: str
    url: str
    relevance_score: float | None = None


class ChatResponse(BaseModel):
    """Data returned by POST /api/v1/chat."""

    model_config = ConfigDict(extra="forbid")

    answer: str
    sources: list[ChatSource] = Field(default_factory=list)
    grounded: bool
    message: str

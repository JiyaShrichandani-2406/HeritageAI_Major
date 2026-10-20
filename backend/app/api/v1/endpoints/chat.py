from fastapi import APIRouter, HTTPException, status

from backend.app.ai.answer_generator import generate_answer
from backend.app.ai.output_validator import validate_output
from backend.app.schemas.chat import ChatRequest, ChatResponse
from backend.app.schemas.common import ErrorResponse, ValidationErrorResponse


router = APIRouter(tags=["Chat"])


@router.post(
    "/chat",
    response_model=ChatResponse,
    responses={
        400: {
            "description": "The question could not be processed.",
            "model": ErrorResponse,
        },
        422: {
            "description": "The request body failed validation.",
            "model": ValidationErrorResponse,
        },
        503: {
            "description": "The heritage answer service is unavailable.",
            "model": ErrorResponse,
        },
        500: {
            "description": "An unexpected answer-generation error occurred.",
            "model": ErrorResponse,
        },
    },
)
def chat(request: ChatRequest) -> ChatResponse:
    """Answer a heritage question using RAG and Ollama."""

    try:
        result = generate_answer(
            question=request.question.strip(),
            top_k=request.top_k,
        )

        validated_result = validate_output(result)

        return ChatResponse(**validated_result)

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

    except RuntimeError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "The heritage answer service is currently unavailable. "
                "Please try again later."
            ),
        ) from error

    except Exception as error:
        print(f"Unexpected chat endpoint error: {error}")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while generating the answer.",
        ) from error
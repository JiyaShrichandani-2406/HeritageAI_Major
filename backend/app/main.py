"""FastAPI application entry point for HeritageAI."""

from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.app.api.v1.router import api_router
from backend.app.core.config import get_settings

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Keep startup lightweight; AI resources are initialized on demand."""
    logger.info("Starting HeritageAI API")
    yield
    logger.info("Shutting down HeritageAI API")


settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description=(
        "AI-powered Indian cultural heritage explorer "
        "using Retrieval-Augmented Generation (RAG)."
    ),
    version=settings.app_version,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_origins),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def unexpected_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """Log unexpected failures without exposing internal details."""
    logger.error(
        "Unexpected error while handling %s %s",
        request.method,
        request.url.path,
        exc_info=(type(exc), exc, exc.__traceback__),
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


@app.get("/")
def home():
    return {
        "message": "Welcome to HeritageAI API",
        "status": "running",
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
    }


# All versioned endpoints (health, chat, itinerary, ...) live in one router.
app.include_router(api_router)

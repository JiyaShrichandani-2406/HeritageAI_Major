
from fastapi import FastAPI

from backend.app.api.v1.endpoints.chat import router as chat_router


app = FastAPI(
    title="HeritageAI API",
    description=(
        "AI-powered Indian cultural heritage explorer "
        "using Retrieval-Augmented Generation (RAG)."
    ),
    version="1.0.0",
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


app.include_router(chat_router)

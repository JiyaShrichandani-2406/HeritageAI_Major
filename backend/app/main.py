from fastapi import FastAPI

from backend.app.api.v1.router import api_router


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


# All versioned endpoints (health, chat, itinerary, ...) live in one router.
app.include_router(api_router)
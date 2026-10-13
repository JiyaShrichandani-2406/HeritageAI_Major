
from fastapi import FastAPI

from backend.app.api.v1.endpoints.chat import router as chat_router
from backend.app.api.v1.endpoints.itinerary import (
    router as itinerary_router,
)


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


# Member 5: RAG chatbot
app.include_router(chat_router)

# Member 6: AI budget-based itinerary planner
app.include_router(itinerary_router)

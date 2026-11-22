---
title: HeritageAI Backend
emoji: 🛕
colorFrom: orange
colorTo: red
sdk: docker
app_port: 7860
pinned: false
---

# HeritageAI Backend

FastAPI + RAG backend for the HeritageAI project.

- Framework: FastAPI
- Vector store: FAISS
- Embeddings: sentence-transformers
- Generation: Cloudflare Workers AI

## Endpoints

- `GET /` — service info
- `GET /health` — health check
- `/api/v1/...` — chat, itinerary, etc.

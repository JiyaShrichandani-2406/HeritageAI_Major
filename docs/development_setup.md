# HeritageAI - Development Setup

This guide explains how to set up the HeritageAI backend locally for development and testing.

## 1. Prerequisites

- Python 3.11 recommended

- Git

- Internet access for installing Python packages and downloading the embedding model when needed

- Ollama installed locally if you want to use the local language model for AI responses

## 2. Open the project directory

Open a terminal in the repository root, where `README.md` and `requirements.txt` are located.

## 3. Create and activate a virtual environment

On Windows Command Prompt:

```cmd

python -m venv .venv

.venv\Scripts\activate

```

## 4. Install dependencies

Install the runtime dependencies:

```cmd

python -m pip install -r requirements.txt

```

Install development and testing dependencies:

```cmd

python -m pip install -r requirements-dev.txt

```

The development requirements include the runtime dependencies, so installing `requirements-dev.txt` alone is also sufficient for development.

## 5. Configure environment variables

Copy `.env.example` to `.env` in the project root if you need to customize the local configuration.

Keep `.env` local. Do not commit credentials, API keys, or other secrets.

Use the documented environment variable names and valid values from `.env.example` and `backend/app/core/config.py`.

## 6. Prepare the heritage knowledge base

The document loader expects text documents under:

`data/raw/heritage/`

The vector-store builder reads these documents, creates embeddings, and writes the FAISS index and matching chunk metadata under:

`data/vector_store/`

Before running the builder, ensure the required source documents are present. Do not use placeholder or unverified heritage information as authoritative content.

Build the vector store from the repository root:

```cmd

python -m backend.app.rag.vector_store

```

This step may download the embedding model on its first run.

## 7. Start the API

From the repository root, activate the virtual environment and run:

```cmd

python -m uvicorn backend.app.main:app --reload

```

The local API normally listens at:

`http://127.0.0.1:8000`

Interactive API documentation is available at:

`http://127.0.0.1:8000/docs`

## 8. Run tests

Run the complete test suite:

```cmd

python -m pytest -q

```

Run the main application tests:

```cmd

python -m pytest tests/integration/test_main.py -v

```

Run LLM client tests:

```cmd

python -m pytest tests/unit/test_llm_client.py -v

```

Tests that exercise the RAG retriever may require the FAISS index, chunk metadata, and embedding model to be available.

## 9. Git workflow

Check your current branch and working tree:

```cmd

git status -sb

```

Review changes before staging:

```cmd

git diff --check

git diff

```

Stage and commit only files within your task scope. Do not push directly to the main branch. Follow the team's agreed integration and pull-request process.

## 10. Troubleshooting

- **Missing heritage data:** check that source `.txt` files exist under `data/raw/heritage/`.

- **Missing FAISS index or chunks:** run the vector-store builder after preparing the source documents.

- **Embedding model download errors:** check internet access and retry the operation.

- **Configuration errors:** compare `.env` values with the validation rules in `backend/app/core/config.py`.

- **Test failures:** read the first traceback and the final pytest summary before changing code.

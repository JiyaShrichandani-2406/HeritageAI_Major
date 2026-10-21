# HeritageAI — Backend Architecture



## 1. Purpose



HeritageAI is a heritage-information application built with FastAPI. Its backend exposes versioned API endpoints, manages application configuration, and supports AI-powered responses and information retrieval.



This document describes the current backend implementation. Features owned by other team members may be added during the integration phase.



## 2. Backend Directory Structure



```text

backend/

└── app/

    ├── main.py

    ├── core/

    │   ├── config.py

    │   └── \_\_init\_\_.py

    ├── api/

    │   └── v1/

    │       ├── router.py

    │       └── endpoints/

    ├── schemas/

    ├── services/

    ├── rag/

    │   ├── document\_loader.py

    │   ├── text\_splitter.py

    │   ├── vector\_store.py

    │   └── retriever.py

    └── ai/

        └── llm\_client.py



data/

├── raw/

├── samples/

└── vector\_store/



docs/

└── development\_setup.md

```



The structure above represents the main application components. Additional endpoint files and supporting modules may exist inside the directories shown.



## 3. Main Application



\*\*File:\*\* `backend/app/main.py`



The main application module initializes the FastAPI application and provides the following responsibilities:



\- Application metadata and version configuration.

\- Application lifecycle management.

\- CORS middleware configuration.

\- Registration of the central versioned API router.

\- Root and legacy health endpoints.

\- A consistent response for unexpected server errors.



The main application should remain the central entry point rather than duplicating endpoint implementations.



## 4. Configuration Management



\*\*File:\*\* `backend/app/core/config.py`



Centralized configuration manages application settings and environment-specific values.



Configuration includes:



\- Application name and version.

\- Environment settings.

\- Allowed CORS origins.

\- Ollama server URL.

\- Ollama model name.

\- LLM request timeout.

\- Data and storage paths.



Environment variables allow configuration to change without modifying application source code. The `.env.example` file provides a template for local configuration.



Secrets and machine-specific values should not be committed to the repository.



## 5. API Routing



\*\*File:\*\* `backend/app/api/v1/router.py`



The backend uses `/api/v1` as its central API prefix.



The currently registered versioned endpoints are:



| Endpoint | Method | Purpose |

|---|---|---|

| `/api/v1/health` | GET | Check API health |

| `/api/v1/chat` | POST | Submit a heritage-related chat question |

| `/api/v1/itinerary` | POST | Request an itinerary |



The application also exposes `/` and a legacy `/health` endpoint.



Feature-specific endpoint modules are registered through the central router. Additional team-owned endpoints should be registered during the agreed integration phase after their implementations and tests are ready.



## 6. Shared Schemas



\*\*File:\*\* `backend/app/schemas/common.py`



Shared schemas establish consistent structures for responses used across the backend.



The common schema definitions include:



\- `HealthResponse` — health status, service name, and version.

\- `CostStatus` — represents verified, estimated, or unavailable cost information.

\- `ErrorResponse` — common error-response structure.

\- `ValidationError` — validation-error structure.



Unknown costs must not be represented as zero. Cost information should be marked according to its verification status. For itinerary responses, each day's `estimated_cost` and the overall `estimated_total_cost` are null when an included cost is unknown. `known_cost_subtotal` includes only verified prices; a numeric overall estimate may also include estimates. `within_budget` is null whenever any included cost is estimated or unknown, unless verified costs alone already exceed the budget.

Itinerary generation is limited to destinations covered by the local heritage or nearby-place data. An unsupported destination returns an explanatory 422 response instead of being treated as an AI-generation failure.



Feature-specific request and response models should remain with their respective modules unless the team agrees that a model belongs in the shared schema layer.



## 7. AI and RAG Architecture



### 7.1 AI Client



\*\*File:\*\* `backend/app/ai/llm\_client.py`



The AI client communicates with Ollama using the centralized configuration.



Its responsibilities include:



\- Sending prompts to the configured language model.

\- Applying the configured request timeout.

\- Handling connection and response errors.

\- Validating that the generated response contains usable text.



The existing `generate\_response(prompt: str) -> str` interface should be preserved unless a coordinated change is required.



### 7.2 Retrieval-Augmented Generation



\*\*Directory:\*\* `backend/app/rag/`



The RAG subsystem separates document processing and retrieval from language-model communication.



| Module | Responsibility |

|---|---|

| `document\_loader.py` | Load source documents |

| `text\_splitter.py` | Divide documents into smaller text chunks |

| `vector\_store.py` | Build and manage vector-store artifacts |

| `retriever.py` | Retrieve relevant information for a query |



The intended high-level flow is:



1\. Source documents are loaded.

2\. Documents are split into chunks.

3\. Chunks are processed into vector representations and stored in the vector store.

4\. A user query is used to retrieve relevant information.

5\. Retrieved context can be provided to the AI response-generation process.



The exact behavior depends on the current implementation and the availability of valid source documents and vector-store artifacts.



AI-generated answers should not be presented as verified historical facts without appropriate supporting evidence. Where the API contract requires sources, the response should include available supporting references.



## 8. Data and Storage



The repository currently contains the following data directories:



\- `data/raw/` — source data.

\- `data/samples/` — sample data.

\- `data/vector\_store/` — vector-store-related artifacts.



The RAG subsystem uses document-based input and FAISS-based retrieval. The current project does not have a separately configured SQL database or a `backend/app/db/` module.



\*\*Current database decision:\*\* No separate SQL database is configured in the current implementation. The existing document and vector-store approach is retained for the present scope.



This decision does not prevent the team from adding a database later if requirements for persistent structured records, transactions, or other database-backed functionality are established. Any such addition should be agreed upon by the team and documented before implementation.



The `data/processed/` directory is not currently present and should not be treated as an existing component.



## 9. Error Handling and Middleware



The main application configures CORS and a handler for unexpected exceptions.



The intended behavior is to:



\- Allow configured origins according to the CORS settings.

\- Return a consistent generic server-error response for unexpected exceptions.

\- Avoid exposing internal exception details to API clients.

\- Preserve useful server-side diagnostic information through appropriate logging.



Expected validation errors should be handled according to FastAPI's normal request-validation behavior and the applicable endpoint contract.



## 10. Testing and Quality Assurance



The backend includes unit and integration tests.



The test suite covers areas including:



\- Application configuration and metadata.

\- Root and health endpoints.

\- Versioned routing.

\- CORS configuration.

\- LLM-client behavior.



A full test run completed with \*\*54 passing tests\*\* during the current development work. Tests should be run again after changes to verify that the application remains stable.



Run the test suite from the repository root:



```bash

python -m pytest -q

```



## 11. Local Development



Refer to `docs/development\_setup.md` for instructions on:



\- Setting up the development environment.

\- Installing dependencies.

\- Configuring environment variables.

\- Preparing RAG/vector-store data.

\- Starting the FastAPI application.

\- Running tests.

\- Following the Git workflow.



## 12. Integration Boundaries



This document describes the current backend foundation, not a claim that all six members' modules are integrated.



The following activities remain part of team integration:



\- Registering additional feature routers once their modules are ready.

\- Verifying consistency between shared schemas and the API contract.

\- Testing cross-module interactions.

\- Verifying required source attribution and cost-status behavior across features.

\- Updating the API contract and architecture documentation as necessary.



Shared files should have a clearly agreed owner. Changes affecting another member's module or a shared interface should be coordinated before implementation.



\---



\*\*Document status:\*\* Initial backend architecture documentation.



\*\*Scope:\*\* Member 1 — backend foundation and current architecture.



\*\*Note:\*\* Update this document when the team finalizes the integration design or changes the storage architecture.

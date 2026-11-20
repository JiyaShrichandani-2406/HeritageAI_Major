# 🏛️ HeritageAI – AI-Powered Indian Cultural Heritage Explorer

**Discover India's history, monuments, festivals, traditions, and cultural heritage with the power of Artificial Intelligence.**

HeritageAI is an AI-powered web application that helps users explore India's rich cultural heritage through intelligent search, an AI chatbot, heritage information, and itinerary planning. It uses **Retrieval-Augmented Generation (RAG)** to retrieve relevant information from a curated heritage knowledge base and generate context-aware responses.

---

## 📌 Table of Contents

- [About the Project](#-about-the-project)
- [Problem Statement](#-problem-statement)
- [Key Features](#-key-features)
- [Technology Stack](#-technology-stack)
- [System Architecture](#-system-architecture)
- [Project Structure](#-project-structure)
- [Installation and Setup](#-installation-and-setup)
- [Running the Project](#-running-the-project)
- [API Endpoints](#-api-endpoints)
- [RAG Workflow](#-rag-workflow)
- [Data Management](#-data-management)
- [Testing](#-testing)
- [Future Enhancements](#-future-enhancements)
- [Contributing](#-contributing)
- [Author](#-author)

---

## 🌍 About the Project

India has an incredibly diverse cultural heritage, including historical monuments, archaeological sites, religious places, festivals, art, architecture, and traditional practices.

However, heritage-related information is often scattered across multiple websites and resources, making it difficult for users to find relevant and reliable information in one place.

**HeritageAI** addresses this challenge by combining a modern web application with Generative AI and Retrieval-Augmented Generation.

Users can explore heritage information, ask questions through an AI chatbot, discover nearby places, and access itinerary-related information.

The project focuses on making cultural heritage more accessible, interactive, and easier to understand.

---

## 🎯 Problem Statement

Traditional heritage information platforms often provide static information and require users to search through multiple sources.

The major challenges include:

- Difficulty finding relevant heritage information.
- Scattered information about historical places and monuments.
- Lack of interactive question-answering facilities.
- Difficulty discovering nearby attractions and visitor services.
- Challenges in planning visits based on available budget and transport information.
- Risk of receiving unsupported or inaccurate AI-generated historical information.

HeritageAI aims to provide a unified, intelligent platform that improves the way users discover and interact with Indian cultural heritage.

---

## ✨ Key Features

### 1. AI-Powered Heritage Chatbot

- Ask questions about Indian monuments, historical places, and cultural heritage.
- Uses Retrieval-Augmented Generation (RAG).
- Retrieves relevant information from the heritage knowledge base.
- Generates contextual responses using a locally hosted language model through Ollama.
- Supports source-grounded responses based on available retrieved information.

### 2. Heritage Information Explorer

- Explore historical monuments and heritage destinations.
- Access structured information about historical places.
- Discover details such as history, architecture, location, and available references.
- Browse curated heritage records.

### 3. Nearby Places Discovery

- Explore nearby attractions and places of interest.
- Access categorized place information.
- View location-related information and coordinates where available.

### 4. Itinerary Planning

- Generate travel itineraries using available heritage and location data.
- Retrieve relevant attractions and visitor-service information.
- Consider available transport options, estimated costs, and travel durations.
- Support budget-related calculations while distinguishing verified, estimated, and unknown costs.
- Avoid presenting unavailable information as confirmed data.

### 5. Transport and Route Information

- Retrieve transport options between supported locations.
- Display transport type, estimated cost, and duration where available.
- Use directional route records rather than assuming that a reverse route is available.
- Clearly handle unsupported routes and missing information.

### 6. Visitor Services

- Access available visitor-service information.
- Explore services such as food, parking, and guides.
- Display cost information according to its availability and verification status.

### 7. Source-Aware Information

- Maintain source references for curated heritage records.
- Preserve source information during document ingestion and retrieval.
- Distinguish verified, estimated, and unknown information where applicable.

---

## 🛠️ Technology Stack

| Category | Technologies |
|---|---|
| Frontend | React.js, JavaScript |
| Frontend Build Tool | Vite |
| Styling | Tailwind CSS |
| UI Icons | Lucide React |
| Routing | React Router |
| API Communication | Axios |
| Maps | Leaflet, React Leaflet |
| Backend | Python, FastAPI |
| API Server | Uvicorn |
| Data Validation | Pydantic |
| AI / LLM | Ollama, Llama 3.2 |
| RAG Framework | Custom document-based RAG pipeline |
| Vector Store | FAISS |
| Embeddings | Sentence Transformers |
| Data Processing | Python, JSON |
| Testing | Pytest, HTTPX |
| Version Control | Git and GitHub |

---

## 🏗️ System Architecture

HeritageAI follows a frontend-backend architecture.

### Frontend Layer

The React frontend provides the user interface for:

- Heritage exploration.
- AI chatbot interaction.
- Location and nearby-place discovery.
- Itinerary planning.
- Displaying transport and visitor-service information.

### Backend Layer

The FastAPI backend handles:

- REST API requests.
- Request validation.
- Heritage and location data retrieval.
- Itinerary generation.
- Transport and visitor-service lookup.
- AI and RAG integration.

### AI and RAG Layer

The AI subsystem:

1. Loads heritage documents.
2. Splits documents into smaller text chunks.
3. Generates vector representations using an embedding model.
4. Stores and retrieves vectors using FAISS.
5. Retrieves relevant context for user questions.
6. Sends relevant context to the configured language model.
7. Returns a generated response.

### Data Layer

The project uses structured JSON files and document-based vector storage for heritage information, nearby places, transport, and visitor services.

**Note:** The current architecture uses file-based structured data and FAISS rather than a separately configured SQL database.

---

## 📂 Project Structure

```text
HeritageAI_Major/
│
├── backend/
│   └── app/
│       ├── main.py
│       ├── core/
│       │   └── config.py
│       ├── api/
│       │   └── v1/
│       │       ├── router.py
│       │       └── endpoints/
│       ├── schemas/
│       ├── services/
│       ├── repositories/
│       ├── ai/
│       ├── rag/
│       └── ingestion/
│
├── frontend/
│   ├── public/
│   ├── src/
│   ├── package.json
│   └── vite.config.js
│
├── data/
│   ├── raw/
│   ├── processed/
│   │   ├── heritage.json
│   │   ├── nearby_places.json
│   │   ├── transport.json
│   │   └── visitor_services.json
│   └── vector_store/
│
├── docs/
│   ├── architecture.md
│   ├── api_contract.md
│   └── development_setup.md
│
├── scripts/
├── tests/
├── .env.example
├── requirements.txt
├── requirements-dev.txt
└── README.md
```

---

## ⚙️ Installation and Setup

### Prerequisites

Install the following before running the project:

- Python 3.11 (recommended)
- Node.js and npm
- Git
- Ollama
- Visual Studio Code (recommended)

### 1. Clone the Repository

```bash
git clone https://github.com/JiyaShrichandani-2406/HeritageAI_Major.git
```

Navigate into the project:

```bash
cd HeritageAI_Major
```

### 2. Create a Python Virtual Environment

```bash
python -m venv .venv
```

Activate it on Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

### 3. Install Backend Dependencies

```bash
python -m pip install -r requirements-dev.txt
```

### 4. Configure Environment Variables

Create a `.env` file in the project root using `.env.example` as a template.

The default AI configuration uses:

```env
OLLAMA_URL=http://localhost:11434/api/generate
OLLAMA_MODEL=llama3.2:latest
OLLAMA_TIMEOUT_SECONDS=600
```

Keep your local `.env` file private and do not commit secrets.

### 5. Set Up Ollama

Install Ollama and download the configured model:

```bash
ollama pull llama3.2
```

Make sure the Ollama service is running before using AI-powered features.

### 6. Prepare the RAG Knowledge Base

From the project root, run:

```bash
python -m backend.app.ingestion.import_heritage
python -m scripts.rebuild_vector_store
```

This prepares heritage documents and rebuilds the FAISS vector store. The embedding model may need to be downloaded during the first run.

### 7. Install Frontend Dependencies

Open a second terminal:

```bash
cd frontend
npm install
```

---

## 🚀 Running the Project

### Start the Backend

From the project root, activate the virtual environment and run:

```bash
python -m uvicorn backend.app.main:app --reload
```

Backend URL:

```text
http://127.0.0.1:8000
```

Interactive API documentation:

```text
http://127.0.0.1:8000/docs
```

Health check:

```text
http://127.0.0.1:8000/health
```

### Start the Frontend

Open another terminal:

```bash
cd frontend
npm run dev
```

Vite will display the local frontend URL, usually:

```text
http://localhost:5173/
```

Open the displayed URL in your browser.

---

## 🔗 API Endpoints

The backend exposes versioned REST API endpoints under `/api/v1`.

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/` | Welcome message |
| GET | `/health` | Basic backend health check |
| GET | `/api/v1/health` | Versioned API health check |
| POST | `/api/v1/chat` | AI heritage chatbot |
| POST | `/api/v1/itinerary` | Generate itinerary |
| GET | `/api/v1/locations` | Retrieve merged location catalog |
| POST | `/api/v1/routes` | Retrieve supported transport routes |

Additional endpoints for monuments, places, and visitor services are registered in the API router.

Refer to the Swagger documentation at `/docs` for request and response schemas.

---

## 🧠 RAG Workflow

HeritageAI uses Retrieval-Augmented Generation to improve the relevance of AI-generated answers.

```text
        Heritage Source Data
                 |
                 v
         Document Ingestion
                 |
                 v
          Text Processing
                 |
                 v
         Text Chunking
                 |
                 v
       Embedding Generation
                 |
                 v
          FAISS Vector Store
                 |
                 v
          User Question
                 |
                 v
        Relevant Retrieval
                 |
                 v
       Context + User Query
                 |
                 v
          Ollama LLM
                 |
                 v
       Contextual AI Answer
```

This approach allows the chatbot to use retrieved heritage information as context instead of relying only on the language model's general knowledge.

---

## 📊 Data Management

The project maintains structured data for:

- Historical monuments and heritage destinations.
- Nearby attractions and places.
- Transport routes and travel information.
- Visitor services such as guides, food, and parking.

The location API combines heritage and nearby-place records into a unified catalog.

The route system uses origin and destination identifiers and respects the direction of available transport records.

Cost information is classified as:

- **Verified:** Supported by a verified source.
- **Estimated:** An approximate value.
- **Unknown:** No reliable amount is available.

Unknown costs are not treated as zero.

---

## 🧪 Testing

The backend includes unit and integration tests.

Run the complete test suite from the project root:

```bash
python -m pytest -q
```

Run tests with detailed output:

```bash
python -m pytest -v
```

Run a specific test file:

```bash
python -m pytest tests/integration/test_main.py -v
```

---

## 🔮 Future Enhancements

Potential future improvements include:

- Expanding the heritage knowledge base across more Indian states.
- Adding more verified historical and cultural sources.
- Improving multilingual chatbot support.
- Enhancing itinerary personalization.
- Expanding transport and visitor-service coverage.
- Adding richer maps and location-based recommendations.
- Improving response quality and retrieval accuracy.
- Adding more comprehensive end-to-end tests.

---

# LearnGraph API

**A local-first retrieval-augmented generation (RAG) API that turns university lecture PDFs into topic-specific study questions.**

LearnGraph extracts and chunks lecture content, indexes it with semantic embeddings in PostgreSQL, retrieves passages relevant to a requested topic, and generates structured questions and answers using a locally served open-weight language model. Each generated question includes source chunk identifiers for traceability.

**Status:** Working local prototype. PDF ingestion, semantic retrieval, and question generation have been tested end to end. Cloud deployment is not required to run the project.

## Features

- **PDF ingestion:** Upload lecture PDFs and track their processing status.
- **Document processing:** Extract text with `pypdf` and divide it into overlapping chunks.
- **Semantic search:** Generate 384-dimensional embeddings using `sentence-transformers/all-MiniLM-L6-v2` and retrieve related passages with pgvector cosine distance.
- **Local question generation:** Run `qwen2.5:3b` through Ollama without a paid LLM API.
- **Structured responses:** Return questions, answers, difficulty labels, concepts, and source chunk UUIDs using Pydantic validation.
- **Source traceability:** Keep only generated questions whose cited chunk IDs appear in the retrieved context.
- **Interactive API documentation:** Explore the endpoints in FastAPI's Swagger UI.

## Architecture

```mermaid
flowchart TD
    A[Lecture PDF] --> B[FastAPI upload]
    B --> C[Local PDF storage]
    C --> D[pypdf text extraction and chunking]
    D --> E[MiniLM embeddings]
    E --> F[(PostgreSQL + pgvector)]
    G[Topic query] --> H[Query embedding]
    H --> I[Cosine similarity search]
    F --> I
    I --> J[Relevant chunks + source IDs]
    J --> K[Ollama: Qwen 2.5 3B]
    K --> L[Pydantic validation]
    L --> M[Source ID verification]
    M --> N[Questions and answers as JSON]
```

The current development setup runs **PostgreSQL with pgvector in Docker**, while **FastAPI, MiniLM, and Ollama run locally**.

## Technology Stack

| Component | Technology |
| --- | --- |
| API | Python, FastAPI, Uvicorn |
| Database | PostgreSQL, SQLAlchemy |
| Schema migrations | Alembic |
| Vector search | pgvector |
| PDF extraction | pypdf |
| Embeddings | Sentence Transformers (`all-MiniLM-L6-v2`) |
| Language model | Qwen 2.5 3B (`qwen2.5:3b`) |
| Model serving | Ollama |
| LLM communication | HTTPX |
| Validation | Pydantic |
| Local database infrastructure | Docker Compose |

## API

Endpoints are available under `/api/v1`.

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `POST` | `/documents` | Upload a PDF |
| `GET` | `/documents/{document_id}` | Get document metadata |
| `POST` | `/documents/{document_id}/process` | Extract and chunk document text |
| `POST` | `/documents/{document_id}/embed` | Generate and store chunk embeddings |
| `GET` | `/documents/{document_id}/search?query=...&limit=5` | Search document chunks by semantic similarity |
| `POST` | `/documents/{document_id}/generate-questions` | Generate questions about a topic |

### Example: Generate Questions

```http
POST /api/v1/documents/{document_id}/generate-questions
Content-Type: application/json
```

```json
{
  "topic": "Independent Component Analysis",
  "number_of_questions": 3
}
```

Example response (shortened):

```json
{
  "questions": [
    {
      "question": "How does PCA differ from ICA in terms of their objectives?",
      "answer": "PCA seeks directions of maximum variance, while ICA seeks statistically independent components.",
      "difficulty": "medium",
      "concepts": ["PCA", "ICA"],
      "source_chunk_ids": ["79dc4dd2-e1e5-4aba-9b7b-bfb81f07c0ae"]
    }
  ]
}
```

The response above illustrates the API structure; actual questions and source IDs depend on the uploaded document. The model may return fewer questions than requested.

## Getting Started

### Prerequisites

- Python 3 and Git
- Docker Desktop with Docker Compose
- Ollama
- Enough memory and disk space for PostgreSQL, MiniLM, and the Qwen 2.5 3B model

### 1. Clone the repository

```bash
git clone https://github.com/manuviswakarmave/LearnGrph--api.git
cd LearnGrph--api
```

### 2. Set up Python

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it on **Windows PowerShell**:

```powershell
.\.venv\Scripts\Activate.ps1
```

Or on **macOS/Linux**:

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

Create a `.env` file in the repository root:

```dotenv
DATABASE_URL=postgresql+psycopg://learngraph:learngraph_dev@localhost:5432/learngraph
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:3b
```

These credentials are intended for local development only. Do not commit `.env` or reuse development credentials in a public deployment.

### 4. Start PostgreSQL

```bash
docker compose up -d
```

Enable the pgvector extension in the development database if it is not already enabled:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

Apply the database migrations:

```bash
alembic upgrade head
```

### 5. Start Ollama

Install and start Ollama, then download the model:

```bash
ollama pull qwen2.5:3b
```

Ensure the Ollama API is available at `http://localhost:11434`.

### 6. Run FastAPI

```bash
python -m uvicorn app.main:app --reload --port 8001
```

Open **Swagger UI** at **http://localhost:8001/docs**.

### 7. Try the complete pipeline

1. Upload a lecture PDF using `POST /api/v1/documents`.
2. Copy the returned document UUID.
3. Process the document using `POST /api/v1/documents/{document_id}/process`.
4. Create embeddings using `POST /api/v1/documents/{document_id}/embed`.
5. Search for a topic using `GET /api/v1/documents/{document_id}/search`.
6. Generate questions using `POST /api/v1/documents/{document_id}/generate-questions`.

The first embedding operation may download the MiniLM model and take longer than subsequent requests. Question generation time depends on local hardware and model loading.

## Current Limitations

- **Local execution:** The application is not currently hosted on a public cloud server.
- **Grounding:** Source IDs are checked against retrieved chunks, but the system does not yet verify that each answer is factually supported by its cited passage.
- **Mathematical accuracy:** The LLM can produce incorrect formulas or explanations even when its JSON is valid.
- **Retrieval relevance:** Nearest-neighbor retrieval may return unrelated passages if the requested topic is absent from a document.
- **Error handling:** Document-state checks and graceful handling of Ollama failures need further development.
- **Security:** Authentication and rate limiting are not yet implemented; the current API is intended for local use.
- **Setup:** PostgreSQL is containerized, but the complete application is not yet managed by a single Docker Compose setup.

## Roadmap

### Reliability and reproducibility

- [ ] Add document existence and processing-state validation.
- [ ] Handle Ollama connection failures, timeouts, and invalid model responses.
- [ ] Introduce retrieval relevance thresholds and context-size limits.
- [ ] Add automated unit and integration tests.
- [ ] Replace verbose debug output with structured logging.
- [ ] Provide a reproducible multi-container Docker Compose setup.
- [ ] Add a short demonstration video and API screenshots.

### Question quality and educational features

- [ ] Allow users to request difficulty levels and question types.
- [ ] Verify answer grounding against cited source passages.
- [ ] Include evidence snippets and page references in generated responses.
- [ ] Detect duplicate or highly similar questions.
- [ ] Save generated question sets for later retrieval.
- [ ] Evaluate output quality against a curated lecture-question dataset.

### Deployment and product development

- [ ] Explore cloud hosting for the API, database, and model inference.
- [ ] Add authentication, authorization, and rate limiting.
- [ ] Move longer document and inference operations to background jobs.
- [ ] Add monitoring and resource-management controls.
- [ ] Build a frontend for uploading lectures and reviewing questions.

## Engineering Decisions

**Why PostgreSQL with pgvector?** It keeps relational document metadata and vector embeddings in the same database, simplifying the initial architecture.

**Why MiniLM?** Its compact, 384-dimensional embeddings make semantic search practical on local hardware.

**Why Qwen through Ollama?** It allows the application to serve an open-weight model locally without depending on a paid inference API.

**Why structured JSON?** Pydantic provides a predictable API contract and validates field types and constraints. It does not guarantee the correctness of the generated content.

**Why source chunk IDs?** They make generated output traceable to retrieved material and provide a foundation for stronger evidence-based validation.

## Repository

**Source code:** https://github.com/manuviswakarmave/LearnGrph--api

LearnGraph is an ongoing AI and backend engineering project focused on building reproducible, source-aware educational question generation.

# LearnGraph API

**A local-first, retrieval-augmented question generation API for university lecture material.**

LearnGraph converts uploaded lecture PDFs into topic-specific study questions. It extracts and chunks document text, stores semantic embeddings in PostgreSQL with pgvector, retrieves relevant passages, and uses a locally served **Qwen 2.5 3B** model to generate structured questions and answers with references to source chunks.

> **Project status:** Working local prototype. The API, retrieval pipeline, and question generation have been tested end to end. This project is **not currently cloud-hosted**, and its outputs are **not guaranteed to be factually or mathematically correct**.

## Features

- **PDF ingestion:** Upload lecture PDFs and save document metadata.
- **Text processing:** Extract text with `pypdf`, normalize whitespace, and split content into overlapping chunks.
- **Semantic embeddings:** Encode chunks with `sentence-transformers/all-MiniLM-L6-v2` (384-dimensional vectors).
- **Vector search:** Store and retrieve embeddings using PostgreSQL and `pgvector` cosine distance.
- **Local LLM inference:** Generate questions with Qwen 2.5 3B served through Ollama—no paid LLM API required.
- **Structured responses:** Return questions, answers, difficulty labels, concepts, and source chunk IDs, validated with Pydantic.
- **Source ID checks:** Discard generated questions whose cited chunk IDs were not among the retrieved passages.
- **Interactive API documentation:** Explore and test endpoints through FastAPI's Swagger UI.

## Architecture

```mermaid
flowchart TD
    A[Lecture PDF] --> B[FastAPI upload endpoint]
    B --> C[Local PDF storage + document metadata]
    C --> D[pypdf extraction and overlapping chunks]
    D --> E[MiniLM embeddings]
    E --> F[(PostgreSQL + pgvector)]
    G[Topic query] --> H[MiniLM query embedding]
    H --> I[Cosine similarity retrieval]
    F --> I
    I --> J[Retrieved text + source chunk IDs]
    J --> K[Ollama / Qwen 2.5 3B]
    K --> L[Pydantic schema validation]
    L --> M[Retrieved source-ID validation]
    M --> N[JSON questions and answers]
```

**Current execution environment:** FastAPI, embedding inference, and Ollama run locally; PostgreSQL with pgvector runs in Docker. Full multi-service containerization is planned.

## Tech Stack

| Layer | Technology |
| --- | --- |
| API | Python, FastAPI, Uvicorn |
| Data validation | Pydantic |
| Database and ORM | PostgreSQL, SQLAlchemy, Alembic |
| Vector database functionality | pgvector |
| PDF parsing | pypdf |
| Embeddings | Sentence Transformers, `all-MiniLM-L6-v2` |
| Language model | `qwen2.5:3b` via Ollama |
| LLM HTTP client | HTTPX |
| Local database infrastructure | Docker Compose |

## API Endpoints

The application currently exposes the following routes under `/api/v1`:

| Method | Route | Description |
| --- | --- | --- |
| `POST` | `/documents` | Upload a PDF |
| `GET` | `/documents/{document_id}` | Retrieve document metadata |
| `POST` | `/documents/{document_id}/process` | Extract and chunk PDF text |
| `POST` | `/documents/{document_id}/embed` | Generate and store missing chunk embeddings |
| `GET` | `/documents/{document_id}/search?query=...&limit=5` | Retrieve semantically similar chunks |
| `POST` | `/documents/{document_id}/generate-questions` | Generate topic-specific questions from retrieved chunks |

> **Routing note:** Check the paths shown in your running `/docs` page. If your router and endpoint both include `/documents`, you may temporarily see `/api/v1/documents/documents/{document_id}/generate-questions`; remove the duplicate segment in the route decorator.

### Example: Generate Questions

**Request**

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

**Example response (abridged; illustrative)**

```json
{
  "questions": [
    {
      "question": "How does PCA differ from ICA in its objective?",
      "answer": "PCA finds directions that maximize variance, while ICA seeks statistically independent components.",
      "difficulty": "medium",
      "concepts": ["PCA", "ICA", "Statistical Independence"],
      "source_chunk_ids": ["00000000-0000-0000-0000-000000000000"]
    }
  ]
}
```

The UUID above is a placeholder; actual responses contain UUIDs of retrieved chunks in your database. The number of returned questions may be lower than requested if the model produces fewer valid results.

## Running Locally

### Prerequisites

- Python and a virtual environment
- Docker Desktop with Docker Compose
- Ollama installed and running locally
- Git
- Sufficient RAM and disk space to run Qwen 2.5 3B, MiniLM, and PostgreSQL

> **Note:** These are development instructions for the current local-first setup, not a one-command production deployment. Check your repository's dependency and Docker Compose filenames and adjust commands if they differ.

### 1. Clone and configure

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd LearnGraph--api
python -m venv .venv
```

Activate the virtual environment:

```powershell
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
```

Install dependencies using the dependency manifest in the repository (for example, if `requirements.txt` exists):

```bash
pip install -r requirements.txt
```

Create a local `.env` file (do **not** commit it):

```dotenv
DATABASE_URL=postgresql+psycopg://learngraph:learngraph_dev@localhost:5432/learngraph
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:3b
```

These credentials are **local development examples only**. Use distinct, securely managed credentials for any public deployment.

### 2. Start PostgreSQL

Use the repository's existing Docker Compose configuration:

```bash
docker compose up -d
```

Ensure the database has the `vector` extension enabled. If the Compose initialization or migrations do not create it automatically, execute the following against the development database:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

Run database migrations:

```bash
alembic upgrade head
```

### 3. Start Ollama and download the model

```bash
ollama pull qwen2.5:3b
```

Ensure the Ollama service is running and accessible at `http://localhost:11434`. Model weights are downloaded locally and are not stored in this Git repository.

### 4. Start the API

```bash
python -m uvicorn app.main:app --reload --port 8001
```

Open the interactive API documentation:

`http://localhost:8001/docs`

### 5. Try the pipeline

1. Upload a lecture PDF with `POST /api/v1/documents` and copy its `document_id`.
2. Process the document using `POST /api/v1/documents/{document_id}/process`.
3. Generate embeddings with `POST /api/v1/documents/{document_id}/embed`.
4. Test retrieval with `GET /api/v1/documents/{document_id}/search`.
5. Generate questions with `POST /api/v1/documents/{document_id}/generate-questions`.

The first embedding request may take longer because Sentence Transformers downloads the MiniLM model.

## Demo

**Demo video:** _Coming soon_  
**Screenshots:** _Coming soon_

A planned short walkthrough will show PDF upload, chunking, embedding, semantic search, and question generation through Swagger UI. This lets reviewers evaluate the application without installing the models themselves.

## Current Limitations

- **No cloud deployment:** The application currently runs locally.
- **Model hallucinations:** Qwen may produce incorrect or unsupported claims, including mistakes in mathematical notation. Structured JSON and valid source UUIDs do **not** prove factual correctness.
- **Limited grounding verification:** The current implementation verifies that cited UUIDs belong to retrieved chunks, but does not establish that each answer is supported by the cited text.
- **Retrieval quality:** Nearest-neighbor search can return irrelevant passages when no sufficiently relevant passage exists; a calibrated relevance threshold is not yet implemented.
- **Error handling:** Document-state validation and graceful handling of model failures need improvement.
- **No authentication or rate limiting:** The API should not be exposed publicly without additional safeguards.
- **Local orchestration:** Only PostgreSQL is currently containerized; API and Ollama setup still require manual steps.

## Roadmap

### Near term — Reliability and developer experience

- [ ] Add explicit document existence and processing-state checks (`404` / `409`).
- [ ] Handle Ollama timeouts, connection errors, and invalid model responses cleanly.
- [ ] Introduce retrieval relevance thresholds and context-length limits.
- [ ] Add automated unit and integration tests for ingestion, retrieval, and generation.
- [ ] Remove verbose debug output and introduce structured logging.
- [ ] Add an `.env.example` and verify a fresh-clone setup.
- [ ] Containerize FastAPI and Ollama, and provide a reproducible Docker Compose setup.
- [ ] Publish a short demo video and API screenshots.

### Medium term — Educational features

- [ ] Let users request question difficulty and question type.
- [ ] Add stronger answer-grounding checks against cited source passages.
- [ ] Include human-readable evidence snippets and page references.
- [ ] Detect duplicate or overly similar generated questions.
- [ ] Persist generated question sets and support retrieval of past results.
- [ ] Evaluate generation quality on a small curated set of lecture materials.

### Longer term — Deployment and productization

- [ ] Explore low-cost or free-tier hosting for the API, database, and model inference.
- [ ] Add authentication, access controls, and rate limiting.
- [ ] Introduce asynchronous/background processing for longer PDF and inference jobs.
- [ ] Add monitoring, resource limits, and model-serving configuration.
- [ ] Build a simple frontend for document upload, topic selection, and question review.

Roadmap items are **planned features**, not current capabilities.

## Design Notes

- **Why pgvector?** It allows relational document metadata and vector embeddings to live in one PostgreSQL database.
- **Why local Qwen?** It enables experimentation with open-weight model serving without relying on a paid third-party inference API.
- **Why structured output?** Pydantic makes the API response shape predictable and rejects invalid schema data. It does not verify the correctness of the answer itself.
- **Why source chunk IDs?** They provide traceability from generated output back to retrieved lecture passages, forming a foundation for future grounding verification.

## Project Status

LearnGraph is an actively developed educational AI/backend engineering portfolio project. Contributions, feedback, and suggestions are welcome.

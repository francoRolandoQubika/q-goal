---
document_type: service
summary: >-
  The GenAI service is a dedicated FastAPI backend for compute-intensive
  generative AI and face-matching workflows. It runs LangGraph agents for quiz
  generatio...
last_updated: '2026-06-23T20:00:00.000Z'
tags:
  - service
  - python
  - backend
  - fastapi
service_id: genai
---
# GenAI Backend

## Purpose

The GenAI service is a dedicated FastAPI backend for compute-intensive generative AI and face-matching workflows. It runs LangGraph agents for quiz generation, handles face detection and embedding computation, and manages match ranking against pre-indexed player profiles. Separated from the lightweight [[server]] to isolate ML/embedding workloads and allow independent scaling and Python-specific dependency management.

## Public API / Surface

**Face Matching**
- `POST /match` — Upload a photo and receive top-K similar World Cup 2026 player matches. Accepts `UploadFile` (photo), query params `top` (1–20, default 3) and `model` (facenet | clip | insightface, default clip). Returns `MatchResponse` with `PlayerMatch` list including player name, similarity score, and profile URL.

**Quiz**
- `POST /quiz/start` — Initialize a quiz session. Returns session ID and first question.
- `POST /quiz/{session_id}/answer` — Submit an answer. Returns feedback and next question or session completion state.

Other endpoints as defined in `genai/src/genai/api.py`. Runs on port 8002 and can be invoked by [[server]] via HTTP or run standalone for the ETL pipeline.

## Internal Architecture

FastAPI application with Pydantic BaseModel request/response schemas. Startup event pre-loads player embedding matrices (FacenetV2, CLIP, InsightFace) into memory for fast inference. LangGraph agent integration manages quiz state and question generation via ChatOpenAI. File uploads temporarily stored via Python's `tempfile` module for preprocessing before embedding computation. No persistent session storage—quizzes held in memory (`_sessions` dict) for the lifetime of the server process.

## Request Lifecycle

**Face Matching Flow:**
1. Receive file upload (POST /match with UploadFile)
2. Preprocess user photo (resize, normalize)
3. Compute embedding via selected model (facenet/clip/insightface)
4. Compute cosine similarity against pre-loaded player embedding matrix
5. Sort results, return top-K matches with scores and metadata

**Quiz Flow:**
1. Receive quiz start request (POST /quiz/start)
2. Initialize LangGraph agent state with player context
3. ChatOpenAI generates opening question JSON (system prompt + player metadata)
4. Store session in `_sessions`, return session ID and question
5. On answer submission, invoke agent node for feedback, advance state
6. Return next question or completion summary

## Data Layer

- **Embedding matrices** — Pre-computed player embeddings (facenet, clip, insightface) loaded at startup into NumPy arrays; enables O(1) lookup and batched similarity computation.
- **Quiz sessions** — Ephemeral in-memory dictionary (`_sessions`); each entry holds LangGraph agent state, current question, and answer history.
- **Player metadata** — PostgreSQL via `genai/core/db.py`; stores player profiles, embeddings references, and quiz history for audit.

## Configuration

| Variable | Purpose |
| --- | --- |
| `OPENAI_API_KEY` | OpenAI API key for ChatOpenAI LLM in quiz generation |
| `DATABASE_URL` | PostgreSQL connection string for metadata and embeddings |
| `MODEL_SELECTION` | Default embedding model (clip, facenet, insightface) |
| `STATS_PDF` | Path to the FIFA player stats PDF used by the pipeline. Defaults to `genai/statsFifa.pdf` (committed to the repo); `uv run genai-pipeline` works without extra flags. |

## Integrations

- **[[PostgreSQL]]** (port 5433) — Stores player metadata, embeddings vectors, quiz history, and match audit logs. Connected via `genai/core/db.py` using SQLAlchemy or raw SQL.
- **OpenAI API** — `langchain-openai` integration for quiz question generation via ChatOpenAI. Called during quiz initialization and answer evaluation.
- **Google Generative AI** (optional) — `langchain-google` can be substituted for OpenAI; configured via environment variable.
- **File Processing** — Temporary storage via Python `tempfile` for user-uploaded photos during preprocessing.

## Service-Specific Patterns

**Startup Embedding Preload** — On application startup, `@app.on_event("startup")` loads all player embedding matrices into memory. Eliminates per-request disk I/O and allows vectorized similarity computation.

**In-Memory Session State** — LangGraph agent state persisted in-process during quiz lifetime; no database round-trip per turn. Sessions cleared on server restart (acceptable for demo/pilot deployments; production use would persist to Redis or PostgreSQL).

**Pydantic Request/Response Models** — All endpoints use Pydantic BaseModel for validation and OpenAPI schema auto-generation. Client can deserialize typed JSON responses.

**Model Polymorphism** — Face-matching endpoint accepts model parameter to select embedding algorithm at runtime, enabling A/B testing and fallback logic without redeployment.

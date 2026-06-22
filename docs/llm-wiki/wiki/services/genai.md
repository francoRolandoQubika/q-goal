---
document_type: service
summary: >-
  genai is a Python FastAPI service (port 8002) for World Cup 2026 face matching
  and an office quiz. It owns an ETL pipeline (scrape → crop → embed → db →
  enrich) that builds a local SQLite database of player photos and embeddings
  using DeepFace, CLIP, and InsightFace. At runtime it exposes REST endpoints
  for face matching and a LangGraph-backed quiz agent.
last_updated: '2026-06-22T00:00:00.000Z'
tags:
  - service
  - python
  - fastapi
  - cli
  - ai
service_id: genai
---
# genai

## Purpose

genai is a standalone Python FastAPI service that powers two features for the WC2026 office experience:

1. **Face match** — upload a photo, get the player who looks most like you (3 embedding models)
2. **Office quiz** — 4 Spanish questions → LLM assigns a "dream office team" of WC2026 players

It is entirely self-contained: its own SQLite database (`players.db`), its own embedding matrices (`.npy` files), and its own ETL pipeline to build them from scratch.

## Public API / Surface

**CLI commands (via `uv run`):**
- `uv run genai-pipeline` — Run the full ETL pipeline (see ETL Pipeline section)
- `uv run genai-api` — Start the FastAPI server on port 8002

**HTTP endpoints (port 8002):**
- `POST /match` — Upload image → returns top-N matching players
- `GET /players` — List all players in the DB
- `GET /faces/{player_id}` — Serve a cropped face image
- `POST /quiz/start` — Start a quiz session → returns first question
- `POST /quiz/answer` — Submit answer → returns next question or final team

## Internal Architecture

```
genai/src/genai/
├── api.py              FastAPI app, all HTTP routes
├── pipeline.py         ETL orchestrator (5 steps, skip logic, --force)
├── core/
│   ├── config.py       .env loader; DATA_DIR = genai/ root; STATS_PDF env var
│   └── db.py           SQLite: players table, get_conn(), get_all_embeddings()
├── etl/
│   ├── scraper.py      FIFA API → players/{team_slug}/{player}.jpg
│   ├── crop.py         DeepFace + rembg → faces/{team_slug}/{player}.jpg (300×300, green bg)
│   ├── embeddings.py   Builds embeddings*.npy for facenet / clip / insightface
│   └── enrich.py       pdfplumber → adds position/dob/club/height/caps/goals to players.db
├── matching/
│   └── engine.py       Cosine similarity across all 3 embedding models
└── agent/
    ├── questions.py    Quiz themes and OUTPUT_SLOTS
    ├── nodes.py        LangGraph nodes (dynamic LLM question generation)
    └── graph.py        LangGraph compile, start_session(), submit_answer()
```

**Key files:**
- `DATA_DIR` = `genai/` repo root (set in `core/config.py` via `Path(__file__).parents[3]`)
- `players.db` — SQLite, gitignored, rebuilt by pipeline
- `embeddings.npy`, `embeddings_clip.npy`, `embeddings_insightface.npy` — gitignored
- `metadata.json` — face index written by embeddings step (facenet pass)

## ETL Pipeline

Run with `uv run genai-pipeline [--steps …] [--models …] [--stats-pdf /path] [--force]`.

| Step | Module | Output |
|------|--------|--------|
| scrape | `genai.etl.scraper` | `players/{team_slug}/*.jpg` — 48 squads, ~1 200 photos |
| crop | `genai.etl.crop` | `faces/{team_slug}/*.jpg` — 300×300, green background |
| embed | `genai.etl.embeddings` | `embeddings*.npy` + `metadata.json` |
| db | `genai.core.db.get_conn` | `players.db` (SQLite) |
| enrich | `genai.etl.enrich` | Adds stats columns from `statsFifa.pdf` |

**Skip logic:** each step is skipped if its output already exists (override with `--force`).

**`slugify()` in scraper.py:** strips Unicode accent marks via NFD normalization before producing folder names — required because DeepFace rejects image paths containing non-ASCII characters.

## Data Layer

**SQLite schema (`players.db`):**
```sql
players(
  id INTEGER PK, name TEXT, team TEXT, face_path TEXT,
  embedding BLOB,      -- FaceNet512 float32 bytes
  position TEXT,       -- GK/DF/MF/FW  (added by enrich step)
  dob TEXT,            -- DD/MM/YYYY
  club TEXT,
  height_cm INTEGER,
  caps INTEGER,
  goals INTEGER
)
```

No PostgreSQL dependency — genai uses SQLite only and is fully independent of the `@q-goal/db` package.

## Configuration

All env vars go in `genai/.env` (gitignored). Loaded at import time by `core/config.py` via python-dotenv.

| Variable | Description |
|----------|-------------|
| `OPENAI_API_KEY` | Required for the quiz LangGraph agent |
| `STATS_PDF` | Absolute path to `statsFifa.pdf` for the enrich step |
| `API_PORT` | FastAPI port (default: 8002) |

Frontend must set `VITE_GENAI_URL=http://localhost:8002`.

## Embedding Models

| Model | File | Dim | Notes |
|-------|------|-----|-------|
| FaceNet512 | `embeddings.npy` | 512 | Identity verification; canonical pass writes `metadata.json` |
| CLIP ViT-L/14 | `embeddings_clip.npy` | 768 | Default for `/match` — best "lookalike" feel |
| InsightFace buffalo_l | `embeddings_insightface.npy` | 512 | ArcFace, L2-normalised |

## Service-Specific Patterns

- **Green background (#00B140)** on all face crops — ensures models compare faces, not backgrounds
- **CLIP is the default match model** — better lookalike results than identity models
- **LangGraph interrupt pattern** — each quiz `session_id` = LangGraph `thread_id`; state lives in `MemorySaver` (resets on server restart)
- **Dynamic question generation** — LLM creates fresh questions each session from 4 themes
- **Progressive PDF parsing** — `enrich.py` detects column positions dynamically from the PDF header row

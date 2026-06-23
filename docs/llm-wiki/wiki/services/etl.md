---
document_type: service
summary: >-
  The ETL service is a Python CLI that orchestrates the bulk ingestion and
  processing of images for the World Cup 2026 face-matching pipeline. It invokes
  the g...
last_updated: '2026-06-23T03:08:58.598Z'
tags:
  - service
  - python
  - cli
service_id: etl
---
# ETL

## Purpose

The ETL service is a Python CLI that orchestrates the bulk ingestion and processing of images for the World Cup 2026 face-matching pipeline. It invokes the genai pipeline module to coordinate face detection, embedding computation, and metadata persistence in PostgreSQL. The service is designed as a one-shot or scheduled job runner that transforms raw image inputs into queryable face embeddings.

## Public API / Surface

- `uv run etl` — Entry point for the CLI (currently a placeholder)
- `uv run genai-pipeline` — Primary command to execute the WC2026 face-matching ETL pipeline

The CLI is thin; actual pipeline logic resides in [[genai]]'s `src/genai/pipeline.py` module.

## Internal Architecture

The etl package is a minimal Python CLI wrapper with a single entry point (`src/etl/__init__.py`). It delegates all processing to the [[genai]] service. The architecture favors simplicity: etl serves as the orchestration layer and job scheduler, while heavy lifting (face detection, embeddings) is handled by genai's LangGraph-based pipeline.

## Request Lifecycle (Job Lifecycle)

1. User invokes `uv run genai-pipeline` (via etl or directly)
2. etl/genai pipeline module loads configuration and connects to PostgreSQL
3. Image metadata is fetched from database
4. Face detection runs on each image (deepface/insightface)
5. Embedding vectors are computed for detected faces
6. Embeddings and match metadata are persisted to PostgreSQL
7. Pipeline completes; results become queryable by [[server]]'s `/matches` endpoint

## Data Layer

The etl service does not own any data stores. It accesses:
- **PostgreSQL** (port 5433) — reads image metadata, writes computed embeddings and match results via [[genai]]'s pipeline module

## Configuration

(no environment variables consumed)

Environment configuration (DATABASE_URL, OPENAI_API_KEY, etc.) is inherited from the parent [[genai]] service when the pipeline executes.

## Integrations

- **[[genai]]** — Face-matching pipeline module invoked as the primary workhorse; etl coordinates its execution
- **[[db]]** — PostgreSQL schema and connection, accessed via genai's database module
- **External ML libraries** — deepface, insightface (depended on by genai, not directly by etl)

## Service-Specific Patterns

**CLI-as-orchestrator**: The etl package is intentionally thin, providing a CLI entry point that launches the actual pipeline logic in genai. This pattern allows future expansion of etl with additional subcommands (for different batch jobs) without duplicating pipeline code.

**Stub implementation**: The current `uv run etl` command is incomplete; the real ETL work happens in genai's pipeline module. This separation allows genai to be tested and invoked independently while etl evolves as a higher-level scheduling and orchestration layer.

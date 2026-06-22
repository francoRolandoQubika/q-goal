---
document_type: service
summary: >-
  The etl service is a Python CLI for data pipeline operations within the q-goal
  monorepo. It is designed to read from PostgreSQL tables, perform
  transformatio...
last_updated: '2026-06-18T21:06:25.817Z'
tags:
  - service
  - python
  - cli
service_id: etl
---
# ETL Service

## Purpose

The etl service is a Python CLI for data pipeline operations within the q-goal monorepo. It is designed to read from PostgreSQL tables, perform transformations, and post results back to the Hono server for persistence. The service runs independently on schedules or can be triggered by server webhooks.

## Public API / Surface

**CLI entry point:**
- `uv run etl` — Executes the ETL pipeline

**Current behavior:** The service prints "Hello from etl!" on invocation.

**Interface:** Command-line only; no HTTP endpoints or library exports.

## Internal Architecture

The etl service is a minimal Python package managed by the uv workspace system (separate from the Bun npm workspace). The service entry point is located at `etl/src/etl/__init__.py`.

**Build & execution:**
- Manifest: `etl/pyproject.toml`
- Runtime: Python 3.13
- Package manager: uv

**Code quality:**
- Linting & formatting: Ruff (`uv run ruff check --fix` / `uv run ruff format`)
- Testing framework: (not determined by analysis)

## Request Lifecycle (or Job Lifecycle)

The etl service follows a read-transform-post pipeline:

1. **Initialization** — CLI invoked via `uv run etl`
2. **Data ingestion** — Reads from PostgreSQL tables via introspection of the [[db]] schema
3. **Transformation** — Processes raw data according to pipeline logic
4. **Persistence** — POSTs transformed results back to the [[server]] at a designated endpoint (e.g., `/api/etl/result`)
5. **Server-side upsert** — The server receives the payload and writes results into PostgreSQL via Drizzle ORM
6. **Polling** — The [[web]] frontend polls the server's `/status` endpoint to subscribe to changes (WebSocket integration is not yet implemented)

## Data Layer

**Read access:**
- PostgreSQL database (port 5433) — introspects schema from [[db]] package
- Tables: (not determined by analysis)

**Write access:** None directly; results are POSTed to the server, which handles persistence.

## Configuration

Environment variables: (not determined by analysis)

Likely candidates (inferred from typical ETL setups):
- `DATABASE_URL` — PostgreSQL connection string
- `SERVER_URL` — Hono server base URL for result posting

## Integrations

**[[server]]** (outbound)
- POSTs transformed data to a server endpoint for upsert

**[[db]]** (read-only)
- Introspects PostgreSQL schema to construct queries
- Reads from PostgreSQL directly

**PostgreSQL** (database)
- Direct table reads for source data

## Service-Specific Patterns

- **CLI-as-pipeline:** The entire service is invoked as a command-line tool with no persistent runtime; suitable for scheduled jobs or webhook triggers.
- **Stateless transformation:** No internal state or caching; each invocation is independent.
- **Server handoff pattern:** Results are not persisted locally; the service POSTs to the server, delegating storage to the backend.

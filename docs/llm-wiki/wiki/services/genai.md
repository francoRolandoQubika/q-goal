---
document_type: service
summary: >-
  genai is a Python CLI service for AI-powered data transformations and
  integrations. It reads from PostgreSQL tables (via the [[db]] package schema)
  and posts...
last_updated: '2026-06-18T21:06:25.817Z'
tags:
  - service
  - python
  - cli
service_id: genai
---
# genai

## Purpose

genai is a Python CLI service for AI-powered data transformations and integrations. It reads from PostgreSQL tables (via the [[db]] package schema) and posts results back to the [[server]] for upsert into the database. The service is designed to run independently on schedules or be triggered by server webhooks, enabling asynchronous AI feature processing outside the request-response cycle.

## Public API / Surface

**CLI Commands:**
- `uv run genai` — Execute the genai CLI

**Integration Points:**
- **Inbound:** Server webhooks or scheduled triggers (not determined by analysis)
- **Outbound:** HTTP POST to the Hono server at `/api/genai/*` (not determined by analysis)

## Internal Architecture

genai follows a standalone CLI pattern, separate from the npm workspace and managed by uv instead of Bun. The service entry point is `genai/src/genai/__init__.py`. Currently minimal in scope, the service is structured to:

1. Read PostgreSQL schemas via introspection of `@q-goal/db`
2. Transform or enrich data using AI models
3. POST transformed results back to the server for persistence

No internal middleware, dependency injection, or middleware pipeline is present in the current implementation.

## Request Lifecycle

For a typical genai job invoked by schedule or webhook:

1. **Trigger:** Server sends webhook POST or job scheduler invokes `uv run genai`
2. **Connect:** Service connects to PostgreSQL using connection string from environment
3. **Read:** Query source tables via Drizzle schema introspection
4. **Process:** Apply AI transformations (not determined by analysis)
5. **POST:** Send results back to server `/api/genai/*` endpoint
6. **Upsert:** Server receives POST and writes results to database
7. **Notify:** Web polls `/status` endpoint to reflect changes in UI

## Data Layer

**Owned Data:** (not determined by analysis)

**Read Access:**
- All PostgreSQL tables via schema introspection of [[db]] (e.g., user accounts, sessions, custom domain tables)

**Write Access:** (indirect, via server POST)
- Results written by the server based on genai responses

## Configuration

**Environment Variables:**
- `DATABASE_URL` — PostgreSQL connection string (inherited from server/.env or shared .env)
- (additional variables: not determined by analysis)

## Integrations

**External Services:**
- [[db]] (PostgreSQL via schema introspection)
- [[server]] (HTTP POST endpoint for result delivery)
- (AI model provider: not determined by analysis)

**Inbound:**
- Scheduled triggers or server webhooks

## Service-Specific Patterns

(not determined by analysis)

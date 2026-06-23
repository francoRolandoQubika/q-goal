---
document_type: architecture
summary: >-
  q-goal is a unified npm workspaces monorepo combining TypeScript (Bun-managed)
  and Python (uv-managed) workspaces in a single repository. The structure
  separ...
last_updated: '2026-06-23T03:08:58.598Z'
tags:
  - architecture
  - topology
  - typescript
  - react
  - tanstack-router
---
# Architecture

## Monorepo / Repository Shape

q-goal is a unified npm workspaces monorepo combining TypeScript (Bun-managed) and Python (uv-managed) workspaces in a single repository. The structure separates application services (`apps/*`), shared libraries (`packages/*`), and Python microservices at the root level.

| Workspace | Path | Type | Language | Role |
| --------- | ---- | ---- | -------- | ---- |
| Web | `apps/web` | frontend | TypeScript | React 19 SPA with TanStack Router |
| Server | `apps/server` | backend | TypeScript | Hono REST API gateway |
| GenAI | `genai/` | backend | Python | FastAPI + LangGraph for AI/ML workloads |
| ETL | `etl/` | cli | Python | Stub CLI for future data pipelines |
| Auth | `packages/auth` | library | TypeScript | Better-Auth configuration and exports |
| DB | `packages/db` | library | TypeScript | Drizzle ORM schema and client |
| UI | `packages/ui` | library | TypeScript | React component library with Base UI |

The monorepo uses npm workspaces as the primary tool for TypeScript packages and maintains separate dependency management for Python via `pyproject.toml`. All JavaScript/TypeScript services import shared packages using the `@q-goal/<name>` alias (never relative paths), ensuring clean boundaries and enabling independent versioning.

## Service Inventory

| Service ID | Name | Type | Language | Port | Role |
| ---------- | ---- | ---- | -------- | ---- | ---- |
| [[web]] | Web Application | Frontend | TypeScript 6.x | 3001 | React 19 + TanStack Router SPA |
| [[server]] | API Server | Backend | TypeScript 6.x | 3000 | Hono 4.8.2 REST API gateway |
| [[genai]] | GenAI Backend | Backend | Python 3.13 | 8002 | FastAPI 0.137 + LangGraph for AI pipelines |
| [[etl]] | ETL CLI | CLI | Python 3.13 | — | Stub Python CLI for future ETL tasks |
| [[auth]] | Authentication Library | Library | TypeScript 6.x | — | Better-Auth 1.6.11 session config |
| [[db]] | Database Library | Library | TypeScript 6.x | — | Drizzle ORM 0.45.1 schema + client |
| [[ui]] | UI Component Library | Library | TypeScript 6.x | — | React 19 + Base UI 1.0.0 components |

## Service Communication

**Browser → [[web]]**: HTTP requests from user agents routed by TanStack Router to client-side handlers.

**[[web]] → [[server]]**: REST API calls from React components to the Hono API gateway (same-origin on localhost:3000 or production API endpoint). Includes authentication via session cookies or Authorization header.

**[[server]] → [[db]]**: All data access funneled through the Drizzle ORM client exported from `@q-goal/db`, ensuring type-safe parameterized queries against PostgreSQL.

**[[server]] → [[auth]]**: Session validation middleware extracts and verifies tokens from request cookies/headers using the Better-Auth session schema. User context attached to request handler for authorization checks.

**[[genai]] → PostgreSQL**: Direct database connections via Drizzle client for storing and retrieving embeddings, match metadata, and pipeline state. Uses same schema as [[server]].

**[[genai]] → External LLM APIs**: Outbound HTTPS calls to Google Generative AI and OpenAI for model inference. API credentials managed via environment variables.

**[[server]] → [[genai]]**: (Not determined by analysis)

## External Integrations

| Vendor | Purpose | Client Path | Auth Mechanism | Environments |
| ------ | ------- | ----------- | --------------- | ------------ |
| Google Generative AI | LLM inference for face-matching and enrichment pipelines | `genai/src/genai/` | API key (env var) | dev, staging, production |
| OpenAI | Alternative LLM provider for generation tasks | `genai/src/genai/` | API key (env var) | dev, staging, production |

## Authentication & Authorisation

Authentication uses Better-Auth 1.6.11 configured centrally in [[auth]]. The flow is:

1. **Session Minting**: User submits credentials (email/password or OAuth provider) to [[server]] authentication endpoint.
2. **Token Generation**: Better-Auth creates a signed session token stored in HTTP-only cookies and (for API clients) in Authorization headers.
3. **Middleware Validation**: [[server]] middleware intercepts each request, extracts the session token from cookies or headers, and validates it against the Better-Auth session schema in PostgreSQL.
4. **Request Context**: On valid session, `req.user` is populated with authenticated user attributes (id, role, email, etc.) and attached to the handler context.
5. **Authorization Checks**: Endpoints inspect `req.user.role` or other attributes and return 401 (unauthenticated) or 403 (forbidden) as needed.
6. **Client-Side Protection**: [[web]] maintains client-side auth state via the Better-Auth client library, checking session validity before rendering protected routes. Invalid sessions redirect to login.

## Request Lifecycle

**Common Browser Request (Authenticated User)**

1. User navigates in [[web]] SPA; TanStack Router matches the URL and loads the route component.
2. React component calls a server API function (e.g., `fetch('/api/goals')`) with the session cookie automatically attached by the browser.
3. Request arrives at [[server]] Hono handler on port 3000.
4. Better-Auth middleware in [[server]] extracts session token from cookie and validates it against PostgreSQL via Drizzle.
5. If valid, `req.user` is hydrated; if invalid, handler returns 401 Unauthorized.
6. Authenticated handler queries [[db]] (Drizzle ORM) to fetch user's goals from PostgreSQL.
7. [[server]] serializes the response as JSON and sends it back to [[web]].
8. React component receives the response, updates local state, and re-renders.

**GenAI Pipeline Request**

1. [[server]] endpoint receives a file upload or trigger to start a face-matching pipeline.
2. [[server]] enqueues the job or calls [[genai]] FastAPI endpoint on port 8002 with task parameters.
3. [[genai]] FastAPI handler orchestrates a LangGraph workflow, invoking `parse_pdf` and other ETL steps in `src/genai/etl/`.
4. LangGraph calls external LLM APIs (Google Generative AI, OpenAI) for inference and embeddings.
5. [[genai]] persists embeddings and match metadata to PostgreSQL via Drizzle.
6. [[genai]] returns job status or results to [[server]]; [[web]] polls or subscribes for updates.

## Data Architecture

**PostgreSQL** (remapped to host port 5433 to avoid collision with local Postgres.app on 5432) is the single operational data store.

**Schema Management**: Drizzle ORM stores all table definitions in `packages/db/src/schema/` organized by domain:
- `auth.ts` — Better-Auth tables (users, sessions, accounts, verificationTokens)
- Application domain tables (goals, matches, embeddings, etc.)

**Migrations**: Code-first via Drizzle Kit. Running `bun run --filter @q-goal/db db:push` applies schema changes. Schema is the source of truth; no hand-rolled SQL.

**Client Access**: All services ([[server]], [[genai]]) import the Drizzle client from `@q-goal/db/src/index.ts`, ensuring schema consistency and preventing drift. Parameterized queries mitigate SQL injection.

**Local Development**: Docker Compose spins up a fresh PostgreSQL container on startup; persistent volumes store data across restarts.

## Deployment Topology

(not determined by analysis)

## Local Development

**Full Docker Stack**:
```
bun run docker:up
```
Builds and starts [[web]] (port 3001), [[server]] (port 3000), and PostgreSQL (host port 5433) in isolated containers. Use this workflow when you want containers to manage service dependencies.

**Local with Hot Reload**:
```
bun run db:start      # starts postgres only in docker
bun run dev           # starts web + server in dev mode
uv run genai-api      # starts genai service (port 8002) in a separate terminal
```
Allows rapid iteration with live reloading for TypeScript and Python code while PostgreSQL runs in Docker.

**Database Migrations**:
```
bun run db:push       # applies schema changes from packages/db
```

**Python Dependency Sync**:
```
uv sync               # resolves genai and etl dependencies
```

**Linting & Formatting**:
- TypeScript: `oxlint && oxfmt --write`
- Python: `uv run ruff check --fix && uv run ruff format`

**Type Checking**:
```
bun run check-types   # TypeScript across all workspaces
```

## Automation & CI

**Package Manager Scripts**: npm scripts defined in `package.json` (root and per-package) orchestrate builds, dev servers, and migrations via Bun. Key entry points:
- `bun run docker:up` — full stack in Docker
- `bun run dev` — [[web]] + [[server]] with hot reload
- `bun run db:push` — Drizzle migrations
- `bun run check-types` — TypeScript validation

**Python CLI**: uv manages Python dependency resolution and task execution:
- `uv run etl` — [[etl]] CLI stub
- `uv run genai-api` — [[genai]] FastAPI server
- `uv run genai-pipeline` — face-matching WC2026 pipeline

**Linting & Formatting**:
- JavaScript/TypeScript: Oxlint (Rust-based, faster than ESLint) with Oxfmt
- Python: Ruff for linting and formatting

**CI Provider**: (not determined by analysis)

## Coupling Hotspots

- `genai/src/genai/etl/enrich.py::parse_pdf` (Function, hub score 61) — central PDF parsing step for the face-matching pipeline; called by multiple LangGraph workflow branches.
- `genai/src/genai/core/db.py::get_conn` (Function, bridge score 0.000073) — bridges [[genai]] to PostgreSQL; all database access routes through this factory.
- `apps/web/src/components/user-menu.tsx::UserMenu` (Function, bridge score 0.00007) — widely composed header/layout component; refactors ripple across page layouts.
- `packages/ui/src/lib/utils.ts::cn` (Function, hub score 0.000064) — class-name merging utility used across all Base UI component compositions; changes affect styling consistency.

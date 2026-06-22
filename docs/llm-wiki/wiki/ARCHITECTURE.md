---
document_type: architecture
summary: >-
  **q-goal** is a TypeScript-dominant monorepo structured around two separate
  workspace systems:
last_updated: '2026-06-18T21:06:25.817Z'
tags:
  - architecture
  - topology
  - typescript
  - react
  - hono
---
# Architecture

## Monorepo / Repository Shape

**q-goal** is a TypeScript-dominant monorepo structured around two separate workspace systems:

- **JavaScript/TypeScript workspace**: managed by Bun and npm workspaces, with applications in `apps/*` (web frontend, server backend) and shared packages in `packages/*` (auth config, database ORM, UI component library).
- **Python workspace**: managed by uv, with CLI packages for data pipelines (etl, genai) isolated under separate `pyproject.toml` files to avoid version conflicts with the JS toolchain.

The monorepo uses Bun as the primary package manager for the TypeScript portion and Docker Compose to orchestrate the full local stack (frontend, backend, and PostgreSQL).

| Workspace | Path | Type | Purpose |
| --------- | ---- | ---- | ------- |
| web | `apps/web` | Frontend application | React 19 + TanStack Router SPA |
| server | `apps/server` | Backend application | Hono REST API + auth/DB integration |
| auth | `packages/auth` | Shared library | Better-Auth configuration |
| db | `packages/db` | Shared library | Drizzle ORM schema + database client |
| ui | `packages/ui` | Shared library | Reusable React UI components |
| etl | `etl/` | Python CLI | Data pipeline orchestration |
| genai | `genai/` | Python CLI | AI services and integrations |
| postgres | (Docker Compose) | Database | PostgreSQL OLTP store |

## Service Inventory

| Service | Type | Language | Port | Role |
| ------- | ---- | -------- | ---- | ---- |
| [[web]] | Frontend | TypeScript | 3001 | React 19 single-page application with TanStack Router |
| [[server]] | Backend | TypeScript | 3000 | Hono REST API, session middleware, AI SDK integration |
| [[auth]] | Library | TypeScript | — | Better-Auth session & user management, exported config |
| [[db]] | Library | TypeScript | — | Drizzle ORM schema definitions, client, migrations |
| [[ui]] | Library | TypeScript | — | Shared React components (buttons, forms, layout primitives) |
| [[etl]] | CLI | Python 3.13 | — | Data extraction and transformation pipeline runner |
| [[genai]] | CLI | Python 3.13 | — | AI model integrations and batch operations |
| postgres | Database | PostgreSQL | 5433 | Operational data store (OLTP) |

## Service Communication

Inter-service dependencies flow through package imports and HTTP requests:

- **web → server**: REST API calls over HTTP (unencrypted in dev, TLS in production). Requests for authentication state, data queries, and AI inference endpoints.
- **web → ui**: Import shared components (`@q-goal/ui`) at build time; no runtime call.
- **server → auth**: Imports Better-Auth configuration (`@q-goal/auth`) to validate session cookies and manage user sessions.
- **server → db**: Imports Drizzle ORM client and schemas (`@q-goal/db`) to query PostgreSQL.
- **server → postgres**: TCP connection over port 5433 (local) or Postgres network alias (Docker) for all data operations.
- **etl, genai ↔ external APIs**: Direct HTTP calls to external AI services and data sources (e.g., Google AI SDK, third-party data warehouses).

## External Integrations

| Integration | Type | In-Repo Client | Auth | Notes |
| ----------- | ---- | -------------- | ---- | ----- |
| Google AI SDK (`@ai-sdk/google`) | LLM inference | `apps/server` (imports directly) | API key via env var | Used for AI endpoint responses on backend |
| AI SDK React (`@ai-sdk/react`) | Client-side AI hooks | `apps/web` (imported directly) | Token passed from backend | Streaming responses to UI |

## Authentication & Authorization

**Authentication Flow:**
Better-Auth manages the complete session lifecycle. When a user logs in, the auth package (packages/auth) stores session tokens in PostgreSQL tables and issues session cookies. The server middleware on every protected route verifies that the session cookie is valid and has not expired. If valid, the session context is attached to the request; otherwise, the request is rejected or redirected to login.

**Session Storage:**
- **User table**: Contains user identity (email, name, profile).
- **Session table**: Tracks active sessions with `userId`, `token`, and `expiresAt` timestamps.
- **Token shape**: Opaque session token (generated and validated by Better-Auth); cookie-based transport in HTTP requests.

**Authorization:**
Role-based access control (RBAC) or permission-based authorization is not yet configured. When implemented, the pattern will be: attach `roles` or `permissions` fields to the User table, check them in route handlers before passing requests to service logic.

## Request Lifecycle

**Typical authenticated API request (e.g., fetch user posts):**

1. **Browser (web)**: User clicks a link; TanStack Router navigates to `/posts`.
2. **React component** (apps/web): Component mounts and calls `fetch('/api/posts')` with the session cookie attached (automatic).
3. **Hono middleware** (apps/server): Request arrives at POST `/api/posts` handler; middleware extracts session cookie.
4. **Auth validation** (packages/auth): Middleware calls Better-Auth to validate cookie against postgres session table.
5. **Session context**: If valid, request is decorated with `userId` from session.
6. **Database query** (packages/db): Handler constructs a Drizzle query (e.g., `db.select().from(posts).where(eq(posts.userId, userId))`).
7. **PostgreSQL**: Query executes; rows returned.
8. **Response**: Hono serializes result to JSON and sends to browser.
9. **React state**: web receives JSON, updates component state, re-renders.

## Data Architecture

**PostgreSQL** is the single authoritative operational data store, running on port 5433 locally (containerized via Docker Compose).

**Schema Management:**
- Drizzle ORM in `packages/db` defines all schemas in TypeScript (e.g., `src/schema/auth.ts`, `src/schema/posts.ts`).
- No separate migrations folder; Drizzle introspects schema changes and applies them automatically via `bun run db:push`.
- Both `web` and `server` import the same shared Drizzle client (`@q-goal/db`), ensuring a single source of truth for data contracts.

**Local Development:**
- Start Postgres in Docker: `bun run db:start` (host port 5433).
- Apply schema: `bun run db:push`.
- Postgres persists data to a Docker volume; no schema reset between runs unless volume is deleted.

**Python CLIs (etl, genai):**
- May read from or write to PostgreSQL via direct `psycopg` or similar drivers (not yet in scope).
- Can also consume external data sources and load results into Postgres via uv-managed dependencies.

## Deployment Topology

(not determined by analysis)

## Local Development

**Full Stack (Docker Compose):**
```bash
bun install
bun run docker:up      # Builds and starts web, server, postgres
bun run db:push        # Apply migrations (inside Docker)
# Visit http://localhost:3001 (web) and http://localhost:3000/api (server)
```

**Local Hot Reload (without Docker):**
```bash
bun install
bun run db:start       # Start Postgres container only (host port 5433)
bun run db:push        # Apply migrations
bun run dev            # Start web (3001) + server (3000) in dev mode
```

**Python:**
```bash
uv sync                # Sync etl + genai dependencies
uv run etl             # Execute ETL CLI
uv run genai           # Execute GenAI CLI
uv run ruff check --fix  # Lint and auto-fix
```

## Automation & CI

**Primary Interface:** npm scripts in root `package.json` and per-service manifests.

**Key Commands:**
- `bun run dev`: Start web + server in dev mode.
- `bun run docker:up`: Build and run full Docker Compose stack.
- `bun run db:start` / `bun run db:push`: PostgreSQL setup.
- `bun run check-types`: Type-check all TypeScript services.

**CI Hints (Docker Compose):**
Docker Compose configuration includes orchestration for containerized deployments:
- `docker compose build`: Build all service images.
- `docker compose up -d --build`: Start services with fresh builds.
- `docker compose logs -f`: Stream logs from all services.

**Python Automation:**
- `uv run ruff check --fix`: Lint and auto-fix etl + genai.
- `uv run ruff format`: Format Python code.
- `uv add --package <service> <pkg>`: Add dependency to a specific Python package.

## Coupling Hotspots

High-connectivity nodes that may warrant architectural attention:

**Hub nodes** (most inbound + outbound connections):
- `apps/web/src/components/sign-up-form.tsx::SignUpForm` (degree 37): Form component used across multiple pages; changes affect sign-up flow.
- `apps/web/src/components/sign-in-form.tsx::SignInForm` (degree 30): Authentication entry point; tightly coupled to auth state.
- `packages/ui/src/lib/utils.ts::cn` (degree 24): Classname utility (likely Tailwind helper); used everywhere for styling.
- `apps/web/src/components/user-menu.tsx::UserMenu` (degree 18): Session-aware UI component; bridges auth state and UI.
- `apps/web/src/components/mode-toggle.tsx::ModeToggle` (degree 15): Theme switcher; widely referenced.

**Bridge nodes** (highest betweenness centrality; lie on shortest paths between many node pairs):
- `apps/web/src/components/user-menu.tsx::UserMenu` (score 0.00119)
- `packages/ui/src/lib/utils.ts::cn` (score 0.00109)
- `apps/web/src/components/header.tsx::Header` (score 0.000989)
- `apps/web/src/components/mode-toggle.tsx::ModeToggle` (score 0.000757)
- `apps/web/src/components/sign-in-form.tsx::SignInForm` (score 0.000698)

Changes to these components should be tested carefully, as they connect multiple flows; refactoring should preserve backward compatibility with dependent consumers.

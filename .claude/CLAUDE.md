# q-goal

## Tech Stack

- **Runtime:** Bun (pinned — see `packageManager` in `package.json`)
- **Workspace:** npm workspaces (`apps/*`, `packages/*`)
- **Shared:** React 19, Zod

- **web** (TypeScript) — React 19.2.6, TanStack Router 1.168, @ai-sdk/react, @tailwindcss/vite
- **server** (TypeScript) — Hono 4.8.2, @ai-sdk/google, Better-Auth, Drizzle ORM
- **genai** (Python) — FastAPI 0.137, langgraph 1.2+, langchain-core, langchain-openai, deepface
- **etl** (Python) — CLI (uv-managed)
- **auth** (TypeScript) — Better-Auth 1.6.11, Drizzle ORM, Zod
- **db** (TypeScript) — Drizzle ORM 0.45.1, pg 8.17.1, Zod
- **ui** (TypeScript) — React 19.2.6, Base UI 1.0.0, lucide-react, next-themes

## File Placement Guide

### Shared vs Local Rules

Packages in `packages/*` are imported as `@q-goal/<name>` — never use relative cross-package imports. All file placement is service-local unless importing shared types from `@q-goal/<package>`.

### apps/web (React + TanStack Router)

| File Type | Location Pattern | Example |
| --------- | ---------------- | ------- |
| TanStack root route | `src/routes/__root.tsx` | `apps/web/src/routes/__root.tsx` |
| TanStack page route | `src/routes/{name}.tsx` | `apps/web/src/routes/ai.tsx` |
| React component | `src/components/{name}.tsx` | `apps/web/src/components/header.tsx` |
| Auth client lib | `src/lib/auth-client.ts` | `apps/web/src/lib/auth-client.ts` |
| App entry | `src/main.tsx` | `apps/web/src/main.tsx` |

### apps/server (Hono)

| File Type | Location Pattern | Example |
| --------- | ---------------- | ------- |
| Hono server entry | `src/index.ts` | `apps/server/src/index.ts` |

### packages/auth (Better-Auth)

| File Type | Location Pattern | Example |
| --------- | ---------------- | ------- |
| Auth config entry | `src/index.ts` | `packages/auth/src/index.ts` |

### packages/db (Drizzle)

| File Type | Location Pattern | Example |
| --------- | ---------------- | ------- |
| Drizzle schema | `src/schema/{domain}.ts` | `packages/db/src/schema/auth.ts` |
| Package entry | `src/index.ts` | `packages/db/src/index.ts` |

### packages/ui (React components)

| File Type | Location Pattern | Example |
| --------- | ---------------- | ------- |
| UI component | `src/components/{name}.tsx` | `packages/ui/src/components/button.tsx` |
| Utility function | `src/lib/utils.ts` | `packages/ui/src/lib/utils.ts` |

### genai (FastAPI + LangGraph)

| File Type | Location Pattern | Example |
| --------- | ---------------- | ------- |
| FastAPI app entry | `src/genai/api.py` | `genai/src/genai/api.py` |
| Pipeline entry | `src/genai/pipeline.py` | `genai/src/genai/pipeline.py` |
| LangGraph agent module | `src/genai/agent/{module}.py` | `genai/src/genai/agent/graph.py` |
| ETL submodule | `src/genai/etl/{task}.py` | `genai/src/genai/etl/enrich.py` |
| Core config | `src/genai/core/config.py` | `genai/src/genai/core/config.py` |

### etl (Python CLI)

| File Type | Location Pattern | Example |
| --------- | ---------------- | ------- |
| Package entry | `src/etl/__init__.py` | `etl/src/etl/__init__.py` |

## Directory Structure

```
project/
├── apps/
│   ├── web/   React frontend
│   └── server/   Hono backend
├── etl/   Python CLI
├── genai/   FastAPI backend
└── packages/
    ├── auth/   Better-Auth library
    ├── db/   Drizzle library
    └── ui/   React component library
```

## Essential Commands

| Command | Description |
| ------- | ----------- |
| `bun install` | Install dependencies |
| `bun run docker:up` | Build and start (web, server, postgres) |
| `bun run db:start` | Start postgres only (port 5433) |
| `bun run dev` | Start web + server dev |
| `bun run check-types` | Type-check all packages |
| `oxlint && oxfmt --write` | Lint and format (JS/TS) |
| `uv sync` | Sync Python dependencies |
| `uv run etl` | Run ETL CLI |
| `uv run genai-api` | Start FastAPI server (port 8002) |
| `uv run genai-pipeline` | Run WC2026 face-match ETL pipeline |
| `uv run ruff check --fix` | Lint and fix Python |
| `uv run ruff format` | Format Python |

## Services & Ports

| Service | Type | Port | Role |
| ------- | ---- | ---- | ---- |
| web | frontend | 3001 | React frontend |
| server | backend | 3000 | Hono backend |
| genai | backend | 8002 | FastAPI backend |
| auth | library | — | Better-Auth library |
| db | library | — | Drizzle ORM library |
| ui | library | — | React component library |
| etl | cli | — | Python ETL CLI |
| postgres | database | 5433 | PostgreSQL (host port remapped from 5432) |
| google-generative-ai | llm-service | — (SaaS) | Google Cloud generative AI |
| openai | llm-service | — (SaaS) | OpenAI API |

<!-- LLM_WIKI_START -->
## LLM Wiki
- Router (entry point): `docs/llm-wiki/CLAUDE.md` — decision table, tier discipline, available graph tools. **Read this first.**
- Index (summary catalog): `docs/llm-wiki/wiki/index.md` — one line per page; pick the 1–3 pages whose summaries match your question.
- Graph-backed docs: generated from .code-review-graph/graph.db with wiki-generator synthesis.
- Before broad code changes: load the router → match the index → read only the matched pages. Stop wikilink traversal at depth 2. Fall back to graph MCP tools only if the wiki does not answer.
<!-- LLM_WIKI_END -->

<!-- GRAPH_DISCIPLINE_START -->
## Graph navigation discipline

Top-down, never breadth-first. Graph MCP tools have strict per-result token caps; unbounded calls overflow silently. The full discipline (lean defaults, drill-in budgets, forbidden tools, spill-protocol HARD-FAILURE semantics) lives in the wiki router at `docs/llm-wiki/CLAUDE.md` (or `AGENTS.md` on Codex). Read it before issuing graph queries; do NOT improvise tool parameters from prior knowledge.
<!-- GRAPH_DISCIPLINE_END -->

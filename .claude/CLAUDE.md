# q-goal

## Tech Stack

- **Runtime:** Bun (pinned — see `packageManager` in root `package.json`)
- **Workspace:** npm workspaces (`apps/*`, `packages/*`)
- **Shared:** React 19, Zod

- **web** (TypeScript) — React 19, TanStack Router, @ai-sdk/react, @hookform/resolvers, @tailwindcss/vite
- **server** (TypeScript) — Hono 4, @ai-sdk/google, Better-Auth, Drizzle ORM, pg
- **auth** (TypeScript) — Better-Auth 1.6, Drizzle ORM, Zod
- **db** (TypeScript) — Drizzle ORM 0.45, pg
- **ui** (TypeScript) — React 19, @base-ui/react, lucide-react, Tailwind CSS
- **etl** (Python) — uv managed CLI
- **genai** (Python) — uv managed CLI

## File Placement Guide

### Shared vs Local Rules

Packages in `packages/*` are imported as `@q-goal/<name>` — never use relative cross-package imports. All file placement is service-local unless importing shared types from `@q-goal/<package>`.

### apps/web (React + TanStack Router)

| File Type | Location Pattern | Example |
| --------- | ---------------- | ------- |
| TanStack root route | `src/routes/__root.tsx` | `apps/web/src/routes/__root.tsx` |
| TanStack layout route | `src/routes/{group}/route.tsx` | `apps/web/src/routes/_auth/route.tsx` |
| TanStack page route | `src/routes/{name}.tsx` | `apps/web/src/routes/ai.tsx` |
| React component | `src/components/{name}.tsx` | `apps/web/src/components/header.tsx` |

### apps/server (Hono)

| File Type | Location Pattern | Example |
| --------- | ---------------- | ------- |
| Hono server entry | `src/index.ts` | `apps/server/src/index.ts` |

### packages/auth

| File Type | Location Pattern | Example |
| --------- | ---------------- | ------- |
| Auth config | `src/index.ts` | `packages/auth/src/index.ts` |

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

### etl, genai (Python CLIs)

| File Type | Location Pattern | Example |
| --------- | ---------------- | ------- |
| Package entry | `src/{service}/__init__.py` | `etl/src/etl/__init__.py` |

## Directory Structure

```
project/
├── apps/
│   ├── web/                React frontend
│   └── server/             Hono backend
├── etl/                    Python CLI
├── genai/                  Python CLI
└── packages/
    ├── auth/               Better-Auth library
    ├── db/                 Drizzle ORM library
    └── ui/                 React UI library
```

## Services & Ports

| Service | Type | Port | Role |
| ------- | ---- | ---- | ---- |
| web | frontend | 3001 | React frontend |
| server | backend | 3000 | Hono REST API + AI SDK |
| auth | library | — (library — no runtime) | Better-Auth library |
| db | library | — (library — no runtime) | Drizzle ORM library |
| ui | library | — (library — no runtime) | React UI component library |
| etl | cli | — (CLI — no runtime) | Python data pipeline CLI |
| genai | cli | — (CLI — no runtime) | Python AI services CLI |
| postgres | database | 5433 | PostgreSQL database |

## Essential Commands

| Command | Description |
| ------- | ----------- |
| `bun install` | Install dependencies |
| `bun run docker:up` | Build + start web, server, postgres in Docker |
| `bun run db:start` | Start postgres only (host port 5433) |
| `bun run db:push` | Apply Drizzle migrations |
| `bun run dev` | Start web + server dev servers |
| `bun run check-types` | Run type-checker across all services |
| `uv sync` | Sync Python dependencies (etl, genai) |
| `uv run etl` | Run ETL CLI |
| `uv run genai` | Run GenAI CLI |
| `uv run ruff check --fix` | Fix Python lint issues |
| `uv run ruff format` | Format Python code |

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

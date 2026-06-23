---
document_type: index
summary: >-
  Summary catalog for the q-goal LLM wiki — one line per page, frontmatter
  inline.
last_updated: '2026-06-23T03:08:58.598Z'
related:
  - ARCHITECTURE.md
  - SERVICES.md
---
# q-goal LLM Wiki

Summary catalog of every page in this wiki. Each line carries the page summary, document type, tags, and related pages — frontmatter inline so a single read of `index.md` serves Tier 1 retrieval.

## Architecture

- [ARCHITECTURE](ARCHITECTURE.md) — *architecture* — q-goal is a unified npm workspaces monorepo combining TypeScript (Bun-managed) and Python (uv-managed) workspaces in a single repository. The structure separ... **Tags:** architecture, topology, typescript, react, tanstack-router.

## Services catalog

- [SERVICES](SERVICES.md) — *services* — Catalog of services detected in this project with links to service docs. **Tags:** services, catalog. **Related:** [[ARCHITECTURE]].

## Per-service docs

- [auth](services/auth.md) — *service* — The `auth` package provides centralized authentication and session management for q-goal, built on Better-Auth 1.6.11. It abstracts OAuth and email/password ... **Tags:** service, typescript, library, better-auth.
- [db](services/db.md) — *service* — The **db** package is the shared database abstraction layer for the q-goal monorepo. It defines the PostgreSQL schema using Drizzle ORM, exports a connected ... **Tags:** service, typescript, library.
- [etl](services/etl.md) — *service* — The ETL service is a Python CLI that orchestrates the bulk ingestion and processing of images for the World Cup 2026 face-matching pipeline. It invokes the g... **Tags:** service, python, cli.
- [genai](services/genai.md) — *service* — The GenAI service is a dedicated FastAPI backend for compute-intensive generative AI and face-matching workflows. It runs LangGraph agents for quiz generatio... **Tags:** service, python, backend, fastapi.
- [server](services/server.md) — *service* — The server is a lightweight REST API backend built on Hono 4.8.2 that runs on port 3000. It serves as the primary data layer for the [[web]] frontend, handli... **Tags:** service, typescript, backend, hono.
- [ui](services/ui.md) — *service* — The **ui** package is a shared React component library providing reusable, accessible UI components built on Base UI primitives and Tailwind CSS. It is consu... **Tags:** service, typescript, library, react, base-ui.
- [web](services/web.md) — *service* — The web service is a React 19 single-page application (SPA) that provides the primary user interface for q-goal. It serves as the frontend entry point for us... **Tags:** service, typescript, frontend, react, tanstack-router.

## How agents should use this

- Start with this index. Read the 1–3 page bodies whose summaries match your question.
- Follow `**Related:**` `[[wikilinks]]` only when the matched pages reference them.
- Stop wikilink traversal at depth 2.
- If the wiki does not answer your question, fall back to graph MCP tools — never re-read the wiki cover-to-cover.

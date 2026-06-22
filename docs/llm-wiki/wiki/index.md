---
document_type: index
summary: >-
  Summary catalog for the q-goal LLM wiki — one line per page, frontmatter
  inline.
last_updated: '2026-06-18T21:06:25.817Z'
related:
  - ARCHITECTURE.md
  - SERVICES.md
---
# q-goal LLM Wiki

Summary catalog of every page in this wiki. Each line carries the page summary, document type, tags, and related pages — frontmatter inline so a single read of `index.md` serves Tier 1 retrieval.

## Architecture

- [ARCHITECTURE](ARCHITECTURE.md) — *architecture* — **q-goal** is a TypeScript-dominant monorepo structured around two separate workspace systems: **Tags:** architecture, topology, typescript, react, hono.

## Services catalog

- [SERVICES](SERVICES.md) — *services* — Catalog of services detected in this project with links to service docs. **Tags:** services, catalog. **Related:** [[ARCHITECTURE]].

## Per-service docs

- [auth](services/auth.md) — *service* — The auth package provides centralized session-based authentication configured around Better-Auth 1.6. It manages user identity, sessions, and credentials by ... **Tags:** service, typescript, library, better-auth.
- [db](services/db.md) — *service* — Shared database library providing a type-safe PostgreSQL client and schema definitions for the entire monorepo. It is the single source of truth for all data... **Tags:** service, typescript, library.
- [etl](services/etl.md) — *service* — The etl service is a Python CLI for data pipeline operations within the q-goal monorepo. It is designed to read from PostgreSQL tables, perform transformatio... **Tags:** service, python, cli.
- [genai](services/genai.md) — *service* — genai is a Python CLI service for AI-powered data transformations and integrations. It reads from PostgreSQL tables (via the [[db]] package schema) and posts... **Tags:** service, python, cli.
- [server](services/server.md) — *service* — The server is a Hono 4–based REST API backend responsible for handling all business logic, database queries via Drizzle ORM, and integration with external AI... **Tags:** service, typescript, backend, hono.
- [ui](services/ui.md) — *service* — `@q-goal/ui` is a shared React component library that provides the design system and reusable UI components for the web frontend. It exports shadcn/ui-based ... **Tags:** service, typescript, library.
- [web](services/web.md) — *service* — **web** is a client-side React 19 single-page application (SPA) that serves the browser interface. It uses TanStack Router for file-based client-side routing... **Tags:** service, typescript, frontend, react.

## How agents should use this

- Start with this index. Read the 1–3 page bodies whose summaries match your question.
- Follow `**Related:**` `[[wikilinks]]` only when the matched pages reference them.
- Stop wikilink traversal at depth 2.
- If the wiki does not answer your question, fall back to graph MCP tools — never re-read the wiki cover-to-cover.

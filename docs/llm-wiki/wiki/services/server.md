---
document_type: service
summary: >-
  The server is a lightweight REST API backend built on Hono 4.8.2 that runs on
  port 3000. It serves as the primary data layer for the [[web]] frontend,
  handli...
last_updated: '2026-06-23T19:57:02.000Z'
tags:
  - service
  - typescript
  - backend
  - hono
service_id: server
---
# Server

## Purpose

The server is a lightweight REST API backend built on Hono 4.8.2 that runs on port 3000. It serves as the primary data layer for the [[web]] frontend, handling authentication via [[auth]] (Better-Auth), providing AI-powered streaming endpoints, and orchestrating database operations through [[db]] (Drizzle ORM). The server bridges the frontend client, authentication layer, LLM services (Google Generative AI), and PostgreSQL persistence.

## Public API / Surface

- `POST /api/auth/*` — Better-Auth passthrough routes for signup, signin, signout, OAuth callback, and session management
- `POST /ai` — Streaming text endpoint that accepts a message and returns LLM-generated responses as a UIMessageStreamResponse
- `GET/POST/DELETE /api/quiz-result` — per-user quiz-result persistence. All three require a valid Better-Auth session (`auth.api.getSession`) and return `401` with no DB read/write otherwise. `POST` Zod-validates the body and upserts on `userId`; reads/deletes are scoped to the caller. Backed by the `quiz_result` table in [[db]]. `DELETE` is included in the CORS `allowMethods`.
- Additional routes and endpoints (not enumerated in codebase analysis)

## Internal Architecture

The server follows a middleware-first pattern with Hono. Global middleware includes `logger()` for request logging and `cors()` configured with the `CORS_ORIGIN` environment variable to allow cross-origin requests from the frontend. The server has two primary routing paths:

1. **Authentication layer**: `app.on(["POST", "GET"], "/api/auth/*")` delegates all auth requests to the Better-Auth handler, which manages session tokens, email/password validation, and OAuth provider coordination.
2. **Application routes**: Hono route handlers for `/ai` and other endpoints that interact with the database via the shared [[db]] package and call LLM models via the Google AI SDK.

No explicit dependency injection container or command bus; handlers receive the Hono context object (`c`) and access environment variables and shared libraries directly.

## Request Lifecycle

1. HTTP request arrives at Hono app (port 3000)
2. Logger middleware logs the request metadata
3. CORS middleware validates origin and applies cross-origin headers
4. Router matches request path to handler (e.g., `/api/auth/*` vs `/ai`)
5. If auth route: Better-Auth handler processes credentials, validates session, or initiates OAuth flow; tokens stored/retrieved from PostgreSQL via [[db]]
6. If application route (e.g., `/ai`): handler calls `streamText()` with the Google Gemini model, passing user messages and system context
7. LLM response streamed to client via `toUIMessageStreamResponse()` (HTTP streaming)

## Data Layer

- **PostgreSQL** (port 5433 on host, 5432 inside container) — primary data store managed by [[db]] via Drizzle ORM
- **Tables owned by server** (via Better-Auth schema): `user`, `session`, `account` for authentication state
- **Database connectivity**: All queries routed through the shared `@q-goal/db` client, which centralizes schema definitions and migration management

## Configuration

The server reads the following environment variables:

- `PORT` — HTTP listen port (default: 3000)
- `CORS_ORIGIN` — allowed origin for CORS middleware (e.g., `http://localhost:3001`)
- `DATABASE_URL` — PostgreSQL connection string (inherited from [[db]] package context)
- `GOOGLE_GENERATIVE_AI_API_KEY` — API key for Google Cloud generative AI
- `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` — OAuth 2.0 credentials for Google Sign-In
- `BETTER_AUTH_SECRET` — session token signing secret
- `BETTER_AUTH_URL` — base URL for auth callback routes (e.g., `http://localhost:3000`)

## Integrations

- **[[web]]** — React frontend consumes the `/ai` streaming endpoint and all `/api/auth/*` routes for authentication
- **[[db]]** — Drizzle ORM client for all database operations; server queries user/session/account tables
- **[[auth]]** — Better-Auth library provides session validation, user schema, and OAuth provider configuration
- **PostgreSQL** — primary persistence layer for user accounts, sessions, and application data
- **Google Generative AI** (`@ai-sdk/google`) — called via `streamText()` to generate LLM responses for the chat interface

## Service-Specific Patterns

**Hono middleware-first routing**: Global middleware (logger, CORS) applied via `app.use()` before route-specific handlers. Route-specific logic lives in handler functions that receive context (`c`) and extract request/response utilities from it (e.g., `c.req.json()`, `c.text()`).

**Streaming responses**: The `/ai` endpoint does not return a full response in one call; instead, it streams the LLM output token-by-token using the AI SDK's `streamText()` builder and Hono's `toUIMessageStreamResponse()` adapter, reducing latency for UI updates.

**Better-Auth passthrough**: Authentication routes delegate entirely to the Better-Auth handler rather than implementing custom session logic. This pattern simplifies credential handling and OAuth flows at the cost of tight coupling to the Better-Auth library interface.

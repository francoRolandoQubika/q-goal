---
document_type: service
summary: >-
  The server is a Hono 4–based REST API backend responsible for handling all
  business logic, database queries via Drizzle ORM, and integration with
  external AI...
last_updated: '2026-06-18T21:06:25.817Z'
tags:
  - service
  - typescript
  - backend
  - hono
service_id: server
---
# server

## Purpose

The server is a Hono 4–based REST API backend responsible for handling all business logic, database queries via Drizzle ORM, and integration with external AI services. It serves as the central hub for the web frontend (port 3001), processing authentication via Better-Auth, streaming AI completions from Google Gemini, and providing POST endpoints for the etl and genai Python CLIs to upsert results. All persistent state flows through PostgreSQL.

## Public API / Surface

The server exposes two primary endpoint groups:

- **POST /ai** — Receives a JSON body with UI messages, streams back AI responses from Google Gemini. Uses `@ai-sdk/react` on the frontend and `@ai-sdk/google` on the backend for language model integration.
- **/api/auth/\*** — Better-Auth handler endpoints (sign-in, sign-up, session refresh, logout). Routes all auth requests to the [[auth]] package's managed session workflow.

Additionally, the server may expose POST endpoints for webhooks or direct integrations from the etl and genai Python CLIs to upsert processed data (not yet determined by analysis).

## Internal Architecture

The server uses a lightweight, middleware-first architecture:

1. **Middleware layer:** CORS (configurable trustedOrigins), request logger, Better-Auth session validation attached to context (`c.get("user")` and `c.get("session")`)
2. **Route handlers:** Direct pattern — each route parses JSON body, validates with Zod if needed, calls service logic or database queries, returns JSON
3. **AI integration:** Language model wrapping with devtools middleware; streaming responses via `streamText().toUIMessageStreamResponse()`
4. **Database layer:** All queries go through the shared [[db]] client (Drizzle ORM singleton), which executes parameterized SQL against PostgreSQL

No separate service or repository layer exists yet; business logic is inline in route handlers. As the service grows, route handlers can be extracted into service modules.

## Request Lifecycle

**Authentication flow (POST /api/auth/sign-in):**
1. Hono receives request
2. CORS middleware evaluates origin
3. Request routed to Better-Auth handler
4. Better-Auth queries PostgreSQL for user via Drizzle adapter
5. Session created and stored in database
6. HTTP-only, secure cookie set in response (via `defaultCookieAttributes`)
7. Response returned to browser

**AI endpoint flow (POST /ai):**
1. Hono receives request with JSON body containing UI messages
2. CORS middleware validates origin
3. Route handler parses messages from request body
4. Messages converted to model format
5. Google Gemini called via wrapped language model with devtools middleware
6. Response streamed back to client in chunks

## Data Layer

Session and user data are owned by the [[auth]] package and persisted via Better-Auth's Drizzle adapter:

- `users` — Authenticated user accounts
- `sessions` — Active session records with expiry
- `accounts` — OAuth account linking (prepared for future extensions)
- `verification_tokens` — Email verification and password reset tokens

All tables are defined in the [[db]] schema and queried through the shared Drizzle client. The server has no application-specific tables yet.

## Configuration

The server reads the following environment variables:

| Variable | Purpose |
| --- | --- |
| `DATABASE_URL` | PostgreSQL connection string (used by Drizzle) |
| `CORS_ORIGIN` | Trusted origin for cross-origin requests (e.g., http://localhost:3001) |
| `BETTER_AUTH_SECRET` | Secret for signing session tokens |
| `BETTER_AUTH_URL` | Base URL for auth endpoints (e.g., http://localhost:3000) |
| `GOOGLE_GENERATIVE_AI_API_KEY` | API key for Google Gemini model access |

All variables are loaded at startup and must be set before the server runs (see `apps/server/.env.example`).

## Integrations

**External services:**
- **Google Generative AI** — `@ai-sdk/google` calls Gemini API for text generation and streaming

**Inbound integrations:**
- [[web]] (port 3001) — Calls /ai for streaming AI completions and /api/auth/* for authentication
- **etl, genai Python CLIs** — POST processed results to server endpoints (pattern not yet determined by analysis)

**Outbound integrations:**
- [[db]] — Drizzle ORM queries against PostgreSQL (port 5433)
- [[auth]] — Better-Auth library for session management and password hashing

## Service-Specific Patterns

- **Direct route handler pattern:** No separate controller or service layer; business logic lives inline in Hono route handlers. As complexity grows, handlers can be factored into reusable service functions.
- **Factory + singleton pattern:** `createAuth()` and `createDb()` initialize shared libraries at module load time; instances are exported as singletons (`export const auth = createAuth()`) and imported throughout the codebase.
- **AI SDK wrapper pattern:** Language model wrapped with devtools middleware before calling `streamText()`; enables request/response inspection during development without changing application code.
- **Middleware-based configuration:** CORS and logging configured once at the app level via `app.use()`, applied to all routes; auth validation is middleware-based rather than per-route guards.

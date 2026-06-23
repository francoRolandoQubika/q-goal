---
document_type: service
summary: >-
  The `auth` package provides centralized authentication and session management
  for q-goal, built on Better-Auth 1.6.11. It abstracts OAuth and email/password
  ...
last_updated: '2026-06-23T03:08:58.598Z'
tags:
  - service
  - typescript
  - library
  - better-auth
service_id: auth
---
# Authentication Library

The `auth` package provides centralized authentication and session management for q-goal, built on Better-Auth 1.6.11. It abstracts OAuth and email/password authentication, manages session tokens, and owns the user and account schemas in PostgreSQL. Both [[server]] and [[web]] consume this library to handle sign-up, sign-in, and session validation.

## Public API / Surface

The package exports a single factory function `createAuth()` that returns a configured Better-Auth instance:

```typescript
export function createAuth() { /* ... */ }
```

The instance provides:
- **Email/password authentication** — registration and credential validation
- **Google OAuth 2.0** — social login via Google Sign-In
- **Session management** — HTTP-only cookie-based sessions stored in PostgreSQL
- **HTTP handler** — `auth.handler(request)` routes `/api/auth/*` requests

The [[web]] app imports `createAuthClient` from better-auth/react to instantiate a client-side auth context; [[server]] uses the handler for middleware.

## Internal Architecture

The library follows an adapter pattern: Better-Auth exposes configuration functions, and `createAuth()` wires a Drizzle ORM adapter to PostgreSQL. No business logic lives in auth — all persistence is delegated to [[db]]. The package manages:

1. Provider configuration (email/password toggle, Google OAuth credentials)
2. Session storage adapter (Drizzle + PostgreSQL schema binding)
3. Trust and security settings (CORS_ORIGIN, secret key, base URL)

Configuration is environment-driven; runtime behavior is determined by `env.*` reads.

## Request Lifecycle

When [[server]] receives a request to `/api/auth/*`:

1. Hono middleware routes to `auth.handler(c.req.raw)`
2. Better-Auth parses the request (sign-up form, sign-in form, or token refresh)
3. Auth validates input, checks databases via [[db]], and returns a session token or error
4. Token is set as an HTTP-only cookie on the response

When [[web]] calls `authClient.signIn()` or `authClient.signUp()`:

1. Client sends credentials or OAuth code to server `/api/auth/*`
2. Server responds with session cookie (automatic via handler)
3. Client-side auth state updates, triggering route protection logic

## Data Layer

Auth owns three tables in PostgreSQL (managed via [[db]] schema):

- `user` — user identity (id, email, name, createdAt, updatedAt)
- `session` — active sessions with expiry (id, userId, expiresAt, token)
- `account` — OAuth provider links (id, userId, provider, providerAccountId)

All access is parameterized through the Drizzle adapter; no raw SQL.

## Configuration

Auth reads these environment variables:

| Variable | Purpose |
| --- | --- |
| `BETTER_AUTH_SECRET` | Session encryption key (32+ bytes, base64) |
| `BETTER_AUTH_URL` | Canonical auth base URL (e.g., `http://localhost:3000`) |
| `CORS_ORIGIN` | Allowed cross-origin domain (e.g., `http://localhost:3001`) |
| `GOOGLE_CLIENT_ID` | Google OAuth 2.0 client ID |
| `GOOGLE_CLIENT_SECRET` | Google OAuth 2.0 client secret |

All variables are required; missing env vars will cause startup failure.

## Integrations

- **[[db]]** — Drizzle adapter provides PostgreSQL connectivity and schema management
- **[[server]]** — Server imports `auth` and mounts `auth.handler()` on `/api/auth/*` routes
- **[[web]]** — Web app imports `createAuthClient` to manage client-side session state
- **Google Cloud OAuth** — External OAuth provider for social login (Google Sign-In)

## Service-Specific Patterns

**Adapter pattern:** Better-Auth ships with database adapters; the drizzleAdapter bridges Better-Auth's expectations to [[db]]'s schema and client. This isolates database details from auth logic.

**Configuration over code:** All authentication behavior is parameterized via env variables and the `betterAuth(...)` config object. No conditional branching for feature flags; the config object defines what is enabled.

**Library, not service:** Auth has no runtime footprint—it exports functions and configuration. The actual HTTP handling happens in [[server]]; auth itself is stateless library code.

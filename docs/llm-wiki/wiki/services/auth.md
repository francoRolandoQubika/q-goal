---
document_type: service
summary: >-
  The auth package provides centralized session-based authentication configured
  around Better-Auth 1.6. It manages user identity, sessions, and credentials by
  ...
last_updated: '2026-06-21T21:00:00.000Z'
tags:
  - service
  - typescript
  - library
  - better-auth
service_id: auth
---
# @q-goal/auth

## Purpose

The auth package provides centralized session-based authentication configured around Better-Auth 1.6. It manages user identity, sessions, and credentials by defining the database schema (via Drizzle ORM adapter to PostgreSQL) and exposing authentication handlers for sign-in, sign-up, and session management. Both the server and web applications import this package to maintain a single source of truth for authentication logic.

## Public API / Surface

The service exports a single configuration entry point: `packages/auth/src/index.ts`, which provides:

- `auth` — singleton instance of Better-Auth, configured with a Drizzle PostgreSQL adapter
- `createAuth()` — factory function to instantiate a new Better-Auth instance with environment configuration

The server imports `auth` and attaches it to the Hono app via `auth.handler`, exposing HTTP endpoints at `/api/auth/*` for sign-in, sign-up, session refresh, and logout. The web app accesses these endpoints indirectly through the `@ai-sdk/react` client library.

## Internal Architecture

The auth package follows a **factory + singleton pattern**: `createAuth()` initializes a Better-Auth instance with environment variables (`BETTER_AUTH_SECRET`, `BETTER_AUTH_URL`, `CORS_ORIGIN`), configures a Drizzle ORM adapter for PostgreSQL, and returns the configured instance. This instance is exported as a module-level singleton (`auth`), imported by [[server]] to attach to the Hono router and by [[web]] via the `@ai-sdk/react` client library. The Drizzle adapter handles all database operations (user lookups, session CRUD, account linking) without requiring manual schema migrations.

## Request Lifecycle

**Email/password flow:**

1. User submits email and password via sign-in form (client-side validation with Zod)
2. Web app calls `authClient.signIn.email()`, sending POST to `/api/auth/sign-in`
3. Server routes request to `auth.handler` (Better-Auth middleware)
4. Better-Auth queries PostgreSQL via Drizzle adapter: looks up user by email
5. Compares submitted password against stored hash; returns error if invalid
6. On success, inserts new session record into the database with expiry timestamp
7. Sets HTTP-only, secure, SameSite=none session cookie in response headers
8. Browser receives cookie; web app navigates to `/dashboard` on success or displays error toast

**Google OAuth flow:**

1. User clicks "Sign in with Google"; web app calls `authClient.signIn.social({ provider: "google", callbackURL: "/dashboard" })`
2. Better-Auth redirects the browser to Google's OAuth consent page
3. After consent, Google redirects to `/api/auth/callback/google` (auto-registered by Better-Auth under the existing `/api/auth/*` Hono handler — no custom route needed)
4. Better-Auth exchanges the authorization code for tokens, creates or looks up the user record, and links the Google identity to the `account` table row
5. If a user with the same email already exists (email/password account), Better-Auth links the Google account to the existing user (no duplicate user created)
6. Session cookie is set; browser is redirected to `callbackURL` (`/dashboard`)

## Data Layer

The auth package owns the following PostgreSQL tables (created and managed by the Drizzle adapter):

- `user` — user identity (id, email, name, emailVerified, passwordHash)
- `session` — active sessions (id, userId, expiresAt, ipAddress, userAgent)
- `account` — linked OAuth accounts (for future multi-provider authentication)
- `verification` — email verification tokens (for sign-up confirmation flows)

Schema is not manually written; the Drizzle adapter generates and applies it automatically.

## Configuration

| Variable | Purpose |
| --- | --- |
| `BETTER_AUTH_SECRET` | Cryptographic secret for signing tokens and session data |
| `BETTER_AUTH_URL` | Base URL of the auth service (e.g., `http://localhost:3000`) |
| `CORS_ORIGIN` | Trusted origin for cross-origin cookie sharing (e.g., `http://localhost:3001`) |
| `DATABASE_URL` | PostgreSQL connection string (inherited from [[db]]) |
| `GOOGLE_CLIENT_ID` | OAuth 2.0 Client ID from Google Cloud Console (required for Google sign-in) |
| `GOOGLE_CLIENT_SECRET` | OAuth 2.0 Client Secret from Google Cloud Console (required for Google sign-in) |

Register `${BETTER_AUTH_URL}/api/auth/callback/google` as an authorized redirect URI in Google Cloud Console. Both variables are validated at startup via `@t3-oss/env-core`; a missing or empty value causes an immediate server startup failure.

## Integrations

**Consumed by:**
- [[server]] — imports `auth` singleton, attaches to Hono app, handles `/api/auth/*` routes
- [[web]] — uses `@ai-sdk/react` `createAuthClient()` to call auth endpoints; manages client-side session state

**Depends on:**
- [[db]] — imports and uses the Drizzle ORM client to persist users, sessions, and accounts to PostgreSQL
- `better-auth` (npm package v1.6.x) — provides session management, account linking, and email/password authentication strategies

## Service-Specific Patterns

- **Factory + singleton:** `createAuth()` builds a configured instance; module exports a pre-instantiated `auth` singleton to avoid repeated initialization and allow module-level reuse.
- **`socialProviders` is a top-level key:** Google OAuth (and any future social providers) is configured as `socialProviders: { google: { clientId, clientSecret } }` at the top level of `betterAuth({})`, NOT inside `plugins: []`. Better-Auth automatically registers the callback routes under `/api/auth/callback/<provider>`.
- **Drizzle adapter:** All database operations (user lookups, session creation, token validation) are delegated to the adapter, which translates them into parameterized SQL without exposing raw queries.
- **Environment-driven setup:** Secrets, URLs, and origins are loaded at module initialization; configuration is immutable after instantiation.
- **HTTP-only cookies with CORS:** Sessions are stored server-side in the database; cookies are secure, HTTP-only, and SameSite=none to support cross-origin requests between web (port 3001) and server (port 3000). No manual JWT handling required. This cross-origin cookie config is **required for OAuth** — without `sameSite: "none"` + `secure: true`, the session cookie is silently dropped after the OAuth redirect.
- **Account linking:** When a Google user's email matches an existing email/password account, Better-Auth links the OAuth identity to the existing `account` table row — no duplicate user is created.
- **Stale session behavior:** Modifying a user's role or permissions in the database does not take effect until the user logs out and back in; the active session caches the old user state until explicitly invalidated.

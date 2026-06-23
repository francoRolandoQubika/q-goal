---
document_type: service
summary: >-
  The web service is a React 19 single-page application (SPA) that provides the
  primary user interface for q-goal. It serves as the frontend entry point for
  us...
last_updated: '2026-06-23T05:00:00.000Z'
tags:
  - service
  - typescript
  - frontend
  - react
  - tanstack-router
service_id: web
---
# Web

The web service is a React 19 single-page application (SPA) that provides the primary user interface for q-goal. It serves as the frontend entry point for user authentication (Google OAuth only), navigation across feature pages, and interaction with backend services. The app runs on port 3001 and communicates with the server (port 3000) for API requests and the genai service (port 8002) directly for quiz and face-matching workflows.

## Public API / Surface

The web service has no HTTP endpoints of its own; it is a browser-based SPA delivered via static assets. Its surface consists of **client-side routes** defined in the TanStack Router file structure:

| Route | Purpose |
| ----- | ------- |
| `/` | Root/home page with navigation |
| `/login` | Google OAuth sign-in (redirects to `/quiz` on success) |
| `/ai` | Real-time AI chat interface with streaming responses |
| `/_auth/quiz` | Auth-protected quiz chat interface (calls genai `/quiz/start` + `/quiz/answer`) |
| `/_auth/dashboard` | Auth-protected results dashboard (displays quiz assignments) |
| Other routes | (determined by route files in `src/routes/`) |

Client-side navigation is handled entirely by TanStack Router; no server-side routing is required. The app exports no programmatic library surface—it is consumed as a built application artifact delivered to browsers.

## Internal Architecture

The web app follows a React component tree layered as:

1. **Root route** (`src/routes/__root.tsx`) — wraps all pages with global context providers (theme, auth, router)
2. **Layout routes** (`src/routes/{group}/route.tsx`) — optional nested layouts for page groups (e.g., `_auth/` for signin/signup)
3. **Page routes** (`src/routes/{name}.tsx`) — leaf routes that render page-level components
4. **Components** (`src/components/{name}.tsx`) — reusable React components, imported from `packages/ui` (Base UI + Tailwind) and local components
5. **Libraries** (`src/lib/`) — auth-client and utility functions

**Middleware & Providers:**
- TanStack Router: handles file-based routing and code-splitting
- Better-Auth client: manages session state and OAuth flows
- Theme provider: controls light/dark mode via `next-themes`
- Tailwind CSS (v4): styling via utility classes

No dependency injection container or service locator; composition relies on React context and direct imports.

## Request Lifecycle

Typical user interaction flow:

1. Browser loads `/` → **Route dispatch** (TanStack Router matches URL → `__root.tsx` renders)
2. **Context initialization** → Root component instantiates theme, auth client, and child routes
3. **Auth check** (on mount) → `src/lib/auth-client.ts` calls `/api/auth/getSession` to load user session
4. **Route component render** → TanStack Router renders matched page component with components and UI imports
5. **User interacts** (e.g., fills form, clicks button) → event handler submits to server or genai
6. **API call** → Fetch request to server (`VITE_SERVER_URL` + route) or genai service with method/body/headers
7. **Stream response** (for AI routes) → `@ai-sdk/react` DefaultChatTransport pipes server-sent events to UI state
8. **Re-render** → Component state updates → UI reflects new data

**Example: Sign-in**  
User visits `/login` → clicks "Sign in with Google" → `authClient.signIn.social({ provider: "google" })` redirects to Google OAuth → callback returns session cookie via Better-Auth handler on server → client auth state updates → redirect to `/quiz`.

**Example: AI chat**  
User types message on `/ai` → `useChat` hook sends POST to `/ai` with streaming request → server runs `streamText()` with Google Gemini → streams back to client via ReadableStream → UI appends tokens to chat.

## Data Layer

The web service does not own any persistent data. It reads from:

- **Server** (`/api/*`) — user sessions, authentication state, chat history (if persisted)
- **genai** (`/match`, `/quiz`) — match results, quiz questions
- **Browser localStorage** — client-side session tokens, user preferences (if any)

All durable state is owned by the server and PostgreSQL database; web is stateless.

## Configuration

| Environment Variable | Purpose | Source |
| -------------------- | ------- | ------ |
| `VITE_SERVER_URL` | Base URL for server API calls (e.g., `http://localhost:3000`) | `apps/web/.env` |
| `VITE_GENAI_URL` | Base URL for genai service direct calls (`/quiz/start`, `/quiz/answer`, `/faces/:id`) | `apps/web/.env` |

The prefix `VITE_` indicates these are Vite build-time variables and are embedded into the built assets. No environment variables are read at runtime.

## Integrations

| Service | Protocol | Purpose |
| ------- | -------- | ------- |
| [[server]] | REST (fetch) | API calls for auth, chat, user data |
| [[genai]] | REST (fetch) | Face matching (`/match`) and quiz endpoints (`/quiz`) |
| Google Generative AI | Indirect via [[server]] | LLM inference; server owns API key |
| Google OAuth | Indirect via [[server]] | User authentication; server owns credentials |

The web app does not directly call external services; all external integrations are mediated by the server to keep credentials secure.

## Service-Specific Patterns

**File-based routing:** TanStack Router derives routes from file structure in `src/routes/`. Misspelled filenames are silently ignored; use exact conventions (`__root.tsx`, `{name}.tsx`, `{group}/route.tsx`).

**React hooks for state:** Components use `useState`, `useEffect`, and `useChat` from `@ai-sdk/react` to manage local and streaming state. No global state container (Redux, Zustand) observed.

**Transport abstraction:** `DefaultChatTransport` wraps HTTP streaming into a standard `useChat` interface, decoupling chat logic from transport details.

**Shared UI library:** Components import from `packages/ui` (Base UI + Tailwind CVA variants) to ensure visual consistency and reduce duplication across apps.

**Environment isolation:** Each `.env` file is app-scoped; web does not share configuration with server or other packages via environment files.

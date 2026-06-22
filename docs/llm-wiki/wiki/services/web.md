---
document_type: service
summary: >-
  **web** is a client-side React 19 single-page application (SPA) that serves
  the browser interface. It uses TanStack Router for file-based client-side
  routing...
last_updated: "2026-06-22T00:00:00.000Z"
tags:
  - service
  - typescript
  - frontend
  - react
service_id: web
---

# web

## Purpose

**web** is a client-side React 19 single-page application (SPA) that serves the browser interface. It uses TanStack Router for file-based client-side routing, renders pages on demand, and delegates all data operations and business logic to the [[server]]. Form state is managed locally with React Hook Form and Zod validation; authentication is delegated to [[auth]] via the Better-Auth client.

## Public API / Surface

The web service is not a backend API but a browser SPA. Its public surface consists of the routes it serves:

- **`/`** — root layout and navigation shell (`src/routes/__root.tsx`)
- **`/ai`** — AI chat interface with streaming message exchange (`src/routes/ai.tsx`)
- **`/_auth/*`** — authentication layout group for sign-in, sign-up, and password reset pages (`src/routes/_auth/route.tsx`)
- **`/quiz`** — authenticated quiz interface: role collection, 4-question GenAI-driven progression, and player assignment results (`src/routes/_auth/quiz.tsx`)
- **`/dashboard`** — authenticated user dashboard (still accessible via direct navigation)

All routes render via TanStack Router's file-based convention. Pages export a `Route` object configured with `createFileRoute()` and a React component.

## Internal Architecture

Web follows a component-driven architecture with clear separation of concerns:

- **Route layer** (`src/routes/`) — TanStack Router file-based pages; each exports a `Route` object and a component
- **Component layer** (`src/components/`) — Reusable React components (forms, header, user menu, mode toggle) composed into pages
- **Client layer** — Better-Auth client for session management; @ai-sdk/react's `useChat` hook for streaming AI conversations; TanStack react-form for form state and validation
- **HTTP communication** — Fetch-based (no client SDK; direct calls to `env.VITE_SERVER_URL`)
- **UI primitives** — Imported from [[ui]] (@q-goal/ui) including shadcn/ui components, lucide icons, and Tailwind utility functions

Key libraries: React 19, TanStack Router v1, @hookform/react, @ai-sdk/react, @q-goal/ui, Zod.

## Request Lifecycle

**Typical page navigation:**

1. User navigates to a route (e.g., `/ai`)
2. TanStack Router matches the route file and renders the component
3. Component mounts and calls the server API via `fetch()` if needed
4. Server returns JSON; component updates local state via hooks
5. React re-renders the page

**AI chat example:**

1. User types a message in the chat input
2. `useChat` hook from @ai-sdk/react sends `POST /ai` with message history
3. Server streams response chunks back (Server-Sent Events or streaming JSON)
4. `useChat` hook updates the `messages` array on each chunk
5. Chat component re-renders, displaying the new assistant message

**Authentication example (email/password):**

1. User submits sign-in form (email + password)
2. Form validator runs Zod schema check (email format, password ≥8 chars)
3. On validation pass, `authClient.signIn.email()` sends credentials to server
4. Server validates and issues a session cookie (HTTP-only, secure, SameSite=none)
5. Browser stores cookie; subsequent requests include it automatically
6. On success, TanStack Router navigates to `/quiz`; on error, toast displays

**Authentication example (Google OAuth):**

1. User clicks "Sign in with Google" button on `/login`
2. `authClient.signIn.social({ provider: "google", callbackURL: "${window.location.origin}/quiz" })` triggers a full browser redirect to Google's consent page
3. After consent, Google redirects to the server's `/api/auth/callback/google` (handled by Better-Auth)
4. Server completes the OAuth exchange and sets the session cookie
5. Browser is redirected to `/quiz`; on cancel or error, Better-Auth redirects back to `/login` with an error query param and a toast is displayed

## Data Layer

Web owns no persistent data stores; it is stateless from the server's perspective. Local state includes:

- **Form state** — managed by @hookform/react with Zod validation (sign-in, sign-up, etc.)
- **Chat messages** — managed by `useChat` hook (transient; lost on page reload)
- **Session state** — managed by Better-Auth client; cookie persists across reloads
- **UI state** — dark mode toggle, menu open/close, etc. (local React state or localStorage)

All application data (users, tasks, history) originates from the [[server]] API.

## Configuration

Web reads the following environment variables (via `VITE_*` prefix for Vite):

| Variable          | Purpose                                                       |
| ----------------- | ------------------------------------------------------------- |
| `VITE_SERVER_URL` | Base URL for server API calls (e.g., `http://localhost:3000`) |
| `VITE_GENAI_URL`  | Base URL for GenAI API direct calls (e.g., `http://localhost:8002`) |

Additional environment setup is documented in the root README under "Getting Started" (copy `.env.example` to `.env`).

## Integrations

- **[[server]]** — all data fetches and business logic; web calls `${VITE_SERVER_URL}/api/*` endpoints via fetch
- **[[auth]]** — Better-Auth client library; handles sign-in, sign-up, session refresh, and user state
- **[[ui]]** — reusable React components, icons, and Tailwind utilities imported from `@q-goal/ui`
- **[[genai]]** — direct browser fetch to `${VITE_GENAI_URL}/quiz/start`, `/quiz/answer`, and `/faces/{id}` (no Hono proxy); CORS is open on the GenAI server
- **Google Generative AI** — indirect; web calls server `/ai` endpoint, which streams Gemini responses back to the client

## Service-Specific Patterns

**TanStack Router file-based routing** — Each route file exports a `Route` object via `createFileRoute("/path")`. Layout groups (prefixed with `_`) wrap sibling routes. Route params are accessed via `useParams()`.

**React Hook Form + Zod validation** — Forms use `useForm()` with `onSubmit` validators that run Zod schemas client-side before submission. Error messages are displayed inline and in toast notifications.

**useChat hook for streaming** — @ai-sdk/react's `useChat` hook abstracts message state and streaming from the server, exposing `messages`, `sendMessage`, and `status` props. The hook handles chunked responses automatically.

**Better-Auth client for auth state** — `createAuthClient()` factory returns a client with hooks (`useSession()`) and methods (`signIn.email()`, `signUp.email()`, `signIn.social()`, etc.). Session state is automatically persisted via HTTP-only cookies; logout clears both client state and the server session. Google OAuth is triggered via `signIn.social({ provider: "google", callbackURL: "${window.location.origin}/quiz" })` — `callbackURL` must be an absolute URL to survive the Google redirect.

**Direct GenAI calls** — The `/quiz` route calls the [[genai]] service directly from the browser via `VITE_GENAI_URL` (no Hono proxy). CORS is open (`*`) on the GenAI server. Session state for the quiz is held in local React state (in-memory; lost on reload).

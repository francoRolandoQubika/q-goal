# web

React 19 single-page application. Provides the browser interface for authentication, the AI chat, and the user dashboard.

- **Port:** 3001 (dev server) / 80 inside Docker (served by nginx)
- **Runtime:** Vite (dev) · nginx (Docker)

## Routes

| Path | Access | Description |
|------|--------|-------------|
| `/` | Public | Landing page |
| `/login` | Public | Email/password sign-in and sign-up |
| `/dashboard` | Protected | Authenticated user dashboard |
| `/ai` | Public | AI chat powered by the server's `/ai` endpoint |

Protected routes are wrapped by the `_auth` layout route, which redirects unauthenticated users to `/login`.

## Development

```bash
# from the repo root
bun run dev:web           # Vite dev server with HMR
bun run check-types       # TypeScript check
```

Or from this directory:

```bash
bun run dev
bun run check-types
```

## Build

```bash
bun run build             # outputs static files to dist/
bun run serve             # preview the production build locally
```

The Docker image builds the static files and copies them into an nginx container.

## Environment Variables

`VITE_*` variables are embedded into the JavaScript bundle at **build time** — they are not read at runtime. This means their value depends on when and how the build runs, not on what the server has at startup.

Create `apps/web/.env` by copying the example:

```bash
cp apps/web/.env.example apps/web/.env
```

| Variable | Docker Compose | Local Dev | Description |
|----------|---------------|-----------|-------------|
| `VITE_SERVER_URL` | Set via build arg in `docker-compose.yml` — `.env` is ignored | Set in `apps/web/.env` | URL of the API server the browser calls |

### Docker Compose vs local dev

When running via `bun run docker:up`, `docker-compose.yml` passes `VITE_SERVER_URL` as a Docker build argument:

```yaml
# docker-compose.yml (excerpt)
build:
  args:
    VITE_SERVER_URL: http://localhost:3000
```

The value is baked into the nginx-served bundle at image-build time. The `apps/web/.env` file is mounted at runtime (`env_file: required: false`), but since all web variables are compile-time, it has no effect inside the container.

For local dev (`bun run dev:web`), Vite reads `apps/web/.env` at startup:

```bash
# apps/web/.env for local dev:
VITE_SERVER_URL=http://localhost:3000
```

## Dependencies

| Package | Role |
|---------|------|
| `@tanstack/react-router` | File-based, type-safe client-side routing |
| `@ai-sdk/react` | `useChat` hook for streaming AI responses |
| `better-auth` | `createAuthClient` for session management |
| `@q-goal/ui` | Shared shadcn/ui component library |
| `@q-goal/env` | Validated env var access via `@t3-oss/env-core` |
| `tailwindcss` | Utility-first CSS (v4) |
| `sonner` | Toast notifications |
| `lucide-react` | Icon set |
| `vite-plugin-pwa` | Progressive Web App support |

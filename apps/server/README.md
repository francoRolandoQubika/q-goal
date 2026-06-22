# server

Hono 4 REST API backend. Handles authentication (Better-Auth), AI streaming (Google Gemini via AI SDK), and serves as the central hub for the web frontend.

- **Port:** 3000
- **Runtime:** Bun

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/` | Health check — returns `OK` |
| `POST/GET` | `/api/auth/*` | Better-Auth handler (sign-in, sign-up, session, logout) |
| `POST` | `/ai` | Streams a Gemini 2.5 Flash response from a UI message array |

## Development

```bash
# from the repo root
bun run dev:server        # hot-reload (bun --hot)
bun run check-types       # TypeScript check
```

Or from this directory:

```bash
bun run dev
bun run check-types
```

## Build

```bash
bun run build             # outputs dist/index.mjs
bun run start             # runs dist/index.mjs
```

The Docker image runs `bun dist/index.mjs` directly.

## Environment Variables

Create `apps/server/.env` by copying the example:

```bash
cp apps/server/.env.example apps/server/.env
```

| Variable | Required | Docker Compose | Description |
|----------|----------|---------------|-------------|
| `BETTER_AUTH_SECRET` | Yes | from `.env` | Signing secret — min 32 chars. Generate with `openssl rand -base64 32` |
| `BETTER_AUTH_URL` | Yes | from `.env` | Base URL of this server, e.g. `http://localhost:3000` |
| `CORS_ORIGIN` | Yes | hardcoded in `docker-compose.yml` | Origin of the web app, e.g. `http://localhost:3001` |
| `DATABASE_URL` | Yes | hardcoded in `docker-compose.yml` | PostgreSQL connection string |
| `GOOGLE_GENERATIVE_AI_API_KEY` | Optional | from `.env` | Required for the `/ai` endpoint |
| `NODE_ENV` | No | — | Defaults to `development` |

### Docker Compose vs local dev

When running via `bun run docker:up`, `docker-compose.yml` injects `CORS_ORIGIN` and `DATABASE_URL` directly, so those two do not need to be in `apps/server/.env`. Only the secrets and URLs that docker-compose does not hardcode must be present:

```bash
# Minimum apps/server/.env for Docker:
BETTER_AUTH_SECRET=<generate with: openssl rand -base64 32>
BETTER_AUTH_URL=http://localhost:3000
GOOGLE_GENERATIVE_AI_API_KEY=   # leave blank if not using /ai
```

For local dev (`bun run dev:server`), all variables must be set in the `.env` file because docker-compose does not inject them:

```bash
# Full apps/server/.env for local dev:
BETTER_AUTH_SECRET=<generate with: openssl rand -base64 32>
BETTER_AUTH_URL=http://localhost:3000
CORS_ORIGIN=http://localhost:3001
DATABASE_URL=postgresql://postgres:password@localhost:5433/q-goal
GOOGLE_GENERATIVE_AI_API_KEY=
```

## Dependencies

| Package | Role |
|---------|------|
| `hono` | Web framework |
| `@q-goal/auth` | Better-Auth singleton and session handler |
| `@q-goal/db` | Drizzle ORM client and schema |
| `@q-goal/env` | Validated env var access via `@t3-oss/env-core` |
| `@ai-sdk/google` | Gemini model integration |
| `@ai-sdk/devtools` | Request/response inspection middleware |

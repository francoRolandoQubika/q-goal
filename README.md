# q-goal

This project was created with [Better-T-Stack](https://github.com/AmanVarshney01/create-better-t-stack), a modern TypeScript stack that combines React, TanStack Router, Hono, and more. It also includes a Python (`uv`) workspace for data and generative-AI work (`etl`, `genai`).

## Features

- **TypeScript** - For type safety and improved developer experience
- **TanStack Router** - File-based routing with full type safety
- **TailwindCSS** - Utility-first CSS for rapid UI development
- **Shared UI package** - shadcn/ui primitives live in `packages/ui`
- **Hono** - Lightweight, performant server framework
- **Bun** - Runtime environment
- **Drizzle** - TypeScript-first ORM
- **PostgreSQL** - Database engine
- **Authentication** - Better-Auth
- **Husky** - Git hooks for code quality
- **Oxlint** - Oxlint + Oxfmt (linting & formatting)
- **PWA** - Progressive Web App support
- **Python workspace** - `etl` and `genai` projects managed with uv (Ruff for lint & format)

## Getting Started

This project uses PostgreSQL with Drizzle ORM. You can run it **fully in Docker**
or **locally with hot reload**. Both share the dependency and environment setup below.

### Prerequisites

- [Bun](https://bun.sh) (see `packageManager` in `package.json` for the pinned version)
- [Docker](https://www.docker.com) — required for the Docker workflow, and the easiest way to run Postgres for local development
- [uv](https://docs.astral.sh/uv/) — only needed to work on the Python projects (`etl`, `genai`)

### Install dependencies

```bash
bun install
```

Recommended for both options. Even when you run everything in Docker, a local
install gives your editor type information and import resolution (no red squiggles)
and provides the database CLI used by `bun run db:push`.

### Environment variables

Each app reads config from a git-ignored `.env`. Create them from the checked-in examples:

```bash
cp apps/server/.env.example apps/server/.env
cp apps/web/.env.example apps/web/.env
```

Then set a real `BETTER_AUTH_SECRET` (at least 32 characters) in `apps/server/.env`:

```bash
openssl rand -base64 32
```

> The bundled Postgres is published on host port **5433** (not the default 5432)
> to avoid colliding with any local Postgres install. The example `DATABASE_URL`
> already targets `localhost:5433`; inside Docker the server reaches it as
> `postgres:5432`. Connect GUI clients to `localhost:5433`.

### Option A — Run everything in Docker

Builds and starts the web app, API server, and Postgres as containers.

```bash
bun run docker:up      # build + start (web, server, postgres)
```

Once the stack is healthy, apply the database schema (reaches the container's
Postgres via `localhost:5433`):

```bash
bun run db:push
```

> Skipped the local `bun install`? Run the push inside the server container
> instead, which needs no local toolchain:
>
> ```bash
> docker compose exec server bun run --filter @q-goal/db db:push
> ```

- Web app: [http://localhost:3001](http://localhost:3001)
- API server: [http://localhost:3000](http://localhost:3000)

Tail logs with `bun run docker:logs`, and stop the stack with `bun run docker:down`.

### Option B — Run locally without Docker (hot reload)

The apps run on your machine with Bun; only the database needs to be provided.

1. Start a database. The easiest option is the bundled Postgres container:

   ```bash
   bun run db:start      # docker compose up -d postgres (host port 5433)
   ```

   > Prefer no Docker at all? Point `DATABASE_URL` in `apps/server/.env` at any
   > local Postgres (e.g. `postgresql://postgres:password@localhost:5432/q-goal`)
   > and create a `q-goal` database there.

2. Apply the schema:

   ```bash
   bun run db:push
   ```

3. Start both apps with hot reload:

   ```bash
   bun run dev           # web + server
   ```

- Web app: [http://localhost:3001](http://localhost:3001)
- API server: [http://localhost:3000](http://localhost:3000)

## Python projects (`etl` & `genai`)

`etl/` (data pipelines) and `genai/` (generative-AI workflows) are Python 3.13
projects managed as a single [uv](https://docs.astral.sh/uv/) workspace, kept
separate from the Bun/JS toolchain. The workspace shares one lockfile (`uv.lock`)
and one virtual environment at the repo root.

Install Python dependencies (creates `.venv` and resolves the workspace):

```bash
uv sync
```

Run a project's entry point:

```bash
uv run etl       # -> "Hello from etl!"
uv run genai     # -> "Hello from genai!"
```

Add dependencies to a specific workspace member:

```bash
uv add --package etl pandas
uv add --package genai openai
```

Lint and format Python with Ruff (also runs automatically on staged `*.py` files
via the pre-commit hook):

```bash
uv run ruff check --fix
uv run ruff format
```

## UI Customization

React web apps in this stack share shadcn/ui primitives through `packages/ui`.

- Change design tokens and global styles in `packages/ui/src/styles/globals.css`
- Update shared primitives in `packages/ui/src/components/*`
- Adjust shadcn aliases or style config in `packages/ui/components.json` and `apps/web/components.json`

### Add more shared components

Run this from the project root to add more primitives to the shared UI package:

```bash
npx shadcn@latest add accordion dialog popover sheet table -c packages/ui
```

Import shared components like this:

```tsx
import { Button } from "@q-goal/ui/components/button";
```

### Add app-specific blocks

If you want to add app-specific blocks instead of shared primitives, run the shadcn CLI from `apps/web`.

## Deployment

### Docker Compose

- Target: web + server
- Config: `docker-compose.yml` (app Dockerfiles live in `apps/*/Dockerfile`)
- Build images: bun run docker:build
- Start: bun run docker:up
- Logs: bun run docker:logs
- Stop: bun run docker:down

Environment variables are read from each app's `.env` file (baked into web builds for public variables) and overridden in `docker-compose.yml` for container networking.

> The Python projects (`etl`, `genai`) are not yet containerized or deployed.

## Git Hooks and Formatting

- Initialize hooks: `bun run prepare`
- Run checks: `bun run check` (Oxlint + Oxfmt for JS/TS)
- Lint/format Python: `uv run ruff check --fix && uv run ruff format`

The pre-commit hook (Husky + lint-staged) runs Oxlint/Oxfmt on staged JS/TS files
and Ruff on staged Python files.

## Project Structure

```
q-goal/
├── apps/
│   ├── web/         # Frontend application (React + TanStack Router)
│   └── server/      # Backend API (Hono)
├── packages/
│   ├── ui/          # Shared shadcn/ui components and styles
│   ├── auth/        # Authentication configuration & logic
│   └── db/          # Database schema & queries
├── etl/             # Python data pipelines (uv workspace member)
└── genai/           # Python GenAI workflows (uv workspace member)
```

## Available Scripts

- `bun run dev`: Start all applications in development mode
- `bun run build`: Build all applications
- `bun run dev:web`: Start only the web application
- `bun run dev:server`: Start only the server
- `bun run check-types`: Check TypeScript types across all apps
- `bun run db:push`: Push schema changes to database
- `bun run db:generate`: Generate database client/types
- `bun run db:migrate`: Run database migrations
- `bun run db:studio`: Open database studio UI
- `bun run db:start`: Start the bundled Postgres container (detached)
- `bun run db:watch`: Start Postgres in the foreground (logs attached)
- `bun run db:stop`: Stop the Postgres container
- `bun run db:down`: Remove the Postgres container
- `bun run check`: Run Oxlint and Oxfmt
- `cd apps/web && bun run generate-pwa-assets`: Generate PWA assets
- `bun run docker:build`: Build the Docker Compose images
- `bun run docker:up`: Build and start the Docker Compose stack
- `bun run docker:logs`: Tail logs from the Docker Compose stack
- `bun run docker:down`: Stop the Docker Compose stack

### Python (uv)

- `uv sync`: Install/resolve the Python workspace
- `uv run etl`: Run the `etl` entry point
- `uv run genai`: Run the `genai` entry point
- `uv run ruff check --fix`: Lint Python
- `uv run ruff format`: Format Python

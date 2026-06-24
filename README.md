# QWC Matcher ⚽

Turn a 6-question onboarding quiz into a personalized World Cup 2026 profile card — ready to share on LinkedIn or Slack.

## The Problem

Large distributed teams struggle to connect across geographies and roles. Qubika needed an icebreaker that felt genuinely personal — not another generic "get to know your team" survey. With the World Cup 2026 happening in the same year, football was the obvious shared language.

## The Solution

QWC Matcher takes employees through a short Typeform-style onboarding quiz (6 questions), then uses AI to assign them 6 real World Cup 2026 players — one per workplace relationship slot  The result is a downloadable PNG profile card that feels hand-written for each user, not pulled from a template.

Google OAuth login → quiz → AI-streamed fun facts → downloadable player card.

## How AI Was Used

**In the product:** The Python `genai` service runs a LangGraph agent that receives all 6 quiz answers, maps them to personality traits, queries real player stats (position, caps, goals) from a local SQLite DB built from FIFA data, and streams the fun fact descriptions progressively to the React dashboard via the AI SDK. The AI output *is* the product — not a feature bolted on.

**To build it:** Every Jira story was processed with `/generate-test-cases` — a custom Claude Code skill that downloads the ticket, applies equivalence partitioning, boundary values, and negative testing, then publishes structured subtasks directly back to Jira. The entire QA pipeline was AI-assisted.

**Face matching bonus:** A secondary feature lets employees upload a photo and get matched to their World Cup lookalike using three embedding models (Only developed on the backend side). 

## Tech Stack

| Layer | Tech |
|-------|------|
| Frontend | React 19, TanStack Router, TailwindCSS, AI SDK |
| Backend | Hono 4, Drizzle ORM, PostgreSQL, Better-Auth |
| AI / GenAI | FastAPI, LangGraph, OpenAI GPT-4o-mini, DeepFace, CLIP, InsightFace |
| Runtime | Bun (JS/TS), uv + Python 3.13 (AI services) |
| Data | FIFA API scraper → face crop pipeline → SQLite embeddings DB |

## How to Run It Locally

### Prerequisites
- [Bun](https://bun.sh) (see `packageManager` in `package.json`)
- [Docker](https://www.docker.com) (for Postgres)
- [uv](https://docs.astral.sh/uv/) (for Python services)

### 1. Install dependencies

```bash
bun install
uv sync
```

### 2. Configure environment

```bash
cp apps/server/.env.example apps/server/.env
cp apps/web/.env.example apps/web/.env
cp genai/.env.example genai/.env
```

Set `BETTER_AUTH_SECRET` (32+ chars) and `OPENAI_API_KEY` in their respective `.env` files.

### 3. Start the database

```bash
bun run db:start
bun run db:push
```

### 4. Start web + server

```bash
bun run dev
```

- Web: http://localhost:3001
- API: http://localhost:3000

### 5. Start the GenAI service

```bash
uv run genai-api
```

GenAI runs on http://localhost:8002. Set `VITE_GENAI_URL=http://localhost:8002` in `apps/web/.env`.

### 6. (Optional) Build the player database from scratch

Takes ~40 minutes on first run. Pre-built data files are gitignored.

```bash
uv run genai-pipeline
```

If interrupted, re-run the same command — completed steps are skipped automatically.

## Team

| Name | Country | Role |
|------|---------|------|
| Martín Dauber | 🇺🇾 Uruguay | Project Manager |
| Facundo Sentena | 🇺🇾 Uruguay | AI Engineer |
| Eduardo Osorio | 🇨🇴 Colombia | Developer |
| Franco Rolando | 🇦🇷 Argentina | Developer |
| Marcos Storti | 🇦🇷 Argentina | QA Analyst |

---

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
uv run etl               # -> "Hello from etl!"
uv run genai-api         # Start the GenAI FastAPI server (port 8002)
uv run genai-pipeline    # Run the WC2026 face-match ETL pipeline
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
- `uv run genai-api`: Start the GenAI FastAPI server (port 8002)
- `uv run genai-pipeline`: Run the WC2026 face-match ETL pipeline
- `uv run ruff check --fix`: Lint Python
- `uv run ruff format`: Format Python

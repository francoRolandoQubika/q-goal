---
document_type: service
summary: >-
  Shared database library providing a type-safe PostgreSQL client and schema
  definitions for the entire monorepo. It is the single source of truth for all
  data...
last_updated: '2026-06-18T21:06:25.817Z'
tags:
  - service
  - typescript
  - library
service_id: db
---
# db

## Purpose

Shared database library providing a type-safe PostgreSQL client and schema definitions for the entire monorepo. It is the single source of truth for all data shapes and migrations.

## Public API / Surface

- **Exported singleton:** `db` — Drizzle ORM client instance for all database queries
- **Exported schemas:** all table definitions from `src/schema/{domain}.ts`, aggregated via barrel export
- **Entry point:** `@q-goal/db` (npm workspace import)
- No HTTP routes, webhooks, or CLI commands (library only)

## Internal Architecture

- **src/index.ts** — Main entry point; exports the `db` singleton via factory pattern (`createDb()`) and re-exports all schema tables
- **src/schema/{domain}.ts** — Domain-scoped schema modules (e.g., `auth.ts`, `posts.ts`); each file defines related tables using Drizzle's `pgTable()` API
- **src/schema/index.ts** — Barrel that re-exports all table definitions for aggregation at the package root

The `db` singleton reads `DATABASE_URL` at initialization and instantiates a Drizzle client with the full schema, creating a single connection pool shared across the monorepo.

## Query Lifecycle

1. Consumer imports `db` and table(s) from `@q-goal/db`
2. Consumer calls `db.select()`, `db.insert()`, `db.update()`, or `db.delete()` with table and SQL-like conditions
3. Drizzle translates the query builder calls to SQL and executes via the `pg` driver
4. PostgreSQL returns rows; Drizzle maps results to TypeScript types inferred from the schema
5. Consumer receives typed promise (e.g., `Promise<User[]>`)

## Data Layer

Owns all PostgreSQL table definitions, split by logical domain:

- **schema/auth.ts** — User, session, account, and verification tables managed by [[auth]] via Drizzle adapter
- **schema/{domain}.ts** — Application-specific entities (e.g., posts, messages, goals)

Migrations are introspection-based: schema changes in code are detected by Drizzle and applied via `bun run db:push`. No separate migrations folder; schema definitions in TypeScript are the source of truth.

## Configuration

- **DATABASE_URL** — PostgreSQL connection string (e.g., `postgresql://user:password@localhost:5433/q-goal`); required at runtime for the Drizzle client to connect

## Integrations

**Depends on:**
- PostgreSQL database (port 5433 in Docker environment)
- Drizzle ORM 0.45 (query builder and migration introspection)

**Used by:**
- [[auth]] — Better-Auth library reads and writes session, user, and account tables via the Drizzle adapter
- [[server]] — Hono backend issues all queries through the exported `db` client
- [[web]] — Indirectly; schema types are inferred for frontend form validation via Zod
- [[etl]], [[genai]] — Optional; Python services can read PostgreSQL schema or query the database directly

## Service-Specific Patterns

**Factory + singleton pattern:** `createDb()` ensures one connection pool per process and centralizes environment initialization.

**Domain-scoped schemas:** Each logical domain owns its own schema file (auth, posts, etc.), reducing merge conflicts and keeping related tables together.

**Barrel export aggregation:** `schema/index.ts` collects all tables; root `index.ts` re-exports them, allowing concise imports: `import { db, users, posts } from "@q-goal/db"`.

**Type-safe queries:** Drizzle's query API provides compile-time type inference; table shapes and query results are inferred directly from schema definitions, eliminating runtime mismatches between SQL and TypeScript.

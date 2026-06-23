---
document_type: service
summary: >-
  The **db** package is the shared database abstraction layer for the q-goal
  monorepo. It defines the PostgreSQL schema using Drizzle ORM, exports a
  connected ...
last_updated: '2026-06-23T19:57:02.000Z'
tags:
  - service
  - typescript
  - library
service_id: db
---
# Database Library (db)

## Purpose

The **db** package is the shared database abstraction layer for the q-goal monorepo. It defines the PostgreSQL schema using Drizzle ORM, exports a connected database client, and provides domain-organized table definitions consumed by the [[server]], [[genai]], and [[auth]] services. All services that persist data route through this package, ensuring schema consistency and type safety across the system.

## Public API / Surface

- **`src/index.ts`** — Main entry point. Exports the configured Drizzle database client and re-exports every schema table (`export * from "./schema"`) so consumers can `import { db, user, session, account, quizResult } from '@q-goal/db'`
- **`src/schema/{domain}.ts`** — Schema definitions organized by domain:
  - `schema/auth.ts` — Better-Auth tables (`user`, `session`, `account`) and relationships
  - `schema/quiz.ts` — `quiz_result` table (persisted quiz outcome per user)
  - `schema/{domain}.ts` — Additional application-specific entities

## Internal Architecture

Drizzle ORM provides the core abstraction. The package follows a code-first schema pattern:

1. **Schema Definition** — `pgTable` builders define tables with column types, constraints, defaults, and indexes
2. **Relations Layer** — `relations()` declares foreign key relationships (one-to-many, many-to-one) without explicit foreign key columns
3. **Timestamps** — `$onUpdate()` hooks automatically refresh `updatedAt` on mutations
4. **Adapters** — The Drizzle instance wraps with `drizzleAdapter` for Better-Auth integration, bridging auth session management to the database layer

All database interactions are parameterized (Drizzle enforces this); no raw SQL escaping needed.

## Consumption Lifecycle

1. Service imports database client: `import { db } from '@q-goal/db'`
2. Service imports schema table(s): `import { user, session } from '@q-goal/db'`
3. Service constructs a query: `db.select().from(user).where(eq(user.email, email))`
4. Drizzle compiles to parameterized SQL and executes against PostgreSQL
5. Result is returned with full TypeScript type inference

## Data Layer

**Owned Tables:**
- **`user`** — User accounts (id, name, email, emailVerified, createdAt, updatedAt)
- **`session`** — Active sessions linked to users (userId foreign key, sessionToken, expires)
- **`account`** — OAuth provider links (userId, provider, providerAccountId, accessToken, refreshToken)
- **`quiz_result`** — Persisted quiz outcome, one row per user (`userId` unique FK → `user.id`, cascade): `role`, `outro`, `assignments` (jsonb), audit timestamps; indexed on `userId`
- **`{domain}_*`** — Additional application tables organized by business domain

Relations: `user` ↔ `session` (one-to-many), `user` ↔ `account` (one-to-many), `user` ↔ `quiz_result` (one-to-one), cascade delete configured.

## Configuration

- **`DATABASE_URL`** — PostgreSQL connection string (format: `postgresql://user:password@host:port/database`). Required by Drizzle at client initialization.

## Integrations

**PostgreSQL** (port 5433) — Primary data store. Drizzle client connects via DATABASE_URL connection pooling (pg library). Schema migrations applied via `bun run --filter @q-goal/db db:push` (Drizzle Kit).

**Better-Auth** (via [[auth]]) — Consumes db schema via `drizzleAdapter(db, { provider: 'pg', schema })`. Better-Auth delegates all session/user/account writes to this database client, avoiding direct database code in the auth service.

## Service-Specific Patterns

**Schema-as-Code** — Database schema is TypeScript; running migrations is code-first (`db:push` regenerates schema from definitions). No separate SQL migration files.

**Relations Declarative Pattern** — Foreign key relationships are declared via `relations()` builder, not inline foreign key columns. Enables clean separation of concerns: schema defines shape, relations define connectivity.

**Adapter Pattern** — `drizzleAdapter` wraps the db client for Better-Auth. Allows services like **auth** to remain ORM-agnostic while leveraging Drizzle at the storage boundary.

**Domain-Scoped Organization** — Schema files organized by business domain (auth.ts, items.ts). Tables and their relations co-locate within domain files. Reduces coupling; new domains add files without modifying existing ones.

**Timestamp Automation** — `defaultNow()` + `$onUpdate()` provide automatic audit trails without service-layer timestamp management.

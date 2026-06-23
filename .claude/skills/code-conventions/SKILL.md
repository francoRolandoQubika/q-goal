---
name: code-conventions
description: Project-specific coding conventions for monorepo, Zod validation, Drizzle ORM, and shared packages
disable-model-invocation: false
version: 1.0
---

# Code Conventions

## Monorepo Import Rules

Always import shared packages using the `@q-goal/<name>` alias, never relative paths across workspaces.

```typescript
// WRONG — relative imports across packages
import { schema } from '../../../packages/db/src/schema/auth';

// CORRECT
import { schema } from '@q-goal/db';
```

Shared modules (`@q-goal/auth`, `@q-goal/db`, `@q-goal/ui`) are the single source of truth. Re-exporting from their `src/index.ts` ensures downstream consumers see the public API.

## Validation Rules

Zod is the standard validator across TypeScript services. Use it at all boundaries: server DTOs, form inputs, shared types.

```typescript
// CORRECT — Zod schema at API boundary
import { z } from 'zod';

const createUserSchema = z.object({
  email: z.string().email(),
  name: z.string().min(1),
});

type CreateUserDTO = z.infer<typeof createUserSchema>;

app.post('/users', async (c) => {
  const result = createUserSchema.safeParse(await c.req.json());
  if (!result.success) return c.json({ errors: result.error.flatten() }, 400);
  // result.data is type-safe
});
```

Share validation schemas in `packages/db` or create a `packages/schemas` if schemas span multiple domains. Never duplicate schema definitions.

## Data Layer Rules

Drizzle ORM is the database abstraction. Always:

1. Define schema in `packages/db/src/schema/{domain}.ts`
2. Export from `packages/db/src/index.ts` so consumers access via `import { schema } from '@q-goal/db'`
3. Run migrations with `bun run --filter @q-goal/db db:push`

```typescript
// packages/db/src/schema/auth.ts
import { pgTable, text, timestamp } from 'drizzle-orm/pg-core';

export const users = pgTable('users', {
  id: text('id').primaryKey(),
  email: text('email').notNull().unique(),
  createdAt: timestamp('created_at').defaultNow(),
});
```

Keep Drizzle logic in the service layer; never expose ORM objects to the frontend. Always use prepared statements and parameterized queries (Drizzle does this by default).

## Gotchas

### Environment Variables Are Not Synchronized Across Services

Each service reads its own `.env` file. The server, web, auth, and db packages each have separate env configurations.

```typescript
// WRONG — assumes DATABASE_URL exists in apps/web/.env
const db = drizzle(process.env.DATABASE_URL);

// CORRECT — web imports shared db package which reads DATABASE_URL from packages/db context
import { db } from '@q-goal/db';
```

### Bun Workspace Imports Require Exact Path Endings

Node module resolution in Bun requires explicit `/src/index.ts` or the package.json `exports` field. Ambiguous paths fail silently.

```typescript
// WRONG — Bun may not resolve this correctly
import { schema } from '@q-goal/db';

// CORRECT — if packages/db/package.json lacks "exports", use full path
import { schema } from '@q-goal/db/src/index.ts';
```

Check `package.json` exports field; if missing, use full paths.

### Postgres Connection Port Is 5433, Not 5432

Docker remaps postgres to 5433 to avoid collision with the user's local Postgres.app.

```typescript
// CORRECT — connection string uses port 5433
const connectionString = 'postgresql://user:pass@localhost:5433/q_goal';
```

## Code-Style Conventions

- **Imports:** sort by `node` → `@q-goal/*` → relative paths; use ES modules consistently
- **Naming:** camelCase for variables/functions, PascalCase for types/classes, UPPER_SNAKE_CASE for constants
- **React:** functional components only; use hooks; no class components
- **Async/await:** prefer async/await over `.then()` chains; handle errors explicitly
- **Type safety:** leverage TypeScript strict mode; avoid `any` and `as` casts
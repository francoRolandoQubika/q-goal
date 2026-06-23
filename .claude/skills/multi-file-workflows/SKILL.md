---
name: multi-file-workflows
description: Ordered checklists for cross-cutting changes — add endpoint, add entity, add route
disable-model-invocation: false
version: 1.0
---

# Multi-File Workflows

## Adding a New API Endpoint

1. Define request/response schemas in `packages/db/src/schema/{domain}.ts` (if new entity) or reuse existing
2. Create DTO schema in the service layer (server) using Zod
3. Add endpoint handler in `apps/server/src/index.ts`
4. Export shared types from `packages/db/src/index.ts` if needed by frontend
5. Call endpoint from frontend `apps/web/src/routes/{page}.tsx` or service layer
6. Test the endpoint manually (curl or Postman) before commit

```typescript
// apps/server/src/index.ts
import { z } from 'zod';
import { hc } from 'hono/client';

const createItemSchema = z.object({
  title: z.string().min(1),
  description: z.string(),
});

app.post('/items', async (c) => {
  const body = createItemSchema.safeParse(await c.req.json());
  if (!body.success) return c.json({ error: 'Invalid input' }, 400);
  // TODO: save to database
  return c.json({ id: '1', ...body.data });
});
```

> **Gotcha**: Don't forget to update the frontend client type if the endpoint signature changes. Use Hono's `hc` RPC client to auto-generate types from the server.

## Adding a New Database Entity

1. Create schema table in `packages/db/src/schema/{domain}.ts` (or extend existing domain file)
2. Export the table from `packages/db/src/index.ts`
3. Run `bun run --filter @q-goal/db db:push` to create migration
4. Add repository/service methods in `apps/server/src/` to query the table
5. Wire endpoints (see "Adding a New API Endpoint" above)

```typescript
// packages/db/src/schema/items.ts
import { pgTable, text, timestamp, serial } from 'drizzle-orm/pg-core';

export const items = pgTable('items', {
  id: serial('id').primaryKey(),
  title: text('title').notNull(),
  description: text('description'),
  createdAt: timestamp('created_at').defaultNow(),
});
```

> **Gotcha**: Always export new tables from `packages/db/src/index.ts` or downstream code cannot import them. Run migrations immediately after schema changes; schema drift causes silent failures.

## Adding a New Shared Type or DTO

1. Create or edit schema file in `packages/db/src/schema/` (for database-backed types) or create new `packages/shared/` package (for stateless DTOs)
2. Export type from `packages/db/src/index.ts` or the new package's `src/index.ts`
3. Import in both frontend and server using `@q-goal/db` or `@q-goal/shared`
4. Use Zod `.infer<typeof schema>` to derive TypeScript types from runtime validators

```typescript
// packages/db/src/schema/user.ts
import { z } from 'zod';

export const userSchema = z.object({
  id: z.string(),
  email: z.string().email(),
  role: z.enum(['admin', 'user']),
});

export type User = z.infer<typeof userSchema>;
```

> **Gotcha**: Never duplicate type definitions. If both `packages/auth` and `packages/db` need a `User` type, define it once and re-export it from the other. Duplication causes type drift and bugs.

## Adding a New React Route

1. Create route file in `apps/web/src/routes/{name}.tsx` (TanStack Router page) or `apps/web/src/routes/{group}/route.tsx` (layout)
2. Create components in `apps/web/src/components/{name}.tsx`
3. Import shared UI from `packages/ui`
4. Fetch data from server in route loaders or inside components using `useQuery` (from `@ai-sdk/react`)
5. Test route in dev server at `http://localhost:3001/{path}`

```typescript
// apps/web/src/routes/items.tsx
import { createFileRoute } from '@tanstack/react-router';
import { ItemList } from '../components/item-list';

export const Route = createFileRoute('/items')({
  component: ItemsPage,
});

function ItemsPage() {
  return (
    <div>
      <h1>Items</h1>
      <ItemList />
    </div>
  );
}
```

> **Gotcha**: TanStack Router requires exact file naming (`__root.tsx`, `{group}/route.tsx`, `{name}.tsx`). Misspelled files are silently ignored and routes don't register.
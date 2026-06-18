---
name: multi-file-workflows
description: Ordered checklists for cross-cutting changes — add endpoint, add entity, add route
disable-model-invocation: false
version: 1.0
---

# Multi-File Workflows

## Adding a New API Endpoint

1. Create the Zod validator in `packages/db/src/index.ts` or create a dedicated validators package
2. Create the route handler in `apps/server/src/index.ts` (or split into modules as the server grows)
3. Validate request body and parse with Zod
4. Call the service logic (or inline if simple)
5. Return JSON response

```typescript
// apps/server/src/index.ts
import { z } from "zod";

const createPostSchema = z.object({
  title: z.string().min(1),
  content: z.string().min(1),
});

app.post("/posts", async (c) => {
  const body = await c.req.json();
  const validated = createPostSchema.safeParse(body);
  if (!validated.success) {
    return c.json({ error: "Invalid request" }, 400);
  }
  const post = await db.insert(posts).values(validated.data).returning();
  return c.json(post);
});
```

## Adding a New Database Entity

1. Create the Drizzle schema in `packages/db/src/schema/{domain}.ts`
2. Export the table from `packages/db/src/schema/index.ts`
3. Re-export from `packages/db/src/index.ts`
4. Run `bun run db:push` to apply the migration
5. Use the table in service/route code via `import { <table> } from "@q-goal/db"`

```typescript
// packages/db/src/schema/posts.ts
import { pgTable, text, serial, timestamp } from "drizzle-orm/pg-core";

export const posts = pgTable("posts", {
  id: serial("id").primaryKey(),
  title: text("title").notNull(),
  content: text("content").notNull(),
  createdAt: timestamp("created_at").defaultNow(),
});
```

```typescript
// packages/db/src/schema/index.ts
export * from "./posts";
```

```typescript
// packages/db/src/index.ts
export { db } from "./client";
export * from "./schema";
```

> **Gotcha**: Always run `db:push` before using the new table, or Drizzle queries will fail at runtime.

## Adding a New Frontend Route

1. Create the TanStack Router file in `apps/web/src/routes/{name}.tsx`
2. Export a component and configure with `createFileRoute()`
3. Optional: create a sibling layout route for grouped routes (e.g., `_auth/route.tsx` wraps auth pages)
4. Access route params with `useParams()`
5. Import and use UI components from `@q-goal/ui` and shared logic from `@q-goal/db`

```typescript
// apps/web/src/routes/posts.$id.tsx
import { createFileRoute } from "@tanstack/react-router";
import { useParams } from "@tanstack/react-router";

export const Route = createFileRoute("/posts/$id")({
  component: PostDetail,
});

function PostDetail() {
  const { id } = useParams({ from: "/posts/$id" });
  const postId = parseInt(id, 10);
  
  return <div>Post {postId}</div>;
}
```

## Adding a New Shared Type or Validator

1. Create or update `packages/ui/src/lib/utils.ts` (or create a dedicated `@q-goal/types` package)
2. Define the type/validator (use Zod for schema validation)
3. Export from the package barrel (`packages/<name>/src/index.ts`)
4. Import in web, server, or auth via `@q-goal/<name>`

```typescript
// packages/ui/src/index.ts (or create packages/types/src/index.ts)
import { z } from "zod";

export const userSchema = z.object({
  id: z.number(),
  email: z.string().email(),
  name: z.string(),
});

export type User = z.infer<typeof userSchema>;
```
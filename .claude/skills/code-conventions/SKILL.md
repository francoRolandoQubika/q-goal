---
name: code-conventions
description: Project-specific coding conventions, validation rules, monorepo patterns, and gotchas
disable-model-invocation: false
version: 1.0
---

# Code Conventions

## Validation Rules

Zod is the validation library across the stack. Use consistent validator placement:

- **Frontend forms:** Zod validator in the form component or custom hook; pair with `@hookform/resolvers` for React Hook Form
- **Backend request DTOs:** Zod validator in `packages/db` or app-local service layer; validate in Hono route handler before passing to service
- **Shared types:** Zod validator in shared `@q-goal/<package>` barrel; import and reuse everywhere

```typescript
// packages/shared-validators (if created)
import { z } from "zod";

export const userCreateSchema = z.object({
  email: z.string().email(),
  name: z.string().min(1),
});

export type UserCreate = z.infer<typeof userCreateSchema>;
```

```typescript
// apps/server/src/routes/users.ts
import { userCreateSchema } from "@q-goal/validators";

app.post("/users", async (c) => {
  const body = await c.req.json();
  const parsed = userCreateSchema.safeParse(body);
  if (!parsed.success) {
    return c.json({ errors: parsed.error.issues }, 400);
  }
  // Use parsed.data
});
```

## Monorepo Cross-Package Imports

Never use relative paths across packages. Always import from the `@q-goal/<package>` namespace.

```typescript
// WRONG
import { db } from "../../packages/db/src/index";

// CORRECT
import { db } from "@q-goal/db";
```

Update the barrel exports (`packages/<name>/src/index.ts`) whenever you add a new public type or function.

## Environment Variables

Server and web each have their own `.env` file (copied from `.env.example` during setup). Keep environment-specific configuration in those files; never hardcode config.

```bash
# apps/server/.env.example
DATABASE_URL=postgresql://...
AUTH_SECRET=<generated-by-openssl>
```

## Gotchas

### Better-Auth Session Management

Better-Auth stores session state in the database. If you modify a user's role or permissions, the active session does NOT reflect the change until the user logs out and back in.

```typescript
// WRONG — user still has old role in this session
await db.update(users).set({ role: "admin" }).where(eq(users.id, userId));
// Response sent with old cached session

// CORRECT — invalidate the session
await db.update(users).set({ role: "admin" }).where(eq(users.id, userId));
await auth.api.deleteSession({ sessionId: req.auth.session.id });
```

### Drizzle Transactions Don't Auto-Rollback

Drizzle does not rollback on thrown exceptions. You must explicitly handle transaction scope.

```typescript
// WRONG — orphans the order if inventory decrement fails
async function createOrder(data: OrderDto) {
  await db.insert(orders).values(data);
  await inventoryService.decrement(data.items); // throws
  // order exists without inventory
}

// CORRECT
async function createOrder(data: OrderDto) {
  return await db.transaction(async (tx) => {
    const order = await tx.insert(orders).values(data).returning();
    await inventoryService.decrement(data.items, tx);
    return order;
  });
}
```

### TanStack Router Params Are Always Strings

`useParams()` returns strings, not parsed types. Validate/coerce them explicitly.

```typescript
// WRONG — param might be "invalid", not a number
const { id } = useParams({ from: "/posts/$id" });
const numId = id as number; // lies to TypeScript

// CORRECT
const { id } = useParams({ from: "/posts/$id" });
const numId = parseInt(id, 10);
if (isNaN(numId)) return <NotFound />;
```
---
name: testing-conventions
description: Testing conventions, strategies, and framework recommendations (testing framework not yet adopted)
disable-model-invocation: false
version: 1.0
---

# Testing Conventions

## Testing Status

**No testing framework is currently configured across any service (web, server, auth, db, ui, etl, genai).** When testing is adopted, follow the recommendations below.

## Recommended Test Frameworks

- **TypeScript services** (web, server, auth, db, ui): **Vitest** — fast, ESM-native, great TypeScript support, Vite integration
- **Python services** (etl, genai): **pytest** — standard, fixtures, parametrization, excellent CLI

## Testing Philosophy

When tests are written, follow these principles:

- **Test behavior, not implementation.** A test for "POST /users returns 201" is better than "createUser calls db.insert"
- **Test boundaries, not internals.** Test route handlers and service APIs; skip testing private helpers that are covered by their public callers
- **Integration > unit for critical paths.** For auth, DB, and payment flows, a real database in tests beats mocks — see "What NOT to Mock"
- **Mock external services.** 3rd-party APIs (OpenAI, Stripe, email vendors) should always be mocked to avoid flaky tests and avoid charges

## Unit Test Patterns

When implemented, unit tests should follow this pattern:

```typescript
// apps/server/src/routes/posts.test.ts
import { describe, it, expect } from "vitest";
import { createPostSchema } from "./posts";

describe("POST /posts", () => {
  it("validates request body", () => {
    const valid = { title: "My Post", content: "Hello" };
    const result = createPostSchema.safeParse(valid);
    expect(result.success).toBe(true);
  });

  it("rejects missing title", () => {
    const invalid = { content: "Hello" };
    const result = createPostSchema.safeParse(invalid);
    expect(result.success).toBe(false);
  });
});
```

## Integration Test Patterns

For route handlers and services, use integration tests with a real (test) database:

```typescript
// apps/server/src/routes/posts.integration.test.ts
import { describe, it, expect, beforeEach } from "vitest";
import { db } from "@q-goal/db";
import { testClient } from "hono/testing";
import app from "../index";

describe("POST /posts (integration)", () => {
  beforeEach(async () => {
    // Seed or reset database state
    await db.delete(posts);
  });

  it("creates a post", async () => {
    const res = await testClient(app).post("/posts").json({
      title: "Test",
      content: "Content",
    });
    expect(res.status).toBe(201);
  });
});
```

## What NOT to Mock

- **Database queries:** Use a test database (e.g., an in-memory or ephemeral Postgres instance). Mocking ORM calls masks real schema mismatches and migration bugs.
- **Better-Auth session logic:** Test with real sessions; mocking the session API gives false confidence
- **Drizzle transactions:** Test transaction rollback and atomicity with real transactions

Mock ONLY:
- External APIs (OpenAI, payment processors, email vendors)
- Time-based behavior (use `vitest.useFakeTimers()`)
- File I/O and network calls to non-test infrastructure

## Fixture Conventions (When Adopted)

- Create a `tests/fixtures/` directory at the project root or per-service
- Use a builder pattern for complex objects:

```typescript
// tests/fixtures/users.ts
export function createUser(overrides = {}) {
  return {
    id: Math.random(),
    email: "test@example.com",
    name: "Test User",
    ...overrides,
  };
}
```

- Seed the database in `beforeEach()` hooks, not in fixture files

## Coverage Expectations (When Framework Adopted)

- **Minimum 60% line coverage** for server, auth, db packages (business logic)
- **Minimum 40% for web** (UI tests are flaky; focus on critical paths and hooks)
- **Minimum 70% for Python services** (data pipelines and AI logic are critical)
- **Do NOT enforce 100% coverage.** Focus on covering error paths and side effects, not trivial getters
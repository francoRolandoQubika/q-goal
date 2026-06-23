---
name: testing-conventions
description: Project-specific testing patterns, what NOT to mock, and integration test rules
disable-model-invocation: false
version: 1.0
---

# Testing Conventions

## Testing Philosophy

Test the contract, not the implementation. For API endpoints, test request → response. For data layer, test database state. For UI, test user interactions and rendered output.

Avoid testing implementation details (e.g., function call counts, middleware execution order). Test behavior that matters to consumers.

## Unit Test Patterns

Unit tests verify single functions or methods in isolation.

```typescript
// Example: Zod schema validation
import { z } from 'zod';
import { describe, it, expect } from 'bun:test';

const userSchema = z.object({
  email: z.string().email(),
  name: z.string().min(1),
});

describe('userSchema', () => {
  it('accepts valid user data', () => {
    const result = userSchema.safeParse({
      email: 'user@example.com',
      name: 'Alice',
    });
    expect(result.success).toBe(true);
  });

  it('rejects invalid email', () => {
    const result = userSchema.safeParse({
      email: 'not-an-email',
      name: 'Alice',
    });
    expect(result.success).toBe(false);
  });
});
```

Keep unit tests fast and isolated. Mock external dependencies (HTTP calls, timers) but use real Zod schemas and utility functions.

## Integration Test Patterns

Integration tests verify multiple components working together: endpoint handlers with database reads/writes, service layers with Drizzle ORM.

```typescript
// Example: Hono endpoint with database
import { describe, it, expect, afterEach } from 'bun:test';
import { app } from '../src/index';

describe('POST /items', () => {
  afterEach(async () => {
    // Clean up test data
    await db.delete(items);
  });

  it('creates and returns item', async () => {
    const response = await app.request('/items', {
      method: 'POST',
      body: JSON.stringify({ title: 'Test Item' }),
      headers: { 'Content-Type': 'application/json' },
    });
    expect(response.status).toBe(200);
    const json = await response.json();
    expect(json).toHaveProperty('id');
    expect(json.title).toBe('Test Item');
  });
});
```

Always hit a real (test) database, not a mock. Prior incident: mocked tests passed but production migrations failed. See [[postgres-port-5433]].

### Auth-guarded endpoints: mint a real session cookie

Endpoints behind `auth.api.getSession` return 401 without a session, so an anonymous `app.request` only ever exercises the guard. To test the authenticated path, sign up/in through `/api/auth/*` and convert the response into a `cookie` header with Better-Auth's `convertSetCookieToCookie` test helper, then pass it to `app.request`. Do not stub the session.

```typescript
import { convertSetCookieToCookie } from 'better-auth/test';

async function getCookie(email: string, password: string): Promise<string> {
  const res = await app.request('/api/auth/sign-in/email', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  });
  return convertSetCookieToCookie(res.headers).get('cookie') ?? '';
}

// Authenticated request
const cookie = await getCookie('user-a@test.com', 'password123456');
const res = await app.request('/api/quiz-result', { headers: { cookie } });
```

Always include an unauthenticated case (assert 401 and that the DB was not mutated) alongside the happy path, and clean up auth rows (`user`, plus the table under test) in `afterAll`.

## What NOT to Mock

**Do not mock the database.** Use a real test database (pg, sqlite, or in-memory). Mocking Drizzle relationships or queries masks migration issues and schema bugs.

**Do not mock Zod validators.** Schema validation must be tested against real Zod instances to catch parsing bugs.

**Do not mock HTTP clients to external services (Google AI, OpenAI) unless testing offline error paths.** Instead, mock at the network boundary (intercept fetch/axios) so the actual API contract code is tested.

## Fixture Conventions

Create reusable test data factories for complex objects.

```typescript
// Example: User factory
function createUser(overrides = {}) {
  return {
    id: '1',
    email: 'test@example.com',
    name: 'Test User',
    role: 'user' as const,
    ...overrides,
  };
}

// Usage
const admin = createUser({ role: 'admin' });
```

Store fixtures in a `__fixtures__/` directory or inline in the test file if simple. Name factories as `create{Entity}()`.

## Coverage Expectations

Aim for > 70% statement coverage on critical paths (API handlers, service layer, data layer). Do not chase 100% coverage — some code paths are unreachable or not worth testing (e.g., error fallbacks on fatal crashes).

Test the golden path (happy case) and 2–3 error cases per endpoint. One untested error case per function is acceptable; five is negligence.
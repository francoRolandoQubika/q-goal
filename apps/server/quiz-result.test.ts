import { db, quizResult, user } from "@q-goal/db";
import { convertSetCookieToCookie } from "better-auth/test";
import { afterAll, afterEach, beforeAll, describe, expect, it } from "bun:test";

import app from "./src/index";

interface QuizResultRow {
  id: string;
  userId: string;
  role: string;
  outro: string;
  assignments: unknown[];
}

const VALID_ASSIGNMENT = {
  title: "Goalkeeper",
  description: "You guard the net",
  player: { id: 1, name: "M. Alisson", team: "Brazil" },
};

const VALID_BODY = {
  role: "goalkeeper",
  outro: "Great match!",
  assignments: [VALID_ASSIGNMENT],
};

async function signUpAndGetCookie(email: string, password: string): Promise<string> {
  const signUpRes = await app.request("/api/auth/sign-up/email", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password, name: email }),
  });

  if (signUpRes.ok) {
    const cookieHeaders = convertSetCookieToCookie(signUpRes.headers);
    return cookieHeaders.get("cookie") ?? "";
  }

  return getCookie(email, password);
}

async function getCookie(email: string, password: string): Promise<string> {
  const signInRes = await app.request("/api/auth/sign-in/email", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  const cookieHeaders = convertSetCookieToCookie(signInRes.headers);
  return cookieHeaders.get("cookie") ?? "";
}

beforeAll(async () => {
  await signUpAndGetCookie("user-a@test.com", "password123456");
  await signUpAndGetCookie("user-b@test.com", "password123456");
});

afterEach(async () => {
  await db.delete(quizResult);
});

afterAll(async () => {
  await db.delete(quizResult);
  await db.delete(user);
});

describe("GET /api/quiz-result — unauthenticated", () => {
  it("returns 401", async () => {
    const res = await app.request("/api/quiz-result");
    expect(res.status).toBe(401);
  });
});

describe("POST /api/quiz-result — unauthenticated", () => {
  it("returns 401 and does not write DB", async () => {
    const before = await db.select().from(quizResult);
    const res = await app.request("/api/quiz-result", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(VALID_BODY),
    });
    expect(res.status).toBe(401);
    const after = await db.select().from(quizResult);
    expect(after.length).toBe(before.length);
  });
});

describe("DELETE /api/quiz-result — unauthenticated", () => {
  it("returns 401 and does not remove an existing row", async () => {
    const cookie = await getCookie("user-a@test.com", "password123456");
    await app.request("/api/quiz-result", {
      method: "POST",
      headers: { "Content-Type": "application/json", cookie },
      body: JSON.stringify(VALID_BODY),
    });
    const before = await db.select().from(quizResult);

    const res = await app.request("/api/quiz-result", { method: "DELETE" });
    expect(res.status).toBe(401);

    const after = await db.select().from(quizResult);
    expect(after.length).toBe(before.length);
  });
});

describe("POST /api/quiz-result — invalid body", () => {
  it("returns 400 on malformed JSON", async () => {
    const cookie = await getCookie("user-a@test.com", "password123456");
    const res = await app.request("/api/quiz-result", {
      method: "POST",
      headers: { "Content-Type": "application/json", cookie },
      body: "this is not json{{{",
    });
    expect(res.status).toBe(400);
    const json = (await res.json()) as { error: string };
    expect(json.error).toBe("Invalid JSON body");
  });

  it("returns 400 when role is empty", async () => {
    const cookie = await getCookie("user-a@test.com", "password123456");
    const res = await app.request("/api/quiz-result", {
      method: "POST",
      headers: { "Content-Type": "application/json", cookie },
      body: JSON.stringify({ ...VALID_BODY, role: "" }),
    });
    expect(res.status).toBe(400);
  });

  it("returns 400 when assignments is an empty array", async () => {
    const cookie = await getCookie("user-a@test.com", "password123456");
    const res = await app.request("/api/quiz-result", {
      method: "POST",
      headers: { "Content-Type": "application/json", cookie },
      body: JSON.stringify({ ...VALID_BODY, assignments: [] }),
    });
    expect(res.status).toBe(400);
  });

  it("returns 400 when player is missing required fields", async () => {
    const cookie = await getCookie("user-a@test.com", "password123456");
    const res = await app.request("/api/quiz-result", {
      method: "POST",
      headers: { "Content-Type": "application/json", cookie },
      body: JSON.stringify({
        ...VALID_BODY,
        assignments: [{ title: "x", description: "y", player: { name: "no-id-or-team" } }],
      }),
    });
    expect(res.status).toBe(400);
  });
});

describe("POST /api/quiz-result — upsert overwrites existing row", () => {
  it("second POST updates the row and GET returns the new values", async () => {
    const cookie = await getCookie("user-a@test.com", "password123456");
    const authHeaders = { "Content-Type": "application/json", cookie };

    await app.request("/api/quiz-result", {
      method: "POST",
      headers: authHeaders,
      body: JSON.stringify(VALID_BODY),
    });

    const updatedBody = { ...VALID_BODY, role: "striker", outro: "Updated outro" };
    const secondPost = await app.request("/api/quiz-result", {
      method: "POST",
      headers: authHeaders,
      body: JSON.stringify(updatedBody),
    });
    expect(secondPost.status).toBe(200);

    const rows = await db.select().from(quizResult);
    expect(rows.length).toBe(1);

    const getRes = await app.request("/api/quiz-result", { headers: { cookie } });
    expect(getRes.status).toBe(200);
    const fetched = (await getRes.json()) as QuizResultRow;
    expect(fetched.role).toBe("striker");
    expect(fetched.outro).toBe("Updated outro");
  });
});

describe("happy path — POST → GET → DELETE → null", () => {
  it("persists on POST, returns on GET, removes on DELETE", async () => {
    const cookie = await getCookie("user-a@test.com", "password123456");
    const authHeaders = { "Content-Type": "application/json", cookie };

    const postRes = await app.request("/api/quiz-result", {
      method: "POST",
      headers: authHeaders,
      body: JSON.stringify(VALID_BODY),
    });
    expect(postRes.status).toBe(200);
    const saved = (await postRes.json()) as QuizResultRow;
    expect(saved.role).toBe(VALID_BODY.role);
    expect(saved.outro).toBe(VALID_BODY.outro);

    const getRes = await app.request("/api/quiz-result", { headers: { cookie } });
    expect(getRes.status).toBe(200);
    const fetched = (await getRes.json()) as QuizResultRow;
    expect(fetched.role).toBe(VALID_BODY.role);

    const delRes = await app.request("/api/quiz-result", {
      method: "DELETE",
      headers: { cookie },
    });
    expect(delRes.status).toBe(200);

    const getAfterDelete = await app.request("/api/quiz-result", { headers: { cookie } });
    expect(getAfterDelete.status).toBe(200);
    const afterDelete = await getAfterDelete.json();
    expect(afterDelete).toBeNull();
  });
});

describe("flow — persistence across refresh", () => {
  it("POST then a fresh GET returns the same row", async () => {
    const cookie = await getCookie("user-a@test.com", "password123456");

    await app.request("/api/quiz-result", {
      method: "POST",
      headers: { "Content-Type": "application/json", cookie },
      body: JSON.stringify(VALID_BODY),
    });

    const getRes = await app.request("/api/quiz-result", { headers: { cookie } });
    const row = (await getRes.json()) as QuizResultRow;
    expect(row.role).toBe(VALID_BODY.role);
    expect(row.assignments).toHaveLength(1);
  });
});

describe("flow — second-user isolation", () => {
  it("user A's result is not visible to user B, and B's DELETE does not affect A", async () => {
    const cookieA = await getCookie("user-a@test.com", "password123456");
    const cookieB = await getCookie("user-b@test.com", "password123456");

    await app.request("/api/quiz-result", {
      method: "POST",
      headers: { "Content-Type": "application/json", cookie: cookieA },
      body: JSON.stringify(VALID_BODY),
    });

    const getBRes = await app.request("/api/quiz-result", { headers: { cookie: cookieB } });
    const bResult = await getBRes.json();
    expect(bResult).toBeNull();

    await app.request("/api/quiz-result", {
      method: "DELETE",
      headers: { cookie: cookieB },
    });

    const getAAfterBDelete = await app.request("/api/quiz-result", {
      headers: { cookie: cookieA },
    });
    const aResult = (await getAAfterBDelete.json()) as QuizResultRow;
    expect(aResult.role).toBe(VALID_BODY.role);
  });
});

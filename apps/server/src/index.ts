import { devToolsMiddleware } from "@ai-sdk/devtools";
import { google } from "@ai-sdk/google";
import { auth } from "@q-goal/auth";
import { db, quizResult } from "@q-goal/db";
import { env } from "@q-goal/env/server";
import { streamText, convertToModelMessages, wrapLanguageModel } from "ai";
import { eq } from "drizzle-orm";
import { Hono } from "hono";
import { cors } from "hono/cors";
import { logger } from "hono/logger";
import { z } from "zod";

const app = new Hono();

app.use(logger());
app.use(
  "/*",
  cors({
    origin: env.CORS_ORIGIN,
    allowMethods: ["GET", "POST", "DELETE", "OPTIONS"],
    allowHeaders: ["Content-Type", "Authorization"],
    credentials: true,
  }),
);

app.on(["POST", "GET"], "/api/auth/*", (c) => auth.handler(c.req.raw));

const quizResultBodySchema = z.object({
  role: z.string().min(1),
  outro: z.string(),
  assignments: z
    .array(
      z.object({
        title: z.string(),
        description: z.string(),
        player: z.object({
          id: z.number(),
          name: z.string(),
          team: z.string(),
          position: z.string().optional(),
          dob: z.string().optional(),
          club: z.string().optional(),
          height_cm: z.number().optional(),
          caps: z.number().optional(),
          goals: z.number().optional(),
        }),
      }),
    )
    .min(1),
});

// Postgres jsonb (and text) columns reject NUL (U+0000); upstream LLM output
// occasionally contains stray control characters. Strip them recursively so a
// valid-looking result is always persistable instead of failing the insert.
function stripNullChars<T>(value: T): T {
  if (typeof value === "string") {
    return value.replaceAll("\u0000", "") as T;
  }
  if (Array.isArray(value)) {
    return value.map(stripNullChars) as T;
  }
  if (value !== null && typeof value === "object") {
    return Object.fromEntries(Object.entries(value).map(([k, v]) => [k, stripNullChars(v)])) as T;
  }
  return value;
}

app.get("/api/quiz-result", async (c) => {
  const session = await auth.api.getSession({ headers: c.req.raw.headers });
  if (!session) {
    return c.json({ error: "Unauthorized" }, 401);
  }

  const row = await db.query.quizResult.findFirst({
    where: eq(quizResult.userId, session.user.id),
  });

  return c.json(row ?? null);
});

app.post("/api/quiz-result", async (c) => {
  const session = await auth.api.getSession({ headers: c.req.raw.headers });
  if (!session) {
    return c.json({ error: "Unauthorized" }, 401);
  }

  let rawBody: unknown;
  try {
    rawBody = await c.req.json();
  } catch {
    return c.json({ error: "Invalid JSON body" }, 400);
  }

  const parsed = quizResultBodySchema.safeParse(rawBody);
  if (!parsed.success) {
    return c.json({ error: parsed.error.flatten() }, 400);
  }

  const role = stripNullChars(parsed.data.role);
  const outro = stripNullChars(parsed.data.outro);
  const assignments = stripNullChars(parsed.data.assignments);
  const userId = session.user.id;

  const [row] = await db
    .insert(quizResult)
    .values({ id: crypto.randomUUID(), userId, role, outro, assignments })
    .onConflictDoUpdate({
      target: quizResult.userId,
      set: { role, outro, assignments, updatedAt: new Date() },
    })
    .returning();

  return c.json(row);
});

app.delete("/api/quiz-result", async (c) => {
  const session = await auth.api.getSession({ headers: c.req.raw.headers });
  if (!session) {
    return c.json({ error: "Unauthorized" }, 401);
  }

  await db.delete(quizResult).where(eq(quizResult.userId, session.user.id));

  return c.json({ ok: true });
});

app.post("/ai", async (c) => {
  const body = await c.req.json();
  const uiMessages = body.messages || [];
  const model = wrapLanguageModel({
    model: google("gemini-2.5-flash"),
    middleware: devToolsMiddleware(),
  });
  const result = streamText({
    model,
    messages: await convertToModelMessages(uiMessages),
  });

  return result.toUIMessageStreamResponse();
});

app.get("/", (c) => {
  return c.text("OK");
});

export default app;

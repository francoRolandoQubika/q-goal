import { env } from "@q-goal/env/web";

import type { QuizResult } from "./dashboard-types";

const BASE_URL = `${env.VITE_SERVER_URL}/api/quiz-result`;

export async function fetchQuizResult(): Promise<QuizResult | null> {
  const res = await fetch(BASE_URL, { credentials: "include" });
  if (!res.ok) return null;
  return res.json() as Promise<QuizResult | null>;
}

export async function saveQuizResult(
  input: Pick<QuizResult, "role" | "outro" | "assignments">,
): Promise<QuizResult> {
  const res = await fetch(BASE_URL, {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
  if (!res.ok) {
    throw new Error(`Failed to save quiz result: ${res.status}`);
  }
  return res.json() as Promise<QuizResult>;
}

export async function deleteQuizResult(): Promise<void> {
  const res = await fetch(BASE_URL, {
    method: "DELETE",
    credentials: "include",
  });
  if (!res.ok) {
    throw new Error(`Failed to delete quiz result: ${res.status}`);
  }
}

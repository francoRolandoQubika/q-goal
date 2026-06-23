import { createFileRoute, redirect } from "@tanstack/react-router";

import { authClient } from "@/lib/auth-client";
import { fetchQuizResult } from "@/lib/quiz-result";

export const Route = createFileRoute("/")({
  beforeLoad: async () => {
    const session = await authClient.getSession();
    if (!session.data) {
      throw redirect({ to: "/login" });
    }
    const result = await fetchQuizResult();
    if (result) {
      throw redirect({ to: "/dashboard" });
    }
    throw redirect({ to: "/quiz" });
  },
  component: () => null,
});

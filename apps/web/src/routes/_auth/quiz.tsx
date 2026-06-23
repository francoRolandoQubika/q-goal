import { Button } from "@q-goal/ui/components/button";
import { Input } from "@q-goal/ui/components/input";
import { Label } from "@q-goal/ui/components/label";
import { useForm } from "@tanstack/react-form";
import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useState } from "react";
import z from "zod";
import { env } from "@q-goal/env/web";
import type { Assignment } from "../../lib/dashboard-types";

export const Route = createFileRoute("/_auth/quiz")({
  component: QuizPage,
});

interface StartResponse {
  session_id: string;
  questions: string[];
  total_questions: number;
}

interface AnswerResponse {
  status: string;
  session_id: string;
  outro: string;
  assignments: Assignment[];
}

type QuizState =
  | { step: "role-input" }
  | { step: "loading-questions" }
  | {
      step: "answering";
      role: string;
      sessionId: string;
      questions: string[];
      current: number;
      answers: string[];
    }
  | { step: "submitting"; role: string; sessionId: string; answers: string[] }
  | { step: "error"; kind: "expired" | "generic"; message: string };

const ANSWER_OPTIONS = ["A", "B", "C", "D"] as const;
const GENAI_URL = env.VITE_GENAI_URL;

function RoleInputStep({ onSubmit }: { onSubmit: (role: string) => Promise<void> }) {
  const form = useForm({
    defaultValues: { role: "" },
    onSubmit: async ({ value }) => {
      await onSubmit(value.role);
    },
    validators: {
      onSubmit: z.object({
        role: z.string().min(1, "Please describe your role"),
      }),
    },
  });

  return (
    <div className="mx-auto w-full max-w-md mt-10 p-6">
      <h1 className="mb-2 text-center text-3xl font-bold">Q-Goal Quiz</h1>
      <p className="mb-6 text-center text-muted-foreground">
        Tell us your role to get personalized questions.
      </p>

      <form
        onSubmit={(e) => {
          e.preventDefault();
          e.stopPropagation();
          form.handleSubmit();
        }}
        className="space-y-4"
      >
        <form.Field name="role">
          {(field) => (
            <div className="space-y-2">
              <Label htmlFor={field.name}>Your role</Label>
              <Input
                id={field.name}
                name={field.name}
                placeholder="e.g. Goalkeeper, Midfielder, Coach"
                value={field.state.value}
                onBlur={field.handleBlur}
                onChange={(e) => field.handleChange(e.target.value)}
              />
              {field.state.meta.errors.map((error) => (
                <p key={error?.message} className="text-red-500 text-sm">
                  {error?.message}
                </p>
              ))}
            </div>
          )}
        </form.Field>

        <form.Subscribe
          selector={(state) => ({
            canSubmit: state.canSubmit,
            isSubmitting: state.isSubmitting,
          })}
        >
          {({ canSubmit, isSubmitting }) => (
            <Button type="submit" className="w-full" disabled={!canSubmit || isSubmitting}>
              {isSubmitting ? "Starting quiz..." : "Start Quiz"}
            </Button>
          )}
        </form.Subscribe>
      </form>
    </div>
  );
}

function AnsweringStep({
  state,
  onAnswer,
}: {
  state: Extract<QuizState, { step: "answering" }>;
  onAnswer: (letter: string) => void;
}) {
  const { questions, current } = state;
  const question = questions[current];

  return (
    <div className="mx-auto w-full max-w-xl mt-10 p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold">Question</h2>
        <span className="text-sm text-muted-foreground">
          {current + 1} / {questions.length}
        </span>
      </div>

      <p className="whitespace-pre-wrap text-base leading-relaxed">{question}</p>

      <div className="grid grid-cols-2 gap-3">
        {ANSWER_OPTIONS.map((letter) => (
          <Button
            key={letter}
            variant="outline"
            className="h-12 text-base font-medium"
            onClick={() => onAnswer(letter)}
          >
            {letter}
          </Button>
        ))}
      </div>
    </div>
  );
}

function ErrorStep({
  state,
  onRestart,
}: {
  state: Extract<QuizState, { step: "error" }>;
  onRestart: () => void;
}) {
  return (
    <div className="mx-auto w-full max-w-md mt-10 p-6 text-center space-y-4">
      <p className="text-red-500">{state.message}</p>
      <Button onClick={onRestart}>{state.kind === "expired" ? "Restart quiz" : "Try again"}</Button>
    </div>
  );
}

function QuizPage() {
  const navigate = useNavigate();
  const [quizState, setQuizState] = useState<QuizState>({ step: "role-input" });

  async function handleRoleSubmit(role: string) {
    setQuizState({ step: "loading-questions" });

    try {
      const response = await fetch(`${GENAI_URL}/quiz/start`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ role }),
      });

      if (!response.ok) {
        setQuizState({
          step: "error",
          kind: "generic",
          message: "Could not load quiz. Please try again.",
        });
        return;
      }

      const data: StartResponse = await response.json();
      setQuizState({
        step: "answering",
        role,
        sessionId: data.session_id,
        questions: data.questions,
        current: 0,
        answers: [],
      });
    } catch {
      setQuizState({
        step: "error",
        kind: "generic",
        message: "Could not load quiz. Please try again.",
      });
    }
  }

  async function handleAnswer(letter: string) {
    if (quizState.step !== "answering") return;

    const { role, sessionId, questions, current, answers } = quizState;
    const nextAnswers = [...answers, letter];
    const isLast = current === questions.length - 1;

    if (!isLast) {
      setQuizState({
        ...quizState,
        current: current + 1,
        answers: nextAnswers,
      });
      return;
    }

    setQuizState({
      step: "submitting",
      role,
      sessionId,
      answers: nextAnswers,
    });

    try {
      const response = await fetch(`${GENAI_URL}/quiz/answer`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: sessionId,
          answers: nextAnswers,
        }),
      });

      if (response.status === 404) {
        setQuizState({
          step: "error",
          kind: "expired",
          message: "Session expired. Please start the quiz again.",
        });
        return;
      }

      if (!response.ok) {
        setQuizState({
          step: "error",
          kind: "generic",
          message: "Could not submit answers. Please try again.",
        });
        return;
      }

      const data: AnswerResponse = await response.json();
      navigate({
        to: "/dashboard",
        state: (prev) => ({
          ...prev,
          assignments: data.assignments,
          outro: data.outro,
          role,
        }),
      });
    } catch {
      setQuizState({
        step: "error",
        kind: "generic",
        message: "Could not submit answers. Please try again.",
      });
    }
  }

  function handleRestart() {
    setQuizState({ step: "role-input" });
  }

  if (quizState.step === "role-input") {
    return <RoleInputStep onSubmit={handleRoleSubmit} />;
  }

  if (quizState.step === "loading-questions" || quizState.step === "submitting") {
    return (
      <div className="mx-auto w-full max-w-md mt-10 p-6 text-center">
        <p className="text-muted-foreground">Loading...</p>
      </div>
    );
  }

  if (quizState.step === "answering") {
    return <AnsweringStep state={quizState} onAnswer={handleAnswer} />;
  }

  return <ErrorStep state={quizState} onRestart={handleRestart} />;
}

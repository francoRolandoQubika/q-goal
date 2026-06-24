import { Button } from "@q-goal/ui/components/button";
import { toast } from "sonner";
import { createFileRoute, redirect, useNavigate, useRouter } from "@tanstack/react-router";
import { useState } from "react";
import { DashboardHeader } from "../../components/dashboard-header";
import { PlayerCard } from "../../components/player-card";
import { RedoQuizDialog } from "../../components/redo-quiz-dialog";
import { deleteQuizResult, fetchQuizResult } from "../../lib/quiz-result";

export const Route = createFileRoute("/_auth/dashboard")({
  loader: async () => {
    const result = await fetchQuizResult();
    if (!result) {
      throw redirect({ to: "/quiz" });
    }
    return result;
  },
  component: DashboardPage,
});

/** OKLCH team accent colors matching the Sticker Album token palette. */
const TEAM_ACCENTS: Record<string, string> = {
  argentina: "oklch(0.55 0.20 230)",
  brazil: "oklch(0.55 0.18 155)",
  france: "oklch(0.50 0.22 270)",
  england: "oklch(0.55 0.18 25)",
  spain: "oklch(0.65 0.18 55)",
  germany: "oklch(0.65 0.04 265)",
  portugal: "oklch(0.50 0.20 15)",
  usa: "oklch(0.50 0.20 250)",
};

function DashboardPage() {
  const { session } = Route.useRouteContext();
  const data = Route.useLoaderData();
  const [redoOpen, setRedoOpen] = useState(false);
  const router = useRouter();
  const navigate = useNavigate();

  const team = data.assignments[0]?.player.team ?? "";
  const teamAccent = TEAM_ACCENTS[team.toLowerCase()] ?? "oklch(0.60 0.22 250)";

  return (
    <div className="min-h-screen" style={{ "--team-accent": teamAccent } as React.CSSProperties}>
      <div
        id="dashboard-share-target"
        className="mx-auto max-w-4xl space-y-7 px-5 py-8"
        style={{ backgroundColor: `color-mix(in oklch, ${teamAccent} 13%, transparent)` }}
      >
        <DashboardHeader
          name={session.data?.user.name ?? ""}
          avatarUrl={session.data?.user.image}
          role={data.role}
          team={team}
        />

        <div className="space-y-1">
          <h1 className="font-display text-4xl sm:text-5xl">Your figurita pack</h1>
          <p className="text-muted-foreground">
            Based on how you play, here's who you'd be on the pitch.
          </p>
        </div>

        <div className="grid grid-cols-1 gap-5 md:grid-cols-2">
          {data.assignments.length === 0 ? (
            <p className="col-span-full text-center text-muted-foreground">No results yet</p>
          ) : (
            data.assignments.map((assignment) => (
              <PlayerCard key={assignment.player.id} assignment={assignment} />
            ))
          )}
        </div>

        {data.outro && (
          <p
            className="border-l-2 pl-4 text-base leading-relaxed text-muted-foreground"
            style={{ borderColor: "var(--team-accent)" }}
          >
            {data.outro}
          </p>
        )}
      </div>

      <div className="mx-auto flex max-w-4xl flex-wrap gap-3 border-t border-foreground/10 px-5 py-5">
        <Button
          disabled
          title="Coming soon"
          style={{ backgroundColor: "var(--team-accent)", borderColor: "var(--team-accent)" }}
        >
          Download PNG
        </Button>
        <Button disabled title="Coming soon" variant="outline">
          Share
        </Button>
        <Button variant="ghost" className="ml-auto" onClick={() => setRedoOpen(true)}>
          Redo quiz
        </Button>
      </div>
      <RedoQuizDialog
        open={redoOpen}
        onOpenChange={setRedoOpen}
        onConfirm={async () => {
          try {
            await deleteQuizResult();
            await router.invalidate();
            navigate({ to: "/quiz" });
          } catch {
            toast.error("Failed to reset quiz. Please try again.");
          }
        }}
      />
    </div>
  );
}

import { Button } from "@q-goal/ui/components/button";
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

const TEAM_COLORS: Record<string, { bg: string; accent: string; text: string }> = {
  argentina: { bg: "#74b9ff", accent: "#0984e3", text: "#ffffff" },
  brazil: { bg: "#55efc4", accent: "#00b894", text: "#2d3436" },
  france: { bg: "#6c5ce7", accent: "#2d3436", text: "#ffffff" },
  england: { bg: "#e17055", accent: "#d63031", text: "#ffffff" },
  spain: { bg: "#fdcb6e", accent: "#e17055", text: "#2d3436" },
  germany: { bg: "#dfe6e9", accent: "#636e72", text: "#2d3436" },
  portugal: { bg: "#fd79a8", accent: "#e84393", text: "#ffffff" },
  usa: { bg: "#74b9ff", accent: "#0652DD", text: "#ffffff" },
  default: { bg: "#b2bec3", accent: "#636e72", text: "#2d3436" },
};

function DashboardPage() {
  const { session } = Route.useRouteContext();
  const data = Route.useLoaderData();
  const [redoOpen, setRedoOpen] = useState(false);
  const router = useRouter();
  const navigate = useNavigate();

  const team = data.assignments[0]?.player.team ?? "";
  const theme = TEAM_COLORS[team.toLowerCase()] ?? TEAM_COLORS.default;

  return (
    <div
      id="dashboard-share-target"
      style={{ backgroundColor: theme.bg, color: theme.text }}
      className="min-h-screen"
    >
      <DashboardHeader
        name={session.data?.user.name ?? ""}
        avatarUrl={session.data?.user.image}
        role={data.role}
        team={team}
      />

      <div className="px-6 pb-6 space-y-6">
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          {data.assignments.length === 0 ? (
            <p className="col-span-full text-center opacity-70">No results yet</p>
          ) : (
            data.assignments.map((assignment) => (
              <PlayerCard
                key={assignment.player.id}
                assignment={assignment}
                accentColor={theme.accent}
              />
            ))
          )}
        </div>

        {data.outro && <p className="text-base leading-relaxed">{data.outro}</p>}

        <div className="flex gap-3">
          <Button disabled>Download PNG</Button>
          <Button disabled>Share</Button>
          <Button variant="outline" onClick={() => setRedoOpen(true)}>
            Redo quiz
          </Button>
        </div>
        <RedoQuizDialog
          open={redoOpen}
          onOpenChange={setRedoOpen}
          onConfirm={async () => {
            await deleteQuizResult();
            await router.invalidate();
            navigate({ to: "/quiz" });
          }}
        />
      </div>
    </div>
  );
}

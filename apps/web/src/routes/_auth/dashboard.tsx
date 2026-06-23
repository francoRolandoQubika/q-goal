import { Button } from "@q-goal/ui/components/button";
import { createFileRoute, useNavigate, useRouterState } from "@tanstack/react-router";
import { useEffect } from "react";
import { DashboardHeader } from "../../components/dashboard-header";
import { PlayerCard } from "../../components/player-card";
import type { DashboardState } from "../../lib/dashboard-types";

export const Route = createFileRoute("/_auth/dashboard")({
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
  const navigate = useNavigate();
  const { session } = Route.useRouteContext();
  const state = useRouterState({
    select: (s) => s.location.state as unknown as DashboardState | undefined,
  });

  useEffect(() => {
    if (!state) {
      navigate({ to: "/quiz", replace: true });
    }
  }, [state, navigate]);

  if (!state) {
    return null;
  }

  const team = state.assignments[0]?.player.team ?? "";
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
        role={state.role}
        team={team}
      />

      <div className="px-6 pb-6 space-y-6">
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          {state.assignments.length === 0 ? (
            <p className="col-span-full text-center opacity-70">No results yet</p>
          ) : (
            state.assignments.map((assignment, i) => (
              <PlayerCard key={i} assignment={assignment} accentColor={theme.accent} />
            ))
          )}
        </div>

        {state.outro && <p className="text-base leading-relaxed">{state.outro}</p>}

        <div className="flex gap-3">
          <Button disabled>Download PNG</Button>
          <Button disabled>Share</Button>
        </div>
      </div>
    </div>
  );
}

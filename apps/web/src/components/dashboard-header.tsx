import { cn } from "@q-goal/ui/lib/utils";
import { useState } from "react";

const TEAM_FLAGS: Record<string, string> = {
  argentina: "🇦🇷",
  brazil: "🇧🇷",
  france: "🇫🇷",
  england: "🏴󠁧󠁢󠁥󠁮󠁧󠁿",
  spain: "🇪🇸",
  germany: "🇩🇪",
  portugal: "🇵🇹",
  usa: "🇺🇸",
};

function teamFlag(team: string): string {
  return TEAM_FLAGS[team.toLowerCase()] ?? "⚽";
}

interface DashboardHeaderProps {
  name: string;
  avatarUrl?: string | null;
  role: string;
  teams: string[];
}

export function DashboardHeader({ name, avatarUrl, role, teams }: DashboardHeaderProps) {
  const [avatarFailed, setAvatarFailed] = useState(false);

  const initial = name?.[0]?.toUpperCase() ?? "?";

  return (
    <div className="flex flex-col gap-4 sm:flex-row sm:items-center">
      <div className="flex min-w-0 items-center gap-4">
        {avatarUrl && !avatarFailed ? (
          <img
            src={avatarUrl}
            alt={name}
            className="h-14 w-14 shrink-0 rounded-full border-2 object-cover"
            style={{ borderColor: "var(--team-accent)" }}
            onError={() => setAvatarFailed(true)}
          />
        ) : (
          <div
            className={cn(
              "flex h-14 w-14 shrink-0 items-center justify-center rounded-full border-2 bg-primary font-display text-2xl text-primary-foreground",
            )}
            style={{ borderColor: "var(--team-accent)" }}
          >
            {initial}
          </div>
        )}

        <div className="flex min-w-0 flex-col">
          <span className="text-[0.65rem] font-medium uppercase tracking-[0.2em] text-muted-foreground">
            Scouting report
          </span>
          <span className="truncate font-display text-2xl leading-none">{name}</span>
          <span className="truncate text-sm text-muted-foreground">{role}</span>
        </div>
      </div>

      {teams.length > 0 && (
        <div className="flex flex-col gap-1 sm:ml-auto sm:items-end">
          <span className="text-[0.6rem] font-medium uppercase tracking-[0.2em] text-muted-foreground">
            {teams.length > 1 ? "Your nations" : "Your nation"}
          </span>
          <div className="flex flex-wrap gap-1.5 sm:justify-end">
            {teams.map((team) => (
              <div
                key={team}
                className="flex items-center gap-1.5 rounded-full border px-3 py-1.5"
                style={{
                  borderColor: "color-mix(in oklch, var(--team-accent) 55%, transparent)",
                  backgroundColor: "color-mix(in oklch, var(--team-accent) 14%, transparent)",
                }}
              >
                <span className="text-base" aria-hidden="true">
                  {teamFlag(team)}
                </span>
                <span className="text-xs font-semibold uppercase tracking-wide">{team}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

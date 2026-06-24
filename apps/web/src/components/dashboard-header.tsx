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
  team: string;
}

export function DashboardHeader({ name, avatarUrl, role, team }: DashboardHeaderProps) {
  const [avatarFailed, setAvatarFailed] = useState(false);

  const initial = name?.[0]?.toUpperCase() ?? "?";

  return (
    <div className="flex items-center gap-4 p-6">
      {avatarUrl && !avatarFailed ? (
        <img
          src={avatarUrl}
          alt={name}
          className="w-16 h-16 rounded-full object-cover border-2 shrink-0"
          style={{ borderColor: "var(--team-accent)" }}
          onError={() => setAvatarFailed(true)}
        />
      ) : (
        <div
          className={cn(
            "w-16 h-16 rounded-full bg-primary text-primary-foreground flex items-center justify-center font-semibold text-xl shrink-0 border-2",
          )}
          style={{ borderColor: "var(--team-accent)" }}
        >
          {initial}
        </div>
      )}

      <div className="flex flex-col gap-1 min-w-0">
        <span
          className="font-bold text-xl leading-tight truncate"
          style={{ fontFamily: "var(--font-display, Impact, sans-serif)" }}
        >
          {name}
        </span>
        <span className="text-sm opacity-80 truncate">{role}</span>
      </div>

      {team && (
        <div className="ml-auto flex items-center gap-1.5 shrink-0">
          <span className="text-lg" aria-hidden="true">
            {teamFlag(team)}
          </span>
          <span className="rounded-full px-3 py-1 text-xs font-medium border border-current opacity-80 capitalize">
            {team}
          </span>
        </div>
      )}
    </div>
  );
}

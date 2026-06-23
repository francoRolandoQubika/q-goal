import { cn } from "@q-goal/ui/lib/utils";
import { useState } from "react";

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
          className="w-10 h-10 rounded-full object-cover"
          onError={() => setAvatarFailed(true)}
        />
      ) : (
        <div
          className={cn(
            "w-10 h-10 rounded-full bg-primary text-primary-foreground flex items-center justify-center font-semibold",
          )}
        >
          {initial}
        </div>
      )}
      <div className="flex flex-col gap-1">
        <span className="font-semibold text-base leading-none">{name}</span>
        <span className="text-sm opacity-80">{role}</span>
      </div>
      <span className="ml-auto rounded-full px-3 py-1 text-xs font-medium border border-current opacity-80">
        {team}
      </span>
    </div>
  );
}

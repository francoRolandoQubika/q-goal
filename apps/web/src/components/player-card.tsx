import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@q-goal/ui/components/card";
import { cn } from "@q-goal/ui/lib/utils";
import { env } from "@q-goal/env/web";
import { useState } from "react";
import type { Assignment } from "../lib/dashboard-types";

interface PlayerCardProps {
  assignment: Assignment;
  accentColor: string;
}

export function PlayerCard({ assignment, accentColor }: PlayerCardProps) {
  const [imgFailed, setImgFailed] = useState(false);

  const initial = assignment.player.name?.[0]?.toUpperCase() ?? "?";

  return (
    <Card className="border-2" style={{ borderColor: accentColor }}>
      {imgFailed ? (
        <div
          className={cn(
            "w-full aspect-square flex items-center justify-center text-4xl font-bold bg-muted text-muted-foreground",
          )}
        >
          {initial}
        </div>
      ) : (
        <img
          src={`${env.VITE_GENAI_URL}/faces/${assignment.player.id}`}
          alt={assignment.player.name}
          className="w-full object-cover aspect-square"
          onError={() => setImgFailed(true)}
        />
      )}
      <CardHeader>
        <CardTitle>{assignment.title}</CardTitle>
        <CardDescription>
          {assignment.player.name} — {assignment.player.team}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <p className="text-sm">{assignment.description}</p>
      </CardContent>
    </Card>
  );
}

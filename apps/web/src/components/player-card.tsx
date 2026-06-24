import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@q-goal/ui/components/card";
import { useEffect, useState } from "react";
import type { Assignment } from "../lib/dashboard-types";
import { getFaceDataUrl } from "../lib/face-cutout";

interface PlayerCardProps {
  assignment: Assignment;
}

export function PlayerCard({ assignment }: PlayerCardProps) {
  const [imgFailed, setImgFailed] = useState(false);
  const [cutoutUrl, setCutoutUrl] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    getFaceDataUrl(assignment.player.id).then((url) => {
      if (cancelled) return;
      if (url !== null) {
        setCutoutUrl(url);
      } else {
        setImgFailed(true);
      }
    });

    return () => {
      cancelled = true;
    };
  }, [assignment.player.id]);

  const initial = assignment.player.name?.[0]?.toUpperCase() ?? "?";

  return (
    <Card
      className="border-2 relative overflow-hidden foil-sticker"
      style={{ borderColor: "var(--team-accent)" }}
    >
      <style>{`
        @media (prefers-reduced-motion: no-preference) {
          .foil-sticker::after {
            content: "";
            position: absolute;
            inset: 0;
            background: linear-gradient(
              120deg,
              transparent 30%,
              oklch(0.75 0.14 88 / 0.25) 50%,
              transparent 70%
            );
            background-size: 200% 100%;
            animation: foil-shimmer 3s linear infinite;
            pointer-events: none;
          }
        }
        @keyframes foil-shimmer {
          0% { background-position: 200% 0; }
          100% { background-position: -200% 0; }
        }
      `}</style>

      {cutoutUrl !== null ? (
        <img
          src={cutoutUrl}
          alt={assignment.player.name}
          className="w-full object-cover aspect-square"
        />
      ) : imgFailed ? (
        <div className="w-full aspect-square flex items-center justify-center text-4xl font-bold bg-muted text-muted-foreground">
          {initial}
        </div>
      ) : (
        <div className="w-full aspect-square flex items-center justify-center bg-muted/50" />
      )}

      <CardHeader>
        <CardTitle style={{ fontFamily: "var(--font-display, Impact, sans-serif)" }}>
          {assignment.title}
        </CardTitle>
        <CardDescription>
          {assignment.player.name} — {assignment.player.team}
        </CardDescription>
      </CardHeader>

      <CardContent className="space-y-2">
        <p className="text-sm">{assignment.description}</p>

        {(assignment.player.position ||
          assignment.player.club ||
          assignment.player.caps !== undefined ||
          assignment.player.goals !== undefined) && (
          <dl
            className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs mt-2 border-t pt-2"
            style={{ borderColor: "var(--team-accent)" }}
          >
            {assignment.player.position && (
              <>
                <dt className="text-muted-foreground font-medium">Position</dt>
                <dd className="font-mono font-semibold">{assignment.player.position}</dd>
              </>
            )}
            {assignment.player.club && (
              <>
                <dt className="text-muted-foreground font-medium">Club</dt>
                <dd className="font-mono font-semibold">{assignment.player.club}</dd>
              </>
            )}
            {assignment.player.caps !== undefined && (
              <>
                <dt className="text-muted-foreground font-medium">Caps</dt>
                <dd className="font-mono font-semibold">{assignment.player.caps}</dd>
              </>
            )}
            {assignment.player.goals !== undefined && (
              <>
                <dt className="text-muted-foreground font-medium">Goals</dt>
                <dd className="font-mono font-semibold">{assignment.player.goals}</dd>
              </>
            )}
          </dl>
        )}
      </CardContent>
    </Card>
  );
}

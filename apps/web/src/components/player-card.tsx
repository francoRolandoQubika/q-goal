import { useEffect, useState } from "react";
import type { Assignment } from "../lib/dashboard-types";
import { getFaceDataUrl } from "../lib/face-cutout";

interface PlayerCardProps {
  assignment: Assignment;
}

interface StatProps {
  label: string;
  value: string | number;
}

function Stat({ label, value }: StatProps) {
  return (
    <div className="flex flex-col gap-0.5">
      <dt className="text-[0.62rem] uppercase tracking-wider text-muted-foreground">{label}</dt>
      <dd className="font-mono text-sm font-semibold tabular-nums">{value}</dd>
    </div>
  );
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

  const { player, title, description } = assignment;
  const initial = player.name?.[0]?.toUpperCase() ?? "?";

  const stats: StatProps[] = [];
  if (player.club) stats.push({ label: "Club", value: player.club });
  if (player.caps !== undefined) stats.push({ label: "Caps", value: player.caps });
  if (player.goals !== undefined) stats.push({ label: "Goals", value: player.goals });

  return (
    // Foil frame: a thin gold-metallic gradient border wrapping the sticker.
    <article
      className="rounded-[1.1rem] p-[2px] shadow-xl shadow-black/30"
      style={{
        backgroundImage:
          "linear-gradient(150deg, oklch(0.88 0.11 92), oklch(0.62 0.1 82) 38%, oklch(0.95 0.05 95) 60%, oklch(0.6 0.1 82))",
      }}
    >
      <div className="overflow-hidden rounded-[1rem] bg-card">
        {/* Photo panel — team-color glow with the cut-out player rising out of it. */}
        <div
          className="foil-shimmer relative aspect-[4/5] overflow-hidden"
          style={{
            backgroundColor: "color-mix(in oklch, var(--team-accent) 32%, var(--card))",
            backgroundImage:
              "radial-gradient(72% 58% at 50% 30%, color-mix(in oklch, var(--team-accent) 78%, white 6%), transparent 72%), linear-gradient(to bottom, transparent 55%, color-mix(in oklch, var(--team-accent) 18%, black 35%))",
          }}
        >
          {cutoutUrl !== null ? (
            <img
              src={cutoutUrl}
              alt={player.name}
              className="absolute bottom-0 left-1/2 w-[112%] max-w-none -translate-x-1/2 object-contain object-bottom drop-shadow-[0_8px_14px_rgba(0,0,0,0.45)]"
            />
          ) : imgFailed ? (
            <div className="flex h-full w-full items-center justify-center font-display text-8xl text-white/85">
              {initial}
            </div>
          ) : (
            <div className="h-full w-full animate-pulse bg-black/10" />
          )}

          {/* Position tag — the little corner chip from a real sticker. */}
          {player.position && (
            <span
              className="absolute left-3 top-3 inline-flex h-9 min-w-9 items-center justify-center rounded-full border border-white/30 px-2 font-mono text-xs font-bold text-white shadow-md backdrop-blur-sm"
              style={{ backgroundColor: "color-mix(in oklch, var(--team-accent) 70%, black 12%)" }}
            >
              {player.position}
            </span>
          )}

          {/* Country band, top-right. */}
          <span className="absolute right-3 top-3 rounded-full bg-black/35 px-2.5 py-1 text-[0.65rem] font-medium uppercase tracking-wide text-white/90 backdrop-blur-sm">
            {player.team}
          </span>
        </div>

        {/* Name plate + scouting report. */}
        <div className="space-y-3 p-4">
          <div>
            <p
              className="font-display text-base uppercase tracking-[0.2em]"
              style={{ color: "var(--team-accent)" }}
            >
              {title}
            </p>
            <h3 className="font-display text-3xl leading-none">{player.name}</h3>
          </div>

          <p className="text-sm leading-relaxed text-muted-foreground">{description}</p>

          {stats.length > 0 && (
            <dl className="grid grid-cols-[1.6fr_1fr_1fr] gap-3 border-t border-foreground/10 pt-3">
              {stats.map((s) => (
                <Stat key={s.label} label={s.label} value={s.value} />
              ))}
            </dl>
          )}
        </div>
      </div>
    </article>
  );
}

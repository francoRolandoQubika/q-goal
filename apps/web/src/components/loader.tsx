import { Loader2 } from "lucide-react";

interface LoaderProps {
  message?: string;
}

export default function Loader({ message = "Scouting…" }: LoaderProps) {
  return (
    <div className="flex h-full flex-col items-center justify-center gap-3 pt-8">
      <Loader2 className="motion-safe:animate-spin" aria-hidden="true" />
      <p className="text-sm text-muted-foreground">{message}</p>
    </div>
  );
}

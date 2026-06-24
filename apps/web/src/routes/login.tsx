import { createFileRoute } from "@tanstack/react-router";
import { toast } from "sonner";

import { authClient } from "@/lib/auth-client";

export const Route = createFileRoute("/login")({
  component: RouteComponent,
});

function GoogleLogo() {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      aria-hidden="true"
      className="w-5 h-5 shrink-0"
    >
      <path
        d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
        fill="#4285F4"
      />
      <path
        d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
        fill="#34A853"
      />
      <path
        d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l3.66-2.84z"
        fill="#FBBC05"
      />
      <path
        d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
        fill="#EA4335"
      />
    </svg>
  );
}

function RouteComponent() {
  function handleGoogleSignIn() {
    authClient.signIn.social(
      { provider: "google", callbackURL: `${window.location.origin}/` },
      {
        onError: (error) => {
          toast.error(error.error.message || error.error.statusText);
        },
      },
    );
  }

  return (
    <div className="flex min-h-screen flex-col items-center justify-center px-6 py-12">
      <div className="w-full max-w-sm space-y-9 text-center">
        <div className="space-y-5">
          {/* Foil-stamped emblem — the sticker-pack hook. */}
          <div
            className="foil-shimmer relative mx-auto flex h-20 w-20 items-center justify-center overflow-hidden rounded-full p-[2px] shadow-lg shadow-black/30"
            style={{
              backgroundImage:
                "linear-gradient(150deg, oklch(0.88 0.11 92), oklch(0.62 0.1 82) 40%, oklch(0.95 0.05 95) 62%, oklch(0.6 0.1 82))",
            }}
          >
            <span className="flex h-full w-full items-center justify-center rounded-full bg-card text-4xl">
              ⚽
            </span>
          </div>

          <div className="space-y-2">
            <p className="text-xs font-medium uppercase tracking-[0.3em] text-muted-foreground">
              World Cup 2026
            </p>
            <h1 className="font-display text-6xl">Your Figurita Awaits</h1>
            <p className="text-base text-muted-foreground">
              Answer a few questions and we'll match you to your World Cup player.
            </p>
          </div>
        </div>

        <button
          type="button"
          onClick={handleGoogleSignIn}
          className="inline-flex w-full items-center justify-center gap-3 rounded-lg border border-neutral-300 bg-white px-6 py-3.5 text-sm font-semibold text-neutral-800 shadow-sm transition-colors hover:bg-neutral-50 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#4285F4]"
        >
          <GoogleLogo />
          Continue with Google
        </button>

        <p className="text-xs text-muted-foreground">Six questions. One scouting report.</p>
      </div>
    </div>
  );
}

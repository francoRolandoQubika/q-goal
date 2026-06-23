import { Button } from "@q-goal/ui/components/button";
import { createFileRoute } from "@tanstack/react-router";
import { toast } from "sonner";

import { authClient } from "@/lib/auth-client";

export const Route = createFileRoute("/login")({
  component: RouteComponent,
});

function RouteComponent() {
  return (
    <div className="mx-auto w-full mt-10 max-w-md p-6 text-center">
      <h1 className="mb-6 text-3xl font-bold">Welcome</h1>
      <Button
        type="button"
        variant="outline"
        className="w-full"
        onClick={() =>
          authClient.signIn.social(
            { provider: "google", callbackURL: `${window.location.origin}/quiz` },
            {
              onError: (error) => {
                toast.error(error.error.message || error.error.statusText);
              },
            },
          )
        }
      >
        Sign in with Google
      </Button>
    </div>
  );
}

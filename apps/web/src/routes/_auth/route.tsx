import { Outlet, createFileRoute, redirect } from "@tanstack/react-router";

import { authClient } from "@/lib/auth-client";
import AppBar from "@/components/app-bar";

export const Route = createFileRoute("/_auth")({
  component: AuthLayout,
  beforeLoad: async () => {
    const session = await authClient.getSession();
    if (!session.data) {
      throw redirect({
        to: "/login",
      });
    }
    return { session };
  },
});

function AuthLayout() {
  return (
    <div className="grid grid-rows-[auto_1fr] h-svh overflow-hidden">
      <AppBar />
      <div className="overflow-y-auto">
        <Outlet />
      </div>
    </div>
  );
}

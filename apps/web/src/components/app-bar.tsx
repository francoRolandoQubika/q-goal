import { ModeToggle } from "./mode-toggle";
import UserMenu from "./user-menu";

export default function AppBar() {
  return (
    <div className="flex items-center justify-between px-4 py-2 border-b bg-background dark:bg-background">
      <span className="font-display text-2xl tracking-wide">⚽ Q-Goal</span>
      <div className="flex items-center gap-2">
        <ModeToggle />
        <UserMenu />
      </div>
    </div>
  );
}

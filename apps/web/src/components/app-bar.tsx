import { ModeToggle } from "./mode-toggle";
import UserMenu from "./user-menu";

export default function AppBar() {
  return (
    <div className="flex items-center justify-between px-2 py-1 border-b">
      <span className="font-semibold">q-goal</span>
      <div className="flex items-center gap-2">
        <ModeToggle />
        <UserMenu />
      </div>
    </div>
  );
}

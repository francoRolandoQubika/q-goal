export interface Player {
  id: number;
  name: string;
  team: string;
  position?: string;
  dob?: string;
  club?: string;
  height_cm?: number;
  caps?: number;
  goals?: number;
}

export interface Assignment {
  title: string;
  player: Player;
  description: string;
}

export interface DashboardState {
  assignments: Assignment[];
  outro: string;
  role: string;
}

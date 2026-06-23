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

export interface QuizResult {
  id?: string;
  role: string;
  outro: string;
  assignments: Assignment[];
  createdAt?: string;
  updatedAt?: string;
}

export type DashboardState = QuizResult;

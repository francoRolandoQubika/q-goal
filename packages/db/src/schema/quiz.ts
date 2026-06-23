import { relations } from "drizzle-orm";
import { index, jsonb, pgTable, text, timestamp } from "drizzle-orm/pg-core";

import { user } from "./auth";

export interface QuizPlayer {
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

export interface QuizAssignment {
  title: string;
  description: string;
  player: QuizPlayer;
}

export const quizResult = pgTable(
  "quiz_result",
  {
    id: text("id").primaryKey(),
    userId: text("user_id")
      .notNull()
      .unique()
      .references(() => user.id, { onDelete: "cascade" }),
    role: text("role").notNull(),
    outro: text("outro").notNull(),
    assignments: jsonb("assignments").$type<QuizAssignment[]>().notNull(),
    createdAt: timestamp("created_at").defaultNow().notNull(),
    updatedAt: timestamp("updated_at")
      .defaultNow()
      .$onUpdate(() => new Date())
      .notNull(),
  },
  (table) => [index("quiz_result_userId_idx").on(table.userId)],
);

export const quizResultRelations = relations(quizResult, ({ one }) => ({
  user: one(user, {
    fields: [quizResult.userId],
    references: [user.id],
  }),
}));

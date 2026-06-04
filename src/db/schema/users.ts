import { pgTable, text, timestamp, integer } from 'drizzle-orm/pg-core';

export const users = pgTable('users', {
  id: text('id').primaryKey(), // Discord User ID
  username: text('username').notNull(),
  globalScore: integer('global_score').default(0),
  mvpBadges: integer('mvp_badges').default(0),
  createdAt: timestamp('created_at').defaultNow(),
  updatedAt: timestamp('updated_at').defaultNow(),
});

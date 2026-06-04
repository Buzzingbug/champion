import { pgTable, text, timestamp, integer } from 'drizzle-orm/pg-core';
import { guilds } from './guilds';
import { users } from './users';

export const teams = pgTable('teams', {
  id: text('id').primaryKey(), // e.g. GuildID-Color
  guildId: text('guild_id').notNull().references(() => guilds.id),
  name: text('name').notNull(),
  color: text('color').notNull(), // 'red', 'blue', etc.
  score: integer('score').default(0),
  captainId: text('captain_id').references(() => users.id),
  createdAt: timestamp('created_at').defaultNow(),
});

export const guildMembers = pgTable('guild_members', {
  id: text('id').primaryKey(), // GuildID-UserID
  guildId: text('guild_id').notNull().references(() => guilds.id),
  userId: text('user_id').notNull().references(() => users.id),
  teamId: text('team_id').references(() => teams.id),
  score: integer('score').default(0),
  streak: integer('streak').default(0),
  joinedAt: timestamp('joined_at').defaultNow(),
});

import { pgTable, text, timestamp, integer, boolean } from 'drizzle-orm/pg-core';
import { guilds } from './guilds';

export const games = pgTable('games', {
  id: text('id').primaryKey(),
  guildId: text('guild_id').notNull().references(() => guilds.id),
  gameType: text('game_type').notNull(),
  status: text('status').notNull().default('active'), // 'active', 'completed', 'delayed'
  winnerTeamId: text('winner_team_id'),
  startedAt: timestamp('started_at').defaultNow(),
  endedAt: timestamp('ended_at'),
});

export const votes = pgTable('votes', {
  id: text('id').primaryKey(), // GameID-UserID
  gameId: text('game_id').notNull().references(() => games.id),
  userId: text('user_id').notNull(),
  vote: text('vote').notNull(),
  isCorrect: boolean('is_correct'),
  pointsAwarded: integer('points_awarded').default(0),
  votedAt: timestamp('voted_at').defaultNow(),
});

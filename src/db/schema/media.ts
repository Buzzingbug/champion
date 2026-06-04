import { pgTable, text, timestamp, integer, boolean } from 'drizzle-orm/pg-core';
import { guilds } from './guilds';

export const media = pgTable('media', {
  id: text('id').primaryKey(),
  guildId: text('guild_id').notNull().references(() => guilds.id),
  url: text('url').notNull(),
  type: text('type').notNull(), // 'image', 'video'
  source: text('source').notNull(), // 'manual', 'starter'
  submittedBy: text('submitted_by'),
  contentRating: text('content_rating').default('sfw'),
  phash: text('phash'),
  timesUsed: integer('times_used').default(0),
  isActive: boolean('is_active').default(true),
  lastUsed: timestamp('last_used'),
  createdAt: timestamp('created_at').defaultNow(),
});

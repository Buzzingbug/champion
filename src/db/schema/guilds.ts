import { pgTable, text, timestamp, boolean } from 'drizzle-orm/pg-core';

export const guilds = pgTable('guilds', {
  id: text('id').primaryKey(), // Discord Guild ID
  name: text('name').notNull(),
  activeTheme: text('active_theme').default('gaming'),
  announcementChannelId: text('announcement_channel_id'),
  logChannelId: text('log_channel_id'),
  isActive: boolean('is_active').default(true),
  createdAt: timestamp('created_at').defaultNow(),
  updatedAt: timestamp('updated_at').defaultNow(),
});

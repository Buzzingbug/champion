import { db } from '../db';
import { media } from '../db/schema';
import crypto from 'crypto';

export class StarterPackService {
  static async seedGuild(guildId: string) {
    console.log(`Seeding Starter Pack for guild ${guildId}...`);
    // Seed default media items for immediate playability
    for (let i=0; i<5; i++) {
      try {
        await db.insert(media).values({
          id: crypto.randomUUID(),
          guildId: guildId,
          url: `https://example.com/starter-${i}.jpg`,
          type: 'image',
          source: 'starter',
          submittedBy: 'system'
        }).onConflictDoNothing();
      } catch (err) {
        console.error('Failed to insert starter pack media', err);
      }
    }
  }
}

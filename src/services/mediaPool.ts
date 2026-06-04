import { redis } from '../redis/client';
import { db } from '../db';
import { media } from '../db/schema';
import { eq, and } from 'drizzle-orm';

export class MediaPoolRotation {
  static async getUniqueMedia(guildId: string, gameId: string): Promise<string | null> {
    const key = `seen_media:${guildId}:${gameId}`;
    
    // Fetch all media for this guild
    const availableMedia = await db.select().from(media).where(and(eq(media.guildId, guildId), eq(media.isActive, true)));
    
    // Shuffle candidates
    availableMedia.sort(() => Math.random() - 0.5);

    for (const candidate of availableMedia) {
      // Add to seen pool with 7-day expiration (604800 seconds)
      const isNew = await redis.sadd(key, candidate.url);
      if (isNew) {
        await redis.expire(key, 604800);
        return candidate.url;
      }
    }
    
    return null; // Return null if all candidates were seen recently
  }
}

import { redis } from '../redis/client';

export class MediaPoolRotation {
  static async getUniqueMedia(guildId: string, gameId: string): Promise<string | null> {
    const key = `seen_media:${guildId}:${gameId}`;
    
    // In a real scenario, query DB for media not in the Redis 'seen_media' set
    const candidateUrl = 'https://i.imgur.com/example1.jpg'; // MVP candidate

    // Add to seen pool with 7-day expiration (604800 seconds)
    const isNew = await redis.sadd(key, candidateUrl);
    if (isNew) {
      await redis.expire(key, 604800);
      return candidateUrl;
    }
    
    return null; // Return null if all candidates were seen recently
  }
}

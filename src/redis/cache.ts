import { redis } from './client';

export class CacheManager {
  static async setVote(roundId: string, userId: string, voteData: string): Promise<boolean> {
    const key = `vote:${roundId}:${userId}`;
    // NX = only set if it does not exist (prevents double vote)
    // EX = expire in 3600 seconds (1 hour to clean up after round)
    const result = await redis.set(key, voteData, 'EX', 3600, 'NX');
    return result === 'OK';
  }

  static async getVotes(roundId: string): Promise<string[]> {
    const keys = await redis.keys(`vote:${roundId}:*`);
    if (keys.length === 0) return [];
    return await redis.mget(keys) as string[];
  }

  static async getVoters(roundId: string): Promise<string[]> {
    const keys = await redis.keys(`vote:${roundId}:*`);
    return keys.map((k: string) => k.split(':').pop()!);
  }
}

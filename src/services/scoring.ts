import { db } from '../db';
import { guildMembers } from '../db/schema';
import { eq, sql } from 'drizzle-orm';

export class ScoringService {
  static async awardPoints(guildId: string, userId: string, points: number) {
    const memberId = `${guildId}-${userId}`;
    console.log(`Awarding ${points} points to ${memberId} in guild ${guildId}`);
    
    // Perform an upsert in Drizzle ORM
    await db.insert(guildMembers).values({
      id: memberId,
      guildId,
      userId,
      score: points,
    }).onConflictDoUpdate({
      target: guildMembers.id,
      set: { score: sql`${guildMembers.score} + ${points}` }
    });
  }

  static async getLeaderboard(guildId: string) {
    // MVP fallback, queries DB directly. Phase 2 will cache to Redis.
    return [];
  }
}

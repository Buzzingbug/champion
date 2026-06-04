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

  static async tallyRound(roundId: string, guildId: string) {
    const { CacheManager } = await import('../redis/cache');
    const { PowerManager } = await import('./powerManager');
    const { teams } = await import('../db/schema');
    const { and, inArray } = await import('drizzle-orm');
    
    const voters = await CacheManager.getVoters(roundId);
    if (voters.length === 0) return;

    const members = await db.select().from(guildMembers)
      .where(and(eq(guildMembers.guildId, guildId), inArray(guildMembers.userId, voters)));

    const baseScores = new Map<string, number>();
    for (const m of members) {
      if (m.teamId) {
        baseScores.set(m.teamId, (baseScores.get(m.teamId) || 0) + 10);
      }
    }

    const { finalScores, streakResets } = await PowerManager.processRoundScores(guildId, baseScores);

    for (const [teamId, score] of finalScores.entries()) {
      await db.update(teams).set({ score: sql`${teams.score} + ${score}` }).where(eq(teams.id, teamId));
      await db.update(guildMembers)
        .set({ score: sql`${guildMembers.score} + ${score}`, streak: sql`${guildMembers.streak} + 1` })
        .where(eq(guildMembers.teamId, teamId));
    }

    if (streakResets.length > 0) {
      await db.update(guildMembers).set({ streak: 0 }).where(inArray(guildMembers.teamId, streakResets));
    }
  }
}

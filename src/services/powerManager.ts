import { db } from '../db';
import { teams } from '../db/schema';
import { eq, inArray } from 'drizzle-orm';

export interface TeamResult {
  id: string;
  color: string;
  baseScore: number;
  finalScore: number;
  activePower: string | null;
  activePowerTarget: string | null;
  streakReset: boolean;
}

export class PowerManager {
  static async processRoundScores(guildId: string, baseScores: Map<string, number>): Promise<{ finalScores: Map<string, number>, streakResets: string[] }> {
    const teamIds = Array.from(baseScores.keys());
    if (teamIds.length === 0) return { finalScores: baseScores, streakResets: [] };

    const dbTeams = await db.select().from(teams).where(inArray(teams.id, teamIds));
    const results: Record<string, TeamResult> = {};

    for (const t of dbTeams) {
      results[t.id] = {
        id: t.id,
        color: t.color,
        baseScore: baseScores.get(t.id) || 0,
        finalScore: baseScores.get(t.id) || 0,
        activePower: t.activePower,
        activePowerTarget: t.activePowerTarget,
        streakReset: false,
      };
    }

    // Step 1: Pre-process Shields and Bankers
    const shieldedTeams = new Set<string>();
    const nextRoundPowers = new Map<string, string>(); // teamId -> next power to store

    for (const t of Object.values(results)) {
      if (t.activePower === 'shield') {
        shieldedTeams.add(t.id);
      } else if (t.activePower === 'interest_banking_active') {
        t.finalScore *= 3; // Apply the banked interest from last round
      }
    }

    // Step 2: Apply Powers
    for (const t of Object.values(results)) {
      const power = t.activePower;
      const target = t.activePowerTarget ? results[t.activePowerTarget] : null;

      if (!power) continue;

      if (power === 'steal' && target) {
        if (!shieldedTeams.has(target.id)) {
          const stolenAmount = Math.floor(target.baseScore * 0.5);
          target.finalScore -= stolenAmount;
          t.finalScore += stolenAmount;
        }
      } else if (power === 'safe_bet') {
        t.finalScore += 50;
      } else if (power === 'sabotage' && target) {
        if (!shieldedTeams.has(target.id)) {
          target.finalScore = Math.floor(target.finalScore * 0.5);
        }
      } else if (power === 'mystic_veil') {
        t.finalScore += 100;
      } else if (power === 'poach' && target) {
        if (!shieldedTeams.has(target.id)) {
          const stolenAmount = Math.floor(target.baseScore * 0.25);
          target.finalScore -= stolenAmount;
          t.finalScore += stolenAmount;
          target.streakReset = true; // Flag to reset streak
        }
      } else if (power === 'interest_banking') {
        // Zero out this round, save for next round
        t.finalScore = 0;
        nextRoundPowers.set(t.id, 'interest_banking_active');
      }
    }

    // Evaluate Double Down
    let highestBaseScore = -1;
    for (const t of Object.values(results)) {
      if (t.baseScore > highestBaseScore) highestBaseScore = t.baseScore;
    }

    for (const t of Object.values(results)) {
      if (t.activePower === 'double_down') {
        if (t.baseScore >= highestBaseScore && highestBaseScore > 0) {
          t.finalScore += t.baseScore; // Double the base score
        } else {
          t.finalScore = 0; // Lost
        }
      }
    }

    // Step 3: Clear active powers in DB, and set nextRoundPowers if any
    for (const t of dbTeams) {
      const nextPower = nextRoundPowers.get(t.id) || null;
      await db.update(teams).set({ activePower: nextPower, activePowerTarget: null }).where(eq(teams.id, t.id));
    }

    const finalScores = new Map<string, number>();
    const streakResets: string[] = [];
    for (const [id, res] of Object.entries(results)) {
      finalScores.set(id, Math.max(0, res.finalScore)); // No negative scores
      if (res.streakReset) {
        streakResets.push(id);
      }
    }

    return { finalScores, streakResets };
  }
}

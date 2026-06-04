import { GameDefinition } from './base.game';

export const GAME_REGISTRY: Record<string, GameDefinition> = {
  'left-or-right': {
    id: 'left-or-right',
    category: 'taste',
    name: 'Left or Right',
    duration: 30,
    mediaCount: 2,
    voteType: 'binary',
    voteEmojis: ['⬅️', '➡️'],
    hasCorrectAnswer: false,
    scoring: { majorityMatch: 1, streakBonus: 2, streakThreshold: 3, participation: 0 },
    teamBonuses: { red: { type: 'minority', points: 2 }, blue: { type: 'majority', points: 2 } }
  },
  'smash-or-pass': {
    id: 'smash-or-pass',
    category: 'taste',
    name: 'Smash or Pass',
    duration: 20,
    mediaCount: 1,
    voteType: 'binary',
    voteEmojis: ['💥', '🚫'],
    hasCorrectAnswer: false,
    scoring: { participation: 1, minorityBonus: 2, smashStreakRole: 'Smash Royalty', smashStreakThreshold: 5 },
    teamBonuses: { red: { type: 'minority', points: 2 }, blue: { type: 'none' } }
  },
  'pick-one-of-four': {
    id: 'pick-one-of-four',
    category: 'taste',
    name: 'Pick One from Four',
    duration: 25,
    mediaCount: 4,
    voteType: 'multi',
    voteEmojis: ['1️⃣', '2️⃣', '3️⃣', '4️⃣'],
    hasCorrectAnswer: false,
    scoring: { winnerPick: 3, participation: 1 },
    specialRole: 'Tastemaker'
  },
  'kiss-kick-carry': {
    id: 'kiss-kick-carry',
    category: 'taste',
    name: 'Kiss, Kick, Carry',
    duration: 24,
    mediaCount: 3,
    voteType: 'sequential',
    voteEmojis: ['😘', '👟', '🎒'],
    hasCorrectAnswer: false,
    scoring: { perVote: 1, carryMatch: 5 },
    specialRole: 'Chaos Agent'
  },
  'rate-the-fit': {
    id: 'rate-the-fit',
    category: 'taste',
    name: 'Rate the Fit',
    duration: 30,
    mediaCount: 1,
    voteType: 'scale',
    voteEmojis: ['1️⃣','2️⃣','3️⃣','4️⃣','5️⃣','6️⃣','7️⃣','8️⃣','9️⃣','🔟'],
    hasCorrectAnswer: false,
    scoring: { participation: 1, accuracyBonus: 3, submitterHigh: 10, submitterMid: 5, submitterLow: 2 }
  }
};

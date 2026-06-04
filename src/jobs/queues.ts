import { Queue } from 'bullmq';
import { redis } from '../redis/client';

export const gameQueue = new Queue('game-events', { connection: redis as any });
export const systemQueue = new Queue('system-events', { connection: redis as any });

export async function scheduleRoundEnd(gameId: string, delayMs: number) {
  await gameQueue.add('round.end', { gameId }, { delay: delayMs, jobId: `end-${gameId}` });
}

export async function schedulePredictionReveal(gameId: string, delayMs: number) {
  await gameQueue.add('delayed.reveal', { gameId }, { delay: delayMs, jobId: `reveal-${gameId}` });
}

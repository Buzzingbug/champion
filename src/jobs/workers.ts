import { Worker, Job } from 'bullmq';
import { redis } from '../redis/client';
import { db } from '../db';
import { games, guildMembers } from '../db/schema';
import { eq } from 'drizzle-orm';
// We would import the actual game instances/registry here eventually
// import { GAME_REGISTRY } from '../games/registry';

export const gameWorker = new Worker('game-events', async (job: Job) => {
  switch (job.name) {
    case 'round.end':
      console.log(`Ending round for game ${job.data.gameId}`);
      await db.update(games).set({ status: 'completed', endedAt: new Date() }).where(eq(games.id, job.data.gameId));
      break;
    case 'delayed.reveal':
      console.log(`Revealing delayed prediction for game ${job.data.gameId}`);
      await db.update(games).set({ status: 'completed', endedAt: new Date() }).where(eq(games.id, job.data.gameId));
      break;
    default:
      console.warn(`Unknown job: ${job.name}`);
  }
}, { connection: redis as any });

export const systemWorker = new Worker('system-events', async (job: Job) => {
  if (job.name === 'leaderboard.reset') {
    console.log('Resetting weekly leaderboards...');
    await db.update(guildMembers).set({ score: 0 }); // MVP reset logic
  }
}, { connection: redis as any });

gameWorker.on('completed', job => console.log(`Job ${job.id} has completed!`));
gameWorker.on('failed', (job, err) => console.error(`Job ${job?.id} has failed with ${err.message}`));

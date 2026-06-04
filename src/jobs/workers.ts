import { Worker, Job } from 'bullmq';
import { redis } from '../redis/client';
import { db } from '../db';
import { games, guildMembers } from '../db/schema';
import { eq } from 'drizzle-orm';
import { SeasonManager } from '../services/seasonManager';
// We would import the actual game instances/registry here eventually
// import { GAME_REGISTRY } from '../games/registry';

export const gameWorker = new Worker('game-events', async (job: Job) => {
  switch (job.name) {
    case 'round.end':
      console.log(`Ending round for game ${job.data.gameId}`);
      await db.update(games).set({ status: 'completed', endedAt: new Date() }).where(eq(games.id, job.data.gameId));
      
      const gameRecord = await db.select().from(games).where(eq(games.id, job.data.gameId));
      if (gameRecord.length > 0) {
         const { ScoringService } = await import('../services/scoring');
         await ScoringService.tallyRound(job.data.gameId, gameRecord[0].guildId);
      }
      break;
    case 'delayed.reveal':
      console.log(`Revealing delayed prediction for game ${job.data.gameId}`);
      await db.update(games).set({ status: 'completed', endedAt: new Date() }).where(eq(games.id, job.data.gameId));
      
      const delayRecord = await db.select().from(games).where(eq(games.id, job.data.gameId));
      if (delayRecord.length > 0) {
         const { ScoringService } = await import('../services/scoring');
         await ScoringService.tallyRound(job.data.gameId, delayRecord[0].guildId);
      }
      break;
    default:
      console.warn(`Unknown job: ${job.name}`);
  }
}, { connection: redis as any });

export const systemWorker = new Worker('system-events', async (job: Job) => {
  if (job.name === 'leaderboard.reset') {
    console.log('Resetting weekly leaderboards...');
    await db.update(guildMembers).set({ score: 0 }); // MVP reset logic
  } else if (job.name === 'season.rollup') {
    await SeasonManager.executeRollup();
  } else if (job.name === 'reddit.scrape') {
    const { RedditScraper } = await import('../services/redditScraper');
    await RedditScraper.fetchTrending();
  }
}, { connection: redis as any });

gameWorker.on('completed', job => console.log(`Job ${job.id} has completed!`));
gameWorker.on('failed', (job, err) => console.error(`Job ${job?.id} has failed with ${err.message}`));

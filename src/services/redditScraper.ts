import { systemQueue } from '../jobs/queues';
import { db } from '../db';
import { media } from '../db/schema';
import crypto from 'crypto';

export class RedditScraper {
  static async fetchTrending() {
    console.log('Fetching trending from Reddit (Tier 3 Fetching)...');
    // MVP implementation: would use snoowrap or raw fetch here
    const dummyPosts = [
      { url: 'https://i.imgur.com/example1.jpg', tag: 'fashion' },
      { url: 'https://i.imgur.com/example2.jpg', tag: 'gaming' }
    ];

    for (const post of dummyPosts) {
      const phash = crypto.createHash('md5').update(post.url).digest('hex');
      try {
        await db.insert(media).values({
          id: crypto.randomUUID(),
          guildId: 'global',
          url: post.url,
          type: 'image',
          source: 'reddit',
          submittedBy: 'system'
        }).onConflictDoNothing();
      } catch (err) {
        console.error('Failed to insert media', err);
      }
    }
  }

  static async scheduleDailyScrape() {
    await systemQueue.add('reddit.scrape', {}, { repeat: { pattern: '0 0 * * *' } });
  }
}

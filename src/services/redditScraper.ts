import { systemQueue } from '../jobs/queues';
import { db } from '../db';
import { media } from '../db/schema';
import crypto from 'crypto';

export class RedditScraper {
  static async fetchTrending() {
    console.log('Fetching trending from Reddit (Tier 3 Fetching)...');
    
    const subreddits = ['streetwear', 'gaming', 'anime', 'memes', 'sports'];
    
    for (const sub of subreddits) {
      try {
        const response = await fetch(`https://www.reddit.com/r/${sub}/hot.json?limit=10`);
        const json = await response.json();
        const posts = json.data.children;

        for (const post of posts) {
          const data = post.data;
          // Filter for images only
          if (data.url && (data.url.endsWith('.jpg') || data.url.endsWith('.png'))) {
            await db.insert(media).values({
              id: crypto.randomUUID(),
              guildId: 'global',
              url: data.url,
              type: 'image',
              source: `reddit:r/${sub}`,
              submittedBy: 'system'
            }).onConflictDoNothing();
          }
        }
      } catch (err) {
        console.error(`Failed to fetch from r/${sub}`, err);
      }
    }
  }

  static async scheduleDailyScrape() {
    await systemQueue.add('reddit.scrape', {}, { repeat: { pattern: '0 0 * * *' } });
  }
}

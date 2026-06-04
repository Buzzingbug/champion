import { BaseGame } from '../base.game';
import { TextChannel, Message, EmbedBuilder } from 'discord.js';

export class KissKickCarryGame extends BaseGame {
  async startRound(channel: TextChannel): Promise<Message> {
    const { db } = await import('../../db');
    const { media } = await import('../../db/schema');
    const { sql } = await import('drizzle-orm');

    // Fetch 3 random pieces of media
    const randomMedia = await db.select().from(media).orderBy(sql`RANDOM()`).limit(3);
    const mediaUrls = randomMedia.map(m => m.url).join('\n');

    const embed = new EmbedBuilder()
      .setTitle(`Round: ${this.def.name}`)
      .setDescription(`React with 😘 for Kiss, 👟 for Kick, 🎒 for Carry!\n\n${mediaUrls || '*(No media found in DB, run scraper!)*'}`)
      .setColor('#FF0000');
    
    const message = await channel.send({ embeds: [embed] });
    for (const emoji of this.def.voteEmojis) {
      await message.react(emoji);
    }
    return message;
  }

  async endRound(messageId: string): Promise<void> {
    const { CacheManager } = await import('../../redis/cache');
    const { db } = await import('../../db');
    const { games } = await import('../../db/schema');
    const { eq } = await import('drizzle-orm');
    
    // For MVP/benchmark, we'll just tally votes based on participants
    const voters = await CacheManager.getVoters(messageId);
    console.log(`Game ${messageId} ended. ${voters.length} players participated.`);
    
    // Actual DB updates handled by scoring worker, but this is game-specific validation
    await db.update(games).set({ status: 'completed' }).where(eq(games.id, messageId));
  }
}

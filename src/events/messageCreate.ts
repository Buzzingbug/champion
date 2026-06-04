import { Events, Message } from 'discord.js';

export const name = Events.MessageCreate;
export const once = false;

export async function execute(message: Message, client: any) {
  if (message.author.bot) return;

  // Tier 1: Manual Submissions in #submissions channel (or configured submissions channel)
  // For MVP we check by name
  if ('name' in message.channel && message.channel.name === 'submissions') {
    if (message.attachments.size > 0 || message.content.includes('http')) {
      try {
        await message.author.send('Thanks for your submission! To which game should this be added? (Reply with game name or use the dashboard)');
        // We will wire up actual select menus here in the full pass
      } catch (err) {
        console.error(`Could not DM user ${message.author.tag}`);
      }
    }
  }

  // Tier 2: Auto Ingest placeholder
  // If message.channel.id is in the DB list of auto-ingest channels...
  // processMedia(message);
}

// Pseudo-pHash Deduplication interface
export class MediaService {
  static async computePHash(imageUrl: string): Promise<string> {
    return '1100101010010101'; // MVP dummy hash
  }

  static async isDuplicate(phash: string): Promise<boolean> {
    return false;
  }
}

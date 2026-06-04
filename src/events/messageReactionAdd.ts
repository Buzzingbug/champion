import { Events, MessageReaction, User } from 'discord.js';
import { CacheManager } from '../redis/cache';

export const name = Events.MessageReactionAdd;
export const once = false;

export async function execute(reaction: MessageReaction, user: User, client: any) {
  if (user.bot) return;
  if (reaction.partial) {
    try {
      await reaction.fetch();
    } catch (error) {
      console.error('Something went wrong when fetching the message:', error);
      return;
    }
  }

  const messageId = reaction.message.id;
  const roundId = messageId;
  const voteOption = reaction.emoji.name;

  const success = await CacheManager.setVote(roundId, user.id, voteOption || 'unknown');
  if (!success) {
    await reaction.users.remove(user.id);
  } else {
    console.log(`Vote registered for user ${user.id} in round ${roundId}: ${voteOption}`);
  }
}

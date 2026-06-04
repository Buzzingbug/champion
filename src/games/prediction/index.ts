import { BaseGame } from '../base.game';
import { TextChannel, Message, EmbedBuilder } from 'discord.js';
import { schedulePredictionReveal } from '../../jobs/queues';

function buildPredictionGame(name: string, description: string) {
  return class extends BaseGame {
    async startRound(channel: TextChannel): Promise<Message> {
      const embed = new EmbedBuilder()
        .setTitle(`Prediction: ${this.def.name}`)
        .setDescription(`${description}\n*Results will be revealed after ${this.def.delayDuration}*`)
        .setColor('#800080');
      const message = await channel.send({ embeds: [embed] });
      for (const emoji of this.def.voteEmojis) { await message.react(emoji); }
      
      // Schedule reveal job
      if (this.def.isDelayed) {
        // Parse delayDuration string to MS for BullMQ (e.g., '7d' -> 7 * 24 * 60 * 60 * 1000)
        let delayMs = 24 * 60 * 60 * 1000; // default 1 day
        if (this.def.delayDuration === '7d') delayMs = 7 * 24 * 60 * 60 * 1000;
        if (this.def.delayDuration === '30d') delayMs = 30 * 24 * 60 * 60 * 1000;
        
        await schedulePredictionReveal(message.id, delayMs);
      }

      return message;
    }
    async endRound(messageId: string): Promise<void> {}
  };
}

export const NextToBlowUpGame = buildPredictionGame('Next to Blow Up', 'Who is the next to blow up?');
export const WouldTheyCollabGame = buildPredictionGame('Would They Collab?', 'Will these two creators ever collab?');
export const PriceIsRightGame = buildPredictionGame('Price Is Right', 'Guess the price of this item!');
export const ViralOrFlopGame = buildPredictionGame('Viral or Flop?', 'Will this video go viral or flop?');
export const FutureFlexGame = buildPredictionGame('Future Flex', 'What will be their biggest flex in 30 days?');

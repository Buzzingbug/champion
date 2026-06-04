import { BaseGame } from '../base.game';
import { TextChannel, Message, EmbedBuilder } from 'discord.js';
import { schedulePredictionReveal } from '../../jobs/queues';

abstract class BasePredictionGame extends BaseGame {
  protected abstract get description(): string;
  
  async startRound(channel: TextChannel): Promise<Message> {
    const embed = new EmbedBuilder()
      .setTitle(`Prediction: ${this.def.name}`)
      .setDescription(`${this.description}\n*Results will be revealed after ${this.def.delayDuration}*`)
      .setColor('#800080');
    
    const message = await channel.send({ embeds: [embed] });
    for (const emoji of this.def.voteEmojis) { await message.react(emoji); }
    
    if (this.def.isDelayed) {
      let delayMs = 24 * 60 * 60 * 1000;
      if (this.def.delayDuration === '7d') delayMs = 7 * 24 * 60 * 60 * 1000;
      if (this.def.delayDuration === '30d') delayMs = 30 * 24 * 60 * 60 * 1000;
      await schedulePredictionReveal(message.id, delayMs);
    }
    return message;
  }
  async endRound(messageId: string): Promise<void> {}
}

export class NextToBlowUpGame extends BasePredictionGame {
  protected get description() { return 'Who is the next to blow up? (7 days)'; }
}

export class WouldTheyCollabGame extends BasePredictionGame {
  protected get description() { return 'Will these two creators ever collab?'; }
}

export class PriceIsRightGame extends BasePredictionGame {
  protected get description() { return 'Guess the price of this item!'; }
}

export class ViralOrFlopGame extends BasePredictionGame {
  protected get description() { return 'Will this video go viral or flop? (24 hours)'; }
}

export class FutureFlexGame extends BasePredictionGame {
  protected get description() { return 'What will be their biggest flex in 30 days?'; }
}

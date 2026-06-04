import { BaseGame } from '../base.game';
import { TextChannel, Message, EmbedBuilder } from 'discord.js';

export class PickOneOfFourGame extends BaseGame {
  async startRound(channel: TextChannel): Promise<Message> {
    const embed = new EmbedBuilder()
      .setTitle(`Round: ${this.def.name}`)
      .setDescription('React with 1️⃣, 2️⃣, 3️⃣, or 4️⃣!')
      .setColor('#FF0000');
    
    const message = await channel.send({ embeds: [embed] });
    for (const emoji of this.def.voteEmojis) {
      await message.react(emoji);
    }
    return message;
  }

  async endRound(messageId: string): Promise<void> {
    // End logic
  }
}

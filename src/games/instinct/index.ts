import { BaseGame } from '../base.game';
import { TextChannel, Message, EmbedBuilder } from 'discord.js';

function buildGame(name: string, description: string, color: string = '#FFA500') {
  return class extends BaseGame {
    async startRound(channel: TextChannel): Promise<Message> {
      const embed = new EmbedBuilder()
        .setTitle(`Round: ${this.def.name}`)
        .setDescription(description)
        .setColor(color as any);
      const message = await channel.send({ embeds: [embed] });
      for (const emoji of this.def.voteEmojis) { await message.react(emoji); }
      return message;
    }
    async endRound(messageId: string): Promise<void> {}
  };
}

export const WhoBlewUpFirstGame = buildGame('Who Blew Up First?', 'Which of these creators blew up first?');
export const GuessTheirNicheGame = buildGame('Guess Their Niche', 'What is their main content niche?');
export const EngagementGuessGame = buildGame('Engagement Guess', 'Guess their like-to-view ratio!');
export const CaptionOrChaosGame = buildGame('Caption or Chaos', 'Is this caption real or AI generated?');
export const PhotoshopOrRealGame = buildGame('Photoshop or Real?', 'Is this image real or photoshopped?');
export const BlindRatingGame = buildGame('Blind Rating', 'Rate without knowing who it is!');
export const WhosTheImposterGame = buildGame('Who is the Imposter?', 'Spot the imposter among these creators!');

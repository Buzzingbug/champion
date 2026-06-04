import { SlashCommandBuilder, ChatInputCommandInteraction } from 'discord.js';
import { db } from '../db';
import { media } from '../db/schema';
import crypto from 'crypto';

export const data = new SlashCommandBuilder()
  .setName('submit')
  .setDescription('Submit media to a game')
  .addStringOption(option => 
    option.setName('game')
      .setDescription('The game to submit to')
      .setRequired(true)
      .addChoices(
        { name: 'Left or Right', value: 'left-or-right' },
        { name: 'Smash or Pass', value: 'smash-or-pass' }
      ))
  .addStringOption(option =>
    option.setName('url')
      .setDescription('URL of the media')
      .setRequired(true)
  );

export async function execute(interaction: ChatInputCommandInteraction) {
  const game = interaction.options.getString('game', true);
  const url = interaction.options.getString('url', true);
  const guildId = interaction.guildId;
  
  if (!guildId) return;

  const id = crypto.randomUUID();
  await db.insert(media).values({
    id,
    guildId,
    url,
    type: url.match(/\.(mp4|webm|mov)$/i) ? 'video' : 'image',
    source: 'manual',
    submittedBy: interaction.user.id,
  });

  await interaction.reply(`Media submitted to ${game}! You earned +5 points!`);
}

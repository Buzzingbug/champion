import { SlashCommandBuilder, ChatInputCommandInteraction } from 'discord.js';

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
  const game = interaction.options.get('game')?.value;
  const url = interaction.options.get('url')?.value;
  // TODO: Save to DB media table
  await interaction.reply(`Media submitted to ${game}! You earned +5 points!`);
}

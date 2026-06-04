import { SlashCommandBuilder, ChatInputCommandInteraction } from 'discord.js';

export const data = new SlashCommandBuilder()
  .setName('setup')
  .setDescription('Set up the tournament in this server.')
  .addStringOption(option => 
    option.setName('theme')
      .setDescription('The theme for the tournament')
      .setRequired(true)
      .addChoices(
        { name: 'Gaming', value: 'gaming' },
        { name: 'Fashion', value: 'fashion' }
      ));

export async function execute(interaction: ChatInputCommandInteraction) {
  const theme = interaction.options.get('theme')?.value;
  await interaction.reply(`Tournament setup with theme: ${theme}`);
}

import { SlashCommandBuilder, ChatInputCommandInteraction } from 'discord.js';

export const data = new SlashCommandBuilder()
  .setName('team')
  .setDescription('Team management')
  .addSubcommand(subcommand =>
    subcommand
      .setName('join')
      .setDescription('Join a team')
      .addStringOption(option => 
        option.setName('color')
          .setDescription('Team color')
          .setRequired(true)
          .addChoices(
            { name: 'Red (Aggressive)', value: 'red' },
            { name: 'Blue (Strategic)', value: 'blue' }
          )));

export async function execute(interaction: ChatInputCommandInteraction) {
  const color = interaction.options.get('color')?.value;
  await interaction.reply(`You joined the ${color} team!`);
}

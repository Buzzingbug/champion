import { SlashCommandBuilder, ChatInputCommandInteraction } from 'discord.js';

export const data = new SlashCommandBuilder()
  .setName('ingest')
  .setDescription('Auto-ingest media from a channel')
  .addSubcommand(subcommand =>
    subcommand.setName('add')
      .setDescription('Add a channel to auto-ingest')
      .addChannelOption(option => 
        option.setName('channel')
          .setDescription('The channel to monitor')
          .setRequired(true)
      )
  );

export async function execute(interaction: ChatInputCommandInteraction) {
  const channel = interaction.options.getChannel('channel');
  // Save to DB (guilds table -> ingest channels)
  await interaction.reply({ content: `Now auto-ingesting media from ${channel}!`, ephemeral: false });
}

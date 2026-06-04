import { SlashCommandBuilder, ChatInputCommandInteraction } from 'discord.js';

export const data = new SlashCommandBuilder()
  .setName('captain')
  .setDescription('Captain dashboard and powers')
  .addSubcommand(subcommand =>
    subcommand.setName('stats').setDescription('View your team stats')
  )
  .addSubcommand(subcommand =>
    subcommand.setName('power')
      .setDescription('Activate a team power')
      .addStringOption(option => 
        option.setName('power_type')
          .setDescription('Which power to use')
          .setRequired(true)
          .addChoices(
            { name: 'Steal (Red)', value: 'steal' },
            { name: 'Double Down (Red)', value: 'double_down' },
            { name: 'Shield (Blue)', value: 'shield' },
            { name: 'Safe Bet (Blue)', value: 'safe_bet' }
          )
      )
  );

export async function execute(interaction: ChatInputCommandInteraction) {
  const subcommand = interaction.options.getSubcommand();
  if (subcommand === 'stats') {
    await interaction.reply({ content: 'Captain Stats: [WIP]', ephemeral: true });
  } else if (subcommand === 'power') {
    const power = interaction.options.get('power_type')?.value;
    // MVP logic for power activation
    await interaction.reply({ content: `Activated power: ${power}! This will affect the next round.`, ephemeral: false });
  }
}

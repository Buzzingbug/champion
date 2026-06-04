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
            { name: 'Blue (Strategic)', value: 'blue' },
            { name: 'Green (Balanced)', value: 'green' },
            { name: 'Gold (Greed)', value: 'gold' },
            { name: 'Purple (Chaos)', value: 'purple' },
            { name: 'Black (Elite)', value: 'black' }
          )));

export async function execute(interaction: ChatInputCommandInteraction) {
  if (!interaction.guildId || !interaction.user.id) return;

  const { db } = await import('../db');
  const { teams, guildMembers, guilds } = await import('../db/schema');
  const { eq, and } = await import('drizzle-orm');
  
  const color = interaction.options.getString('color', true);

  // Ensure guild exists
  await db.insert(guilds).values({
    id: interaction.guildId,
    name: interaction.guild?.name || 'Unknown',
  }).onConflictDoNothing();

  // Ensure team exists for this guild
  const teamId = `${interaction.guildId}-${color}`;
  await db.insert(teams).values({
    id: teamId,
    guildId: interaction.guildId,
    name: color.charAt(0).toUpperCase() + color.slice(1),
    color: color,
  }).onConflictDoNothing();

  // Add user to team
  await db.insert(guildMembers).values({
    id: `${interaction.guildId}-${interaction.user.id}`,
    guildId: interaction.guildId,
    userId: interaction.user.id,
    teamId: teamId
  }).onConflictDoUpdate({
    target: guildMembers.id,
    set: { teamId: teamId }
  });

  const { Logger } = await import('../services/logger');
  await Logger.sendLog(interaction.client, interaction.guildId, 'Team Joined', `<@${interaction.user.id}> joined the **${color}** team!`, '#00FF00');

  await interaction.reply(`You joined the ${color} team!`);
}

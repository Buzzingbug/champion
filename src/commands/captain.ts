import { SlashCommandBuilder, ChatInputCommandInteraction } from 'discord.js';
import { db } from '../db';
import { teams } from '../db/schema';
import { eq, and } from 'drizzle-orm';

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
            { name: 'Safe Bet (Blue)', value: 'safe_bet' },
            { name: 'Sabotage (Green)', value: 'sabotage' },
            { name: 'Interest Banking (Gold)', value: 'interest_banking' },
            { name: 'Mystic Veil (Purple)', value: 'mystic_veil' },
            { name: 'Poach (Black)', value: 'poach' }
          )
      )
      .addStringOption(option =>
        option.setName('target_team')
          .setDescription('Target team color (for Steal, Sabotage, Poach)')
          .setRequired(false)
      )
  );

export async function execute(interaction: ChatInputCommandInteraction) {
  const subcommand = interaction.options.getSubcommand();
  
  // Find team where user is captain
  const userTeams = await db.select().from(teams)
    .where(and(eq(teams.guildId, interaction.guildId!), eq(teams.captainId, interaction.user.id)));
  
  if (userTeams.length === 0) {
    return interaction.reply({ content: 'You are not the captain of any team in this server.', ephemeral: true });
  }

  const team = userTeams[0];

  if (subcommand === 'stats') {
    await interaction.reply({ 
      content: `**Team ${team.name} Stats**\nScore: ${team.score}\nPower Charges: ${team.powerCharges || 0}\nActive Power: ${team.activePower || 'None'}`, 
      ephemeral: true 
    });
  } else if (subcommand === 'power') {
    const power = interaction.options.getString('power_type', true);
    const targetColor = interaction.options.getString('target_team');

    if ((team.powerCharges || 0) <= 0) {
      return interaction.reply({ content: 'Your team has no power charges left this season!', ephemeral: true });
    }

    if (team.activePower) {
      return interaction.reply({ content: 'You already have an active power queued for the next round.', ephemeral: true });
    }

    const targetedPowers = ['steal', 'sabotage', 'poach'];
    let targetId = null;

    if (targetedPowers.includes(power)) {
      if (!targetColor) {
        return interaction.reply({ content: `The power ${power} requires a target_team (e.g. "blue").`, ephemeral: true });
      }
      const targetTeamData = await db.select().from(teams)
        .where(and(eq(teams.guildId, interaction.guildId!), eq(teams.color, targetColor.toLowerCase())));
      
      if (targetTeamData.length === 0) {
        return interaction.reply({ content: `Could not find a team with color ${targetColor} in this server.`, ephemeral: true });
      }
      targetId = targetTeamData[0].id;
    }

    // Update DB
    await db.update(teams)
      .set({ 
        activePower: power, 
        activePowerTarget: targetId,
        powerCharges: (team.powerCharges || 3) - 1 
      })
      .where(eq(teams.id, team.id));

    const { Logger } = await import('../services/logger');
    await Logger.sendLog(interaction.client, interaction.guildId!, 'Power Activated', `Team **${team.color}** captain activated **${power}**!`, '#FFA500');

    await interaction.reply({ content: `🔥 You activated **${power}**! It will be applied at the end of the next round.`, ephemeral: false });
  }
}

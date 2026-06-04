import { SlashCommandBuilder, ChatInputCommandInteraction, EmbedBuilder } from 'discord.js';
import { db } from '../db';
import { guildMembers, teams } from '../db/schema';
import { eq, desc } from 'drizzle-orm';

export const data = new SlashCommandBuilder()
  .setName('leaderboard')
  .setDescription('View the top players and team standings');

export async function execute(interaction: ChatInputCommandInteraction) {
  const guildId = interaction.guildId;
  if (!guildId) return;

  // Fetch top 5 players in the server
  const topPlayers = await db.select()
    .from(guildMembers)
    .where(eq(guildMembers.guildId, guildId))
    .orderBy(desc(guildMembers.score))
    .limit(5);

  // Fetch team scores
  const teamScores = await db.select()
    .from(teams)
    .where(eq(teams.guildId, guildId))
    .orderBy(desc(teams.score));

  let playerText = topPlayers.map((u, i) => `${i + 1}. <@${u.userId}> - ${u.score} pts`).join('\n') || 'No players yet.';
  let teamText = teamScores.map((t, i) => `${i + 1}. **${t.name}** - ${t.score} pts`).join('\n') || 'No teams yet.';

  const embed = new EmbedBuilder()
    .setTitle('🏆 Tournament Leaderboard')
    .setColor('#FFD700')
    .addFields(
      { name: 'Top Players', value: playerText, inline: true },
      { name: 'Team Standings', value: teamText, inline: true }
    )
    .setFooter({ text: 'Updated in real-time' })
    .setTimestamp();

  await interaction.reply({ embeds: [embed] });
}

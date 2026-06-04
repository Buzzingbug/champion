import { db } from '../db';
import { guilds, teams, guildMembers, users } from '../db/schema';
import { eq, desc } from 'drizzle-orm';
import { client } from '../bot';
import { EmbedBuilder, TextChannel } from 'discord.js';

export class SeasonManager {
  static async executeRollup() {
    console.log('Starting Season Rollup...');
    const allGuilds = await db.select().from(guilds);

    for (const g of allGuilds) {
      // Find top team
      const guildTeams = await db.select().from(teams)
        .where(eq(teams.guildId, g.id))
        .orderBy(desc(teams.score));
      
      const winningTeam = guildTeams.length > 0 ? guildTeams[0] : null;

      // Find top user
      const topUsers = await db.select().from(guildMembers)
        .where(eq(guildMembers.guildId, g.id))
        .orderBy(desc(guildMembers.score))
        .limit(1);
      
      const mvp = topUsers.length > 0 ? topUsers[0] : null;

      if (mvp) {
        const userRec = await db.select().from(users).where(eq(users.id, mvp.userId));
        if (userRec.length > 0) {
          await db.update(users).set({ mvpBadges: (userRec[0].mvpBadges || 0) + 1 }).where(eq(users.id, mvp.userId));
        }
      }

      // Send recap if channel configured
      if (g.announcementChannelId) {
        try {
          const channel = await client.channels.fetch(g.announcementChannelId) as TextChannel;
          if (channel && channel.isTextBased()) {
            const embed = new EmbedBuilder()
              .setTitle('🏆 Season Complete! 🏆')
              .setDescription('The season has ended and scores have been tallied!')
              .setColor('#FFD700')
              .addFields(
                { name: 'Winning Team', value: winningTeam ? `${winningTeam.name} (${winningTeam.score} pts)` : 'None', inline: true },
                { name: 'Season MVP', value: mvp ? `<@${mvp.userId}> (${mvp.score} pts)` : 'None', inline: true }
              )
              .setFooter({ text: 'Scores and Power Charges have been reset for the new season.' });
            
            await channel.send({ embeds: [embed] });
          }
        } catch (e) {
          console.error(`Failed to send recap to guild ${g.id}:`, e);
        }
      }

      // Reset Guild Members
      await db.update(guildMembers).set({ score: 0, streak: 0 }).where(eq(guildMembers.guildId, g.id));
      
      // Reset Teams
      await db.update(teams).set({ 
        score: 0, 
        powerCharges: 3,
        activePower: null,
        activePowerTarget: null 
      }).where(eq(teams.guildId, g.id));
    }
    
    console.log('Season Rollup Complete.');
  }
}

import { TextChannel, EmbedBuilder, Client } from 'discord.js';
import { db } from '../db';
import { guilds } from '../db/schema';
import { eq } from 'drizzle-orm';

export class Logger {
  static async sendLog(client: Client, guildId: string, title: string, description: string, color: string = '#808080') {
    try {
      const guildData = await db.select().from(guilds).where(eq(guilds.id, guildId));
      if (!guildData || guildData.length === 0) return;
      
      const logChannelId = guildData[0].logChannelId;
      if (!logChannelId) return;

      const discordGuild = await client.guilds.fetch(guildId).catch(() => null);
      if (!discordGuild) return;

      const channel = await discordGuild.channels.fetch(logChannelId).catch(() => null);
      if (!channel || !(channel instanceof TextChannel)) return;

      const embed = new EmbedBuilder()
        .setTitle(`📝 ${title}`)
        .setDescription(description)
        .setColor(color as any)
        .setTimestamp();

      await channel.send({ embeds: [embed] });
    } catch (err) {
      console.error(`Failed to send log to guild ${guildId}:`, err);
    }
  }
}

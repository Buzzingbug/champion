import { SlashCommandBuilder, ChatInputCommandInteraction, ChannelType } from 'discord.js';
import { db } from '../db';
import { guilds } from '../db/schema';
import { eq } from 'drizzle-orm';

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
      ))
  .addChannelOption(option =>
    option.setName('announcement_channel')
      .setDescription('Channel to post season rollups and announcements')
      .addChannelTypes(ChannelType.GuildText)
      .setRequired(false)
  );

export async function execute(interaction: ChatInputCommandInteraction) {
  const theme = interaction.options.getString('theme', true);
  const channel = interaction.options.getChannel('announcement_channel');
  
  const guildId = interaction.guildId;
  if (!guildId) return;

  await db.insert(guilds).values({
    id: guildId,
    name: interaction.guild?.name || 'Unknown Guild',
    activeTheme: theme,
    announcementChannelId: channel?.id || null,
  }).onConflictDoUpdate({
    target: guilds.id,
    set: {
      activeTheme: theme,
      announcementChannelId: channel?.id || null,
      updatedAt: new Date()
    }
  });

  await interaction.reply(`Tournament setup complete! Theme: ${theme}${channel ? `, Announcements in <#${channel.id}>` : ''}`);
}

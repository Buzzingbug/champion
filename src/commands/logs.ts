import { SlashCommandBuilder, ChatInputCommandInteraction, PermissionsBitField, ChannelType } from 'discord.js';
import { db } from '../db';
import { guilds } from '../db/schema';
import { eq } from 'drizzle-orm';

export const data = new SlashCommandBuilder()
  .setName('logs')
  .setDescription('Master logs configuration')
  .setDefaultMemberPermissions(PermissionsBitField.Flags.Administrator)
  .addSubcommand(subcommand =>
    subcommand
      .setName('set')
      .setDescription('Set the master logs channel')
      .addChannelOption(option => 
        option.setName('channel')
          .setDescription('The channel to receive all bot logs')
          .addChannelTypes(ChannelType.GuildText)
          .setRequired(true)
      )
  )
  .addSubcommand(subcommand =>
    subcommand
      .setName('clear')
      .setDescription('Disable master logs')
  );

export async function execute(interaction: ChatInputCommandInteraction) {
  if (!interaction.guildId) return;

  const subcommand = interaction.options.getSubcommand();

  if (subcommand === 'set') {
    const channel = interaction.options.getChannel('channel', true);
    
    await db.insert(guilds).values({
      id: interaction.guildId,
      name: interaction.guild?.name || 'Unknown Guild',
      logChannelId: channel.id
    }).onConflictDoUpdate({
      target: guilds.id,
      set: { logChannelId: channel.id, updatedAt: new Date() }
    });

    await interaction.reply({ content: `✅ Master logs channel has been set to <#${channel.id}>.`, ephemeral: true });
  } else if (subcommand === 'clear') {
    await db.update(guilds)
      .set({ logChannelId: null, updatedAt: new Date() })
      .where(eq(guilds.id, interaction.guildId));

    await interaction.reply({ content: `✅ Master logs have been disabled.`, ephemeral: true });
  }
}

import { Client, REST, Routes } from 'discord.js';
import * as pingCommand from './ping';
import * as setupCommand from './setup';
import * as teamCommand from './team';

import * as submitCommand from './submit';
import * as captainCommand from './captain';
import * as ingestCommand from './ingest';
import * as leaderboardCommand from './leaderboard';

const commandsList = [pingCommand, setupCommand, teamCommand, submitCommand, captainCommand, ingestCommand, leaderboardCommand];

export async function loadCommands(client: Client) {
  const commandsData = [];

  for (const cmd of commandsList) {
    client.commands.set(cmd.data.name, cmd);
    commandsData.push(cmd.data.toJSON());
  }

  if (!process.env.DISCORD_TOKEN || !process.env.DISCORD_CLIENT_ID) {
    console.warn('Skipping slash command registration due to missing env vars');
    return;
  }

  const rest = new REST({ version: '10' }).setToken(process.env.DISCORD_TOKEN);

  try {
    console.log('Started refreshing application (/) commands.');
    await rest.put(
      Routes.applicationCommands(process.env.DISCORD_CLIENT_ID),
      { body: commandsData },
    );
    console.log('Successfully reloaded application (/) commands.');
  } catch (error) {
    console.error(error);
  }
}

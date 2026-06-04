import { Client, GatewayIntentBits, Partials, Collection } from 'discord.js';
import * as dotenv from 'dotenv';
import { loadEvents } from './events';
import { loadCommands } from './commands';
import './jobs'; // Initialize BullMQ workers
import { startServer } from './server';

dotenv.config();

const client = new Client({
  intents: [
    GatewayIntentBits.Guilds,
    GatewayIntentBits.GuildMessages,
    GatewayIntentBits.GuildMessageReactions,
  ],
  partials: [Partials.Message, Partials.Channel, Partials.Reaction],
});

client.commands = new Collection();

async function start() {
  await loadCommands(client);
  await loadEvents(client);
  
  if (process.env.DISCORD_TOKEN) {
    // Start Express Server for Dashboard/Healthchecks
    startServer();

    // Login to Discord
    client.login(process.env.DISCORD_TOKEN);
  } else {
    console.warn('DISCORD_TOKEN is missing. Bot cannot log in.');
  }
}

start().catch(console.error);

declare module 'discord.js' {
  export interface Client {
    commands: Collection<string, any>;
  }
}

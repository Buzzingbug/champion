import { Client } from 'discord.js';
import * as readyEvent from './ready';
import * as interactionCreateEvent from './interactionCreate';
import * as messageReactionAddEvent from './messageReactionAdd';

const eventsList = [readyEvent, interactionCreateEvent, messageReactionAddEvent];

export async function loadEvents(client: Client) {
  for (const event of eventsList) {
    if (event.once) {
      client.once(event.name, (...args: any[]) => (event.execute as any)(...args, client));
    } else {
      client.on(event.name, (...args: any[]) => (event.execute as any)(...args, client));
    }
  }
}

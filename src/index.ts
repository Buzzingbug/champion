import { ShardingManager } from 'discord.js';
import * as dotenv from 'dotenv';
import path from 'path';

dotenv.config();

const manager = new ShardingManager(path.join(__dirname, 'bot.js'), {
  token: process.env.DISCORD_TOKEN,
  totalShards: 'auto', // Automatically scales shards as bot grows past 2k servers
});

manager.on('shardCreate', shard => console.log(`[ShardingManager] Launched shard ${shard.id}`));

manager.spawn();

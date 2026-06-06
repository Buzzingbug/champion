import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import asyncpg
import redis.asyncio as redis

# Load local .env if it exists
load_dotenv()

class GamesBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix='!', intents=intents)
        
        self.db_pool = None
        self.redis_pool = None

    async def create_db_tables(self):
        if not self.db_pool:
            return
        async with self.db_pool.acquire() as connection:
            await connection.execute("""
                CREATE TABLE IF NOT EXISTS server_configs (
                    guild_id BIGINT PRIMARY KEY,
                    smash_channel_id BIGINT,
                    smash_role_id BIGINT,
                    smash_reward_amount INT,
                    smash_custom_message TEXT
                );
                
                CREATE TABLE IF NOT EXISTS smash_votes (
                    message_id BIGINT,
                    user_id BIGINT,
                    vote_choice VARCHAR(10),
                    PRIMARY KEY (message_id, user_id)
                );
                
                CREATE TABLE IF NOT EXISTS kfm_configs (
                    guild_id BIGINT PRIMARY KEY,
                    channel_id BIGINT,
                    role_id BIGINT,
                    reward_amount INT,
                    custom_message TEXT
                );
                
                CREATE TABLE IF NOT EXISTS kfm_votes (
                    message_id BIGINT,
                    user_id BIGINT,
                    vote_choice VARCHAR(10),
                    PRIMARY KEY (message_id, user_id)
                );
                
                CREATE TABLE IF NOT EXISTS rol_configs (
                    guild_id BIGINT PRIMARY KEY,
                    channel_id BIGINT,
                    role_id BIGINT,
                    reward_amount INT,
                    custom_message TEXT
                );
                
                CREATE TABLE IF NOT EXISTS rol_votes (
                    message_id BIGINT,
                    user_id BIGINT,
                    vote_choice VARCHAR(10),
                    PRIMARY KEY (message_id, user_id)
                );
                
                CREATE TABLE IF NOT EXISTS puzzle_configs (
                    guild_id BIGINT PRIMARY KEY,
                    channel_id BIGINT,
                    reward_amount INT
                );

                CREATE TABLE IF NOT EXISTS active_puzzles (
                    message_id BIGINT PRIMARY KEY,
                    guild_id BIGINT,
                    correct_order VARCHAR(20)
                );

                CREATE TABLE IF NOT EXISTS puzzle2_configs (
                    guild_id BIGINT PRIMARY KEY,
                    channel_id BIGINT,
                    reward_amount INT
                );

                CREATE TABLE IF NOT EXISTS puzzle2_active (
                    message_id BIGINT PRIMARY KEY,
                    guild_id BIGINT,
                    image_data BYTEA
                );

                CREATE TABLE IF NOT EXISTS economy (
                    guild_id BIGINT,
                    user_id BIGINT,
                    supercoins BIGINT DEFAULT 0,
                    PRIMARY KEY (guild_id, user_id)
                );
            """)
            print("Database tables verified/created.")

    async def setup_hook(self):
        # Database setup
        database_url = os.getenv("DATABASE_URL")
        if database_url:
            try:
                self.db_pool = await asyncpg.create_pool(database_url)
                print("Connected to PostgreSQL")
                await self.create_db_tables()
            except Exception as e:
                print(f"Failed to connect to PostgreSQL: {e}")
        else:
            print("Warning: DATABASE_URL not found in environment variables.")

        # Redis setup
        redis_url = os.getenv("REDIS_URL")
        if redis_url:
            try:
                self.redis_pool = redis.from_url(redis_url)
                # Ping redis to test connection
                await self.redis_pool.ping()
                print("Connected to Redis")
            except Exception as e:
                print(f"Failed to connect to Redis: {e}")
        else:
            print("Warning: REDIS_URL not found in environment variables.")

        # Load cogs
        if not os.path.exists('./cogs'):
            os.makedirs('./cogs')
            
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py') and not filename.startswith('__'):
                try:
                    await self.load_extension(f'cogs.{filename[:-3]}')
                    print(f"Loaded cog: {filename}")
                except Exception as e:
                    print(f"Failed to load cog {filename}: {e}")

        # Sync slash commands globally
        try:
            synced = await self.tree.sync()
            print(f"Synced {len(synced)} command(s)")
        except Exception as e:
            print(f"Failed to sync commands: {e}")

    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        print('------')

bot = GamesBot()

if __name__ == '__main__':
    token = os.getenv('DISCORD_TOKEN')
    if token:
        bot.run(token)
    else:
        print("Error: DISCORD_TOKEN not found in environment variables.")

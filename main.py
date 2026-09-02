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
        
        import time
        self.start_time = time.time()
        
        self.db_pool = None
        self.redis_pool = None

        # High-Performance Memory Cache
        self.cache = {
            'gates': {},  # channel_id -> dict
            'smash': {},  # guild_id -> channel_id
            'kfm': {},    # guild_id -> channel_id
            'lor': {},    # guild_id -> channel_id
            'categories': {}, # category_id -> dict
            'channel_rewards': {} # channel_id -> dict
        }

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
                    smash_custom_message TEXT,
                    post_cost INT DEFAULT 0
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
                    custom_message TEXT,
                    post_cost INT DEFAULT 0
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
                    custom_message TEXT,
                    post_cost INT DEFAULT 0
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

                CREATE TABLE IF NOT EXISTS coin_gates (
                    channel_id BIGINT PRIMARY KEY,
                    guild_id BIGINT,
                    bypass_role_id BIGINT,
                    required_amount INT,
                    custom_message TEXT
                );

                CREATE TABLE IF NOT EXISTS server_settings (
                    guild_id BIGINT PRIMARY KEY,
                    coin_name VARCHAR(50) DEFAULT 'Supercoins'
                );

                CREATE TABLE IF NOT EXISTS economy (
                    guild_id BIGINT,
                    user_id BIGINT,
                    supercoins BIGINT DEFAULT 0,
                    lifetime_channel BIGINT DEFAULT 0,
                    lifetime_category BIGINT DEFAULT 0,
                    lifetime_games BIGINT DEFAULT 0,
                    PRIMARY KEY (guild_id, user_id)
                );

                -- Migration for existing economy table
                DO $$ 
                BEGIN
                    BEGIN
                        ALTER TABLE economy ADD COLUMN lifetime_channel BIGINT DEFAULT 0;
                    EXCEPTION
                        WHEN duplicate_column THEN NULL;
                    END;
                    BEGIN
                        ALTER TABLE economy ADD COLUMN lifetime_category BIGINT DEFAULT 0;
                    EXCEPTION
                        WHEN duplicate_column THEN NULL;
                    END;
                    BEGIN
                        ALTER TABLE economy ADD COLUMN lifetime_games BIGINT DEFAULT 0;
                    EXCEPTION
                        WHEN duplicate_column THEN NULL;
                    END;
                END $$;

                CREATE TABLE IF NOT EXISTS category_configs (
                    category_id BIGINT PRIMARY KEY,
                    guild_id BIGINT,
                    reward_amount INT,
                    daily_limit INT,
                    custom_message TEXT
                );
                
                CREATE TABLE IF NOT EXISTS category_earnings (
                    user_id BIGINT,
                    category_id BIGINT,
                    date DATE,
                    earned_today INT,
                    PRIMARY KEY (user_id, category_id, date)
                );

                CREATE TABLE IF NOT EXISTS channel_reward_configs (
                    channel_id BIGINT PRIMARY KEY,
                    guild_id BIGINT,
                    reward_amount INT,
                    daily_limit INT,
                    custom_message TEXT
                );
                
                CREATE TABLE IF NOT EXISTS channel_earnings (
                    user_id BIGINT,
                    channel_id BIGINT,
                    date DATE,
                    earned_today INT,
                    PRIMARY KEY (user_id, channel_id, date)
                );

                CREATE TABLE IF NOT EXISTS weekly_dashboards (
                    guild_id BIGINT PRIMARY KEY,
                    channel_id BIGINT,
                    smash_msg TEXT,
                    smash_prize INT,
                    kfm_msg TEXT,
                    kfm_prize INT,
                    rol_msg TEXT,
                    rol_prize INT,
                    last_posted DATE
                );

                CREATE TABLE IF NOT EXISTS user_activity (
                    user_id BIGINT,
                    guild_id BIGINT,
                    messages_sent INT DEFAULT 0,
                    media_shared INT DEFAULT 0,
                    words_typed BIGINT DEFAULT 0,
                    night_owl_msgs INT DEFAULT 0,
                    voice_minutes INT DEFAULT 0,
                    current_streak INT DEFAULT 0,
                    longest_streak INT DEFAULT 0,
                    last_active_date DATE,
                    PRIMARY KEY (user_id, guild_id)
                );
            """)
            
            # Safely add the post_cost column to existing tables if they were created before this update
            try:
                await connection.execute("ALTER TABLE server_configs ADD COLUMN post_cost INT DEFAULT 0;")
            except asyncpg.exceptions.DuplicateColumnError:
                pass
                
            try:
                await connection.execute("ALTER TABLE kfm_configs ADD COLUMN post_cost INT DEFAULT 0;")
            except asyncpg.exceptions.DuplicateColumnError:
                pass
                
            try:
                await connection.execute("ALTER TABLE rol_configs ADD COLUMN post_cost INT DEFAULT 0;")
            except asyncpg.exceptions.DuplicateColumnError:
                pass
                
            try:
                await connection.execute("ALTER TABLE category_configs ADD COLUMN notify BOOLEAN DEFAULT TRUE;")
            except asyncpg.exceptions.DuplicateColumnError:
                pass
                
            try:
                await connection.execute("ALTER TABLE channel_reward_configs ADD COLUMN notify BOOLEAN DEFAULT TRUE;")
            except asyncpg.exceptions.DuplicateColumnError:
                pass
                
            try:
                await connection.execute("ALTER TABLE active_puzzles ADD COLUMN image_data BYTEA;")
            except asyncpg.exceptions.DuplicateColumnError:
                pass
                
            print("Database tables verified/created.")

    async def load_caches(self):
        if not self.db_pool:
            return
            
        async with self.db_pool.acquire() as connection:
            # Load Gates
            gates = await connection.fetch("SELECT * FROM coin_gates")
            self.cache['gates'] = {g['channel_id']: dict(g) for g in gates}
            
            # Load Smash
            smash = await connection.fetch("SELECT * FROM server_configs")
            self.cache['smash'] = {s['guild_id']: dict(s) for s in smash}
            
            # Load KFM
            kfm = await connection.fetch("SELECT * FROM kfm_configs")
            self.cache['kfm'] = {k['guild_id']: dict(k) for k in kfm}

            # Load LOR
            lor = await connection.fetch("SELECT * FROM rol_configs")
            self.cache['lor'] = {l['guild_id']: dict(l) for l in lor}

            # Load Categories
            categories = await connection.fetch("SELECT * FROM category_configs")
            self.cache['categories'] = {c['category_id']: dict(c) for c in categories}

            # Load Channel Rewards
            channel_rewards = await connection.fetch("SELECT * FROM channel_reward_configs")
            self.cache['channel_rewards'] = {c['channel_id']: dict(c) for c in channel_rewards}
            
        print(f"Caches loaded: {len(self.cache['gates'])} gates, {len(self.cache['categories'])} categories, {len(self.cache['channel_rewards'])} channel rewards.")

    async def setup_hook(self):
        # Database setup
        database_url = os.getenv("DATABASE_URL")
        if database_url:
            try:
                self.db_pool = await asyncpg.create_pool(database_url)
                print("Connected to PostgreSQL")
                await self.create_db_tables()
                await self.load_caches()
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

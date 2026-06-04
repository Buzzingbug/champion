# Graph Report - .  (2026-06-04)

## Corpus Check
- Corpus is ~4,365 words - fits in a single context window. You may not need a graph.

## Summary
- 208 nodes · 305 edges · 15 communities (11 shown, 4 thin omitted)
- Extraction: 98% EXTRACTED · 2% INFERRED · 0% AMBIGUOUS · INFERRED: 7 edges (avg confidence: 0.89)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_NPM Package Config|NPM Package Config]]
- [[_COMMUNITY_Core Events & Jobs|Core Events & Jobs]]
- [[_COMMUNITY_Database & Services|Database & Services]]
- [[_COMMUNITY_Taste Games System|Taste Games System]]
- [[_COMMUNITY_Discord Slash Commands|Discord Slash Commands]]
- [[_COMMUNITY_Theme Presets|Theme Presets]]
- [[_COMMUNITY_TypeScript Config|TypeScript Config]]
- [[_COMMUNITY_Instinct Games System|Instinct Games System]]
- [[_COMMUNITY_Railway Deployment|Railway Deployment]]
- [[_COMMUNITY_Prediction Games System|Prediction Games System]]
- [[_COMMUNITY_Media Message Processing|Media Message Processing]]
- [[_COMMUNITY_Graphify Workflows|Graphify Workflows]]
- [[_COMMUNITY_Sharding Manager|Sharding Manager]]
- [[_COMMUNITY_TS Config File|TS Config File]]

## God Nodes (most connected - your core abstractions)
1. `BaseGame` - 15 edges
2. `db` - 10 edges
3. `compilerOptions` - 10 edges
4. `guilds` - 8 edges
5. `guildMembers` - 8 edges
6. `ThemeDefinition` - 8 edges
7. `scripts` - 6 edges
8. `teams` - 6 edges
9. `systemQueue` - 6 edges
10. `redis` - 6 edges

## Surprising Connections (you probably didn't know these)
- `execute()` --semantically_similar_to--> `execute()`  [INFERRED] [semantically similar]
  src/commands/submit.ts → src/commands/ingest.ts
- `LeftOrRightGame` --semantically_similar_to--> `SmashOrPassGame`  [INFERRED] [semantically similar]
  src/games/taste/left-or-right.ts → src/games/taste/smash-or-pass.ts
- `systemWorker` --shares_data_with--> `systemQueue`  [INFERRED]
  src/jobs/workers.ts → src/jobs/queues.ts
- `StarterPackService` --semantically_similar_to--> `RedditScraper`  [INFERRED] [semantically similar]
  src/services/starterPack.ts → src/services/redditScraper.ts
- `start()` --calls--> `loadCommands()`  [EXTRACTED]
  src/bot.ts → src/commands/index.ts

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Discord Slash Commands** — commands_captain_data, commands_ingest_data, commands_leaderboard_data, commands_ping_data, commands_setup_data, commands_submit_data, commands_team_data [EXTRACTED 1.00]
- **Discord Command Executors** — commands_captain_execute, commands_ingest_execute, commands_leaderboard_execute, commands_ping_execute, commands_setup_execute, commands_submit_execute, commands_team_execute [EXTRACTED 1.00]
- **Drizzle Database Schema Tables** — schema_games_games, schema_games_votes, schema_guilds_guilds, schema_media_media, schema_teams_teams, schema_teams_guildmembers, schema_users_users [EXTRACTED 1.00]
- **Taste Game Implementations** — taste_kiss_kick_carry_kisskickcarrygame, taste_left_or_right_leftorrightgame, taste_pick_one_of_four_pickoneoffourgame, taste_rate_the_fit_ratethefitgame, taste_smash_or_pass_smashorpassgame, games_base_game_basegame [EXTRACTED 1.00]
- **BullMQ Job Queue System** — jobs_queues_gamequeue, jobs_queues_systemqueue, jobs_workers_gameworker, jobs_workers_systemworker, src_server_startserver [INFERRED 0.85]
- **Theme Presets Implementation** — presets_adult_adulttheme, presets_anime_animetheme, presets_fashion_fashiontheme, presets_gaming_gamingtheme, presets_music_musictheme, presets_sports_sportstheme, themes_base_theme_themedefinition [EXTRACTED 1.00]

## Communities (15 total, 4 thin omitted)

### Community 0 - "NPM Package Config"
Cohesion: 0.06
Nodes (32): author, dependencies, @bull-board/api, @bull-board/express, bullmq, discord.js, dotenv, drizzle-orm (+24 more)

### Community 1 - "Core Events & Jobs"
Cohesion: 0.11
Nodes (13): eventsList, loadEvents(), execute(), gameQueue, systemQueue, gameWorker, systemWorker, CacheManager (+5 more)

### Community 2 - "Database & Services"
Cohesion: 0.15
Nodes (14): data, execute(), db, pool, games, votes, guilds, media (+6 more)

### Community 3 - "Taste Games System"
Cohesion: 0.11
Nodes (8): BaseGame, GameDefinition, GAME_REGISTRY, KissKickCarryGame, LeftOrRightGame, PickOneOfFourGame, RateTheFitGame, SmashOrPassGame

### Community 4 - "Discord Slash Commands"
Cohesion: 0.10
Nodes (10): data, commandsList, loadCommands(), data, execute(), data, data, data (+2 more)

### Community 5 - "Theme Presets"
Cohesion: 0.28
Nodes (8): AdultTheme, AnimeTheme, fashionTheme, gamingTheme, MusicTheme, SportsTheme, ThemeDefinition, THEME_REGISTRY

### Community 6 - "TypeScript Config"
Cohesion: 0.15
Nodes (12): compilerOptions, esModuleInterop, forceConsistentCasingInFileNames, module, outDir, resolveJsonModule, rootDir, skipLibCheck (+4 more)

### Community 7 - "Instinct Games System"
Cohesion: 0.22
Nodes (7): BlindRatingGame, CaptionOrChaosGame, EngagementGuessGame, GuessTheirNicheGame, PhotoshopOrRealGame, WhoBlewUpFirstGame, WhosTheImposterGame

### Community 8 - "Railway Deployment"
Cohesion: 0.22
Nodes (8): build, buildCommand, builder, deploy, restartPolicyMaxRetries, restartPolicyType, startCommand, $schema

### Community 9 - "Prediction Games System"
Cohesion: 0.29
Nodes (7): schedulePredictionReveal(), buildPredictionGame(), FutureFlexGame, NextToBlowUpGame, PriceIsRightGame, ViralOrFlopGame, WouldTheyCollabGame

## Knowledge Gaps
- **72 isolated node(s):** `name`, `version`, `description`, `main`, `dev` (+67 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **4 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `BaseGame` connect `Taste Games System` to `Prediction Games System`, `Instinct Games System`?**
  _High betweenness centrality (0.126) - this node is a cross-community bridge._
- **Why does `db` connect `Database & Services` to `Core Events & Jobs`?**
  _High betweenness centrality (0.038) - this node is a cross-community bridge._
- **What connects `name`, `version`, `description` to the rest of the system?**
  _72 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `NPM Package Config` be split into smaller, more focused modules?**
  _Cohesion score 0.06060606060606061 - nodes in this community are weakly interconnected._
- **Should `Core Events & Jobs` be split into smaller, more focused modules?**
  _Cohesion score 0.11182795698924732 - nodes in this community are weakly interconnected._
- **Should `Database & Services` be split into smaller, more focused modules?**
  _Cohesion score 0.14942528735632185 - nodes in this community are weakly interconnected._
- **Should `Taste Games System` be split into smaller, more focused modules?**
  _Cohesion score 0.10826210826210826 - nodes in this community are weakly interconnected._
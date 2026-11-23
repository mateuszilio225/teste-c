CREATE TABLE IF NOT EXISTS rating_presets (
 player_id TEXT PRIMARY KEY NOT NULL,
 overall INTEGER NOT NULL CHECK(overall BETWEEN 40 AND 99),
 updated_at INTEGER NOT NULL
);
--> statement-breakpoint
CREATE TABLE IF NOT EXISTS rank_profiles (
 id TEXT PRIMARY KEY NOT NULL,
 name TEXT NOT NULL,
 step INTEGER NOT NULL DEFAULT 4,
 lp INTEGER NOT NULL DEFAULT 0,
 wins INTEGER NOT NULL DEFAULT 0,
 losses INTEGER NOT NULL DEFAULT 0,
 titles INTEGER NOT NULL DEFAULT 0,
 updated_at INTEGER NOT NULL
);
--> statement-breakpoint
CREATE TABLE IF NOT EXISTS rank_awards (
 marker TEXT PRIMARY KEY NOT NULL,
 profile_id TEXT NOT NULL,
 delta INTEGER NOT NULL,
 placed INTEGER NOT NULL,
 created_at INTEGER NOT NULL
);
--> statement-breakpoint
CREATE INDEX IF NOT EXISTS rank_profiles_score_idx ON rank_profiles(step DESC,lp DESC);

CREATE TABLE rooms (
 code TEXT PRIMARY KEY NOT NULL,
 state TEXT NOT NULL,
 auth TEXT NOT NULL,
 version INTEGER NOT NULL DEFAULT 1,
 updated_at INTEGER NOT NULL,
 expires_at INTEGER NOT NULL
);
--> statement-breakpoint
CREATE INDEX rooms_expiry_idx ON rooms(expires_at);
--> statement-breakpoint
CREATE TABLE rate_limits (
 key TEXT PRIMARY KEY NOT NULL,
 window INTEGER NOT NULL,
 count INTEGER NOT NULL DEFAULT 0
);

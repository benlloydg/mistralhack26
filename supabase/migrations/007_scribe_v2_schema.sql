-- Migration 007: Scribe v2 Realtime — new tables + transcript column additions
-- Date: 2026-02-28

-- live_partials: one active partial transcript per case (upserted by Scribe v2)
CREATE TABLE IF NOT EXISTS live_partials (
  case_id TEXT PRIMARY KEY REFERENCES incident_state(case_id),
  text TEXT NOT NULL,
  timestamp FLOAT NOT NULL,
  updated_at TIMESTAMPTZ DEFAULT now()
);

-- demo_control: coordinates frontend playback state
CREATE TABLE IF NOT EXISTS demo_control (
  case_id TEXT PRIMARY KEY REFERENCES incident_state(case_id),
  status TEXT NOT NULL DEFAULT 'ready',
  video_url TEXT,
  approve_enabled BOOLEAN DEFAULT false,
  approve_clicked BOOLEAN DEFAULT false,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Extend transcripts with feed/direction/priority/audio/facts columns
ALTER TABLE transcripts ADD COLUMN IF NOT EXISTS feed_id TEXT;
ALTER TABLE transcripts ADD COLUMN IF NOT EXISTS direction TEXT DEFAULT 'inbound';
ALTER TABLE transcripts ADD COLUMN IF NOT EXISTS priority TEXT;
ALTER TABLE transcripts ADD COLUMN IF NOT EXISTS audio_url TEXT;
ALTER TABLE transcripts ADD COLUMN IF NOT EXISTS facts_extracted JSONB;

-- Extend agent_logs with model column
ALTER TABLE agent_logs ADD COLUMN IF NOT EXISTS model TEXT;

-- Enable Realtime on new tables
ALTER PUBLICATION supabase_realtime ADD TABLE live_partials;
ALTER PUBLICATION supabase_realtime ADD TABLE demo_control;

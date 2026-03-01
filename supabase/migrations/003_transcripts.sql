-- Per-caller transcript segments. Frontend renders as the "Transcript Panel" with tabs.
CREATE TABLE transcripts (
  id BIGSERIAL PRIMARY KEY,
  case_id TEXT NOT NULL REFERENCES incident_state(case_id),
  caller_id TEXT NOT NULL,         -- caller_1, caller_2, caller_3
  caller_label TEXT,               -- "The Wife", "Bystander", "Shopkeeper"
  language TEXT NOT NULL,           -- es, zh, fr
  original_text TEXT NOT NULL,      -- Original language transcript
  translated_text TEXT,             -- English translation
  entities JSONB DEFAULT '[]'::jsonb, -- Extracted entities
  confidence FLOAT,
  segment_index INT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_transcripts_case ON transcripts(case_id);
CREATE INDEX idx_transcripts_caller ON transcripts(case_id, caller_id);

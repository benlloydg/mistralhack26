-- Every agent action gets logged here. Frontend renders as the "Agent Terminal" panel.
CREATE TABLE agent_logs (
  id BIGSERIAL PRIMARY KEY,
  case_id TEXT NOT NULL REFERENCES incident_state(case_id),
  agent TEXT NOT NULL,             -- triage | vision | voice | dispatch | intake | orchestrator
  event_type TEXT NOT NULL,        -- transcript_received | severity_changed | detection | dispatch | etc
  message TEXT NOT NULL,           -- Human-readable log line
  data JSONB DEFAULT '{}'::jsonb,  -- Structured event data
  display_color TEXT DEFAULT 'blue', -- UI color hint: blue | red | amber | green | purple
  display_flash BOOLEAN DEFAULT false, -- If true, UI should flash/pulse this entry
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_agent_logs_case ON agent_logs(case_id);
CREATE INDEX idx_agent_logs_created ON agent_logs(created_at);

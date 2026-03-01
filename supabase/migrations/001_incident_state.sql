-- The single source of truth. Agents write here. Frontend reads via Realtime.
CREATE TABLE incident_state (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  case_id TEXT UNIQUE NOT NULL,               -- e.g. "TN-2026-00417"
  status TEXT NOT NULL DEFAULT 'intake',       -- intake | active | escalated | critical | resolved_demo
  incident_type TEXT,                          -- vehicle_collision | fire | etc
  location_raw TEXT,
  location_normalized TEXT,
  severity TEXT NOT NULL DEFAULT 'unknown',    -- unknown | low | medium | high | critical
  caller_count INT NOT NULL DEFAULT 0,
  people_count_estimate INT DEFAULT 0,
  injury_flags JSONB DEFAULT '[]'::jsonb,      -- ["trapped_person", "child_present"]
  hazard_flags JSONB DEFAULT '[]'::jsonb,      -- ["engine_fire", "smoke"]
  vision_detections JSONB DEFAULT '[]'::jsonb,  -- [{type, confidence, frame_id}]
  recommended_units JSONB DEFAULT '[]'::jsonb,  -- ["EMS", "Fire Response"]
  confirmed_units JSONB DEFAULT '[]'::jsonb,    -- ["EMS", "Traffic Control"]
  timeline JSONB DEFAULT '[]'::jsonb,           -- [{t, agent, event}]
  action_plan_version INT DEFAULT 0,
  action_plan JSONB DEFAULT '[]'::jsonb,        -- [{status, action}]
  match_confidence FLOAT,
  operator_summary TEXT,
  confidence_scores JSONB DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

-- Auto-update updated_at
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_updated_at
  BEFORE UPDATE ON incident_state
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- Dispatch records. One row per dispatched unit.
CREATE TABLE dispatches (
  id BIGSERIAL PRIMARY KEY,
  case_id TEXT NOT NULL REFERENCES incident_state(case_id),
  unit_type TEXT NOT NULL,         -- EMS | Fire Response | Pediatric EMS | Traffic Control
  unit_assigned TEXT,              -- AMB-7, ENG-4, PED-2, etc
  destination TEXT,                -- Mass General ER, UCSF Children's, etc
  eta_minutes INT,
  status TEXT NOT NULL DEFAULT 'recommended', -- recommended | confirmed | dispatched
  voice_message TEXT,              -- Generated dispatch brief
  language TEXT DEFAULT 'en',
  rationale TEXT,                  -- Why this unit was dispatched
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_dispatches_case ON dispatches(case_id);

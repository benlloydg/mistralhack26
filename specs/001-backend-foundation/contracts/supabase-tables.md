# Contract: Supabase Tables

These are the database contracts between backend (writer) and frontend (reader via Realtime).

## incident_state

| Column | Type | Default | Constraint |
|--------|------|---------|------------|
| id | UUID | gen_random_uuid() | PRIMARY KEY |
| case_id | TEXT | — | UNIQUE NOT NULL |
| status | TEXT | 'intake' | NOT NULL |
| incident_type | TEXT | — | — |
| location_raw | TEXT | — | — |
| location_normalized | TEXT | — | — |
| severity | TEXT | 'unknown' | NOT NULL |
| caller_count | INT | 0 | NOT NULL |
| people_count_estimate | INT | 0 | — |
| injury_flags | JSONB | '[]' | — |
| hazard_flags | JSONB | '[]' | — |
| vision_detections | JSONB | '[]' | — |
| recommended_units | JSONB | '[]' | — |
| confirmed_units | JSONB | '[]' | — |
| timeline | JSONB | '[]' | — |
| action_plan_version | INT | 0 | — |
| action_plan | JSONB | '[]' | — |
| match_confidence | FLOAT | — | — |
| operator_summary | TEXT | — | — |
| confidence_scores | JSONB | '{}' | — |
| created_at | TIMESTAMPTZ | now() | — |
| updated_at | TIMESTAMPTZ | now() | auto-updated via trigger |

## agent_logs

| Column | Type | Default | Constraint |
|--------|------|---------|------------|
| id | BIGSERIAL | — | PRIMARY KEY |
| case_id | TEXT | — | NOT NULL, FK → incident_state(case_id) |
| agent | TEXT | — | NOT NULL |
| event_type | TEXT | — | NOT NULL |
| message | TEXT | — | NOT NULL |
| data | JSONB | '{}' | — |
| display_color | TEXT | 'blue' | — |
| display_flash | BOOLEAN | false | — |
| created_at | TIMESTAMPTZ | now() | — |

## transcripts

| Column | Type | Default | Constraint |
|--------|------|---------|------------|
| id | BIGSERIAL | — | PRIMARY KEY |
| case_id | TEXT | — | NOT NULL, FK → incident_state(case_id) |
| caller_id | TEXT | — | NOT NULL |
| caller_label | TEXT | — | — |
| language | TEXT | — | NOT NULL |
| original_text | TEXT | — | NOT NULL |
| translated_text | TEXT | — | — |
| entities | JSONB | '[]' | — |
| confidence | FLOAT | — | — |
| segment_index | INT | — | NOT NULL |
| created_at | TIMESTAMPTZ | now() | — |

## dispatches

| Column | Type | Default | Constraint |
|--------|------|---------|------------|
| id | BIGSERIAL | — | PRIMARY KEY |
| case_id | TEXT | — | NOT NULL, FK → incident_state(case_id) |
| unit_type | TEXT | — | NOT NULL |
| unit_assigned | TEXT | — | — |
| destination | TEXT | — | — |
| eta_minutes | INT | — | — |
| status | TEXT | 'recommended' | NOT NULL |
| voice_message | TEXT | — | — |
| language | TEXT | 'en' | — |
| rationale | TEXT | — | — |
| created_at | TIMESTAMPTZ | now() | — |

## Realtime

All 4 tables are added to `supabase_realtime` publication for frontend subscriptions.

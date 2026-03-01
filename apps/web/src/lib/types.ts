export interface IncidentState {
  case_id: string;
  status: 'intake' | 'active' | 'escalated' | 'critical' | 'resolved_demo';
  incident_type: string | null;
  location_raw: string | null;
  location_normalized: string | null;
  severity: 'unknown' | 'low' | 'medium' | 'high' | 'critical';
  caller_count: number;
  people_count_estimate: number;
  injury_flags: string[];
  hazard_flags: string[];
  vision_detections: any[];
  recommended_units: string[];
  confirmed_units: string[];
  timeline: { t: string; agent: string; event: string }[];
  action_plan_version: number;
  action_plan: { status: string; action: string }[];
  match_confidence: number | null;
  operator_summary: string | null;
  confidence_scores: Record<string, number>;
  created_at: string;
  updated_at: string;
}

export interface AgentLog {
  id: number;
  case_id: string;
  agent: string;
  event_type: string;
  message: string;
  data: any;
  display_color: string;
  display_flash: boolean;
  created_at: string;
}

export interface Transcript {
  id: number;
  case_id: string;
  caller_id: string;
  caller_label: string | null;
  language: string;
  original_text: string;
  translated_text: string | null;
  entities: string[];
  confidence: number | null;
  segment_index: number;
  created_at: string;
  feed_id?: string | null;
  direction?: string | null;
  priority?: string | null;
  audio_url?: string | null;
}

export interface Dispatch {
  id: number;
  case_id: string;
  unit_type: string;
  unit_assigned: string | null;
  destination: string | null;
  eta_minutes: number | null;
  status: 'recommended' | 'confirmed' | 'dispatched';
  voice_message: string | null;
  language: string;
  rationale: string | null;
  created_at: string;
}

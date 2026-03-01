import { ReportData } from "./page";

export const demoReportData: ReportData = {
  case_id: "TN-2026-00417",
  generated_at: "2026-03-01T03:35:12Z",
  warning: null,
  header: {
    case_id: "TN-2026-00417",
    incident_type: "VEHICLE COLLISION + FIRE + EXPLOSION",
    location: "Market St & 5th St, San Francisco, CA",
    severity: "CRITICAL",
    status: "SCENE_SECURED",
    duration_seconds: 55,
    speaker_count: 4,
    languages: ["EN", "ES", "ZH", "FR"],
    audio_segments: 4,
    vision_frames: 2,
    outcome: "ZERO CASUALTIES — ALL PERSONS EVACUATED"
  },
  timeline: [
    {
      t: "00:00",
      timestamp: "2026-03-01T03:33:45Z",
      agent: "SYSTEM",
      model: null,
      event_type: "INITIALIZATION",
      message: "Demo initialized. Case created.\nScene monitoring armed: CAM-04 + MIC-04.",
      severity_indicator: "info",
      color: "blue",
      flash: false
    },
    {
      t: "00:03",
      timestamp: "2026-03-01T03:33:48Z",
      agent: "AUDIO",
      model: "scribe-v2",
      event_type: "PRE_INCIDENT",
      message: "Multiple speakers, elevated stress.\nStatus: MONITORING",
      severity_indicator: "info",
      color: "amber",
      flash: false
    },
    {
      t: "00:05",
      timestamp: "2026-03-01T03:33:50Z",
      agent: "TRIAGE",
      model: "mistral-lg",
      event_type: "ASSESSMENT",
      message: "Vehicle out of control reported.\nThreat assessment: POSSIBLE SITUATION",
      severity_indicator: "info",
      color: "blue",
      flash: false
    },
    {
      t: "00:07",
      timestamp: "2026-03-01T03:33:52Z",
      agent: "FUSION",
      model: "mistral-lg",
      event_type: "IMPACT DETECTED",
      message: "Collision confirmed via audio spike\nand visual scene change.\nStatus: MONITORING → ACTIVE",
      severity_indicator: "critical",
      color: "red",
      flash: true
    },
    {
      t: "00:08",
      timestamp: "2026-03-01T03:33:53Z",
      agent: "AUDIO",
      model: "scribe-v2",
      event_type: "TRANSCRIPT",
      message: "\"My husband is trapped in the car\"\nLocation: Market & 5th",
      severity_indicator: "info",
      color: "amber",
      flash: false
    },
    {
      t: "00:10",
      timestamp: "2026-03-01T03:33:55Z",
      agent: "TRIAGE",
      model: "mistral-lg",
      event_type: "SEVERITY_UPDATE",
      message: "Severity: HIGH\nRecommend: EMS, Traffic Control\nAction Plan v1",
      severity_indicator: "info",
      color: "blue",
      flash: false
    },
    {
      t: "00:12",
      timestamp: "2026-03-01T03:33:57Z",
      agent: "OPERATOR",
      model: null,
      event_type: "RESPONSE APPROVED",
      message: "EMS + Traffic Control confirmed.",
      severity_indicator: "operator",
      color: "green",
      flash: false
    },
    {
      t: "00:15",
      timestamp: "2026-03-01T03:34:00Z",
      agent: "AUDIO",
      model: "scribe-v2",
      event_type: "TRANSCRIPT",
      message: "\"Child in the back seat\"",
      severity_indicator: "info",
      color: "amber",
      flash: false
    },
    {
      t: "00:18",
      timestamp: "2026-03-01T03:34:03Z",
      agent: "FUSION",
      model: "mistral-lg",
      event_type: "ESCALATION",
      message: "Evidence fused: trapped adult +\nchild present. Two independent\naudio sources corroborating.\n── SEVERITY: HIGH → CRITICAL ──",
      severity_indicator: "critical",
      color: "red",
      flash: true
    },
    {
      t: "00:26",
      timestamp: "2026-03-01T03:34:11Z",
      agent: "AUDIO",
      model: "scribe-v2",
      event_type: "TRANSCRIPT",
      message: "\"The engine is on fire!\"",
      severity_indicator: "info",
      color: "amber",
      flash: false
    },
    {
      t: "00:31",
      timestamp: "2026-03-01T03:34:16Z",
      agent: "VISION",
      model: "pixtral-12b",
      event_type: "ENGINE FIRE DETECTED (0.99)",
      message: "Engine block temperature critical.",
      severity_indicator: "critical",
      color: "purple",
      flash: true
    },
    {
      t: "00:32",
      timestamp: "2026-03-01T03:34:17Z",
      agent: "FUSION",
      model: "mistral-lg",
      event_type: "CROSS-MODAL CORROBORATION",
      message: "Fire confirmed by 2 modalities:\n→ Vision: engine fire (0.99)\n→ Audio: FR speaker reported fire\nFire first detected by vision.\nNo audio source aware before camera.\n── EVACUATION PROTOCOL TRIGGERED ──",
      severity_indicator: "critical",
      color: "red",
      flash: true
    },
    {
      t: "00:35",
      timestamp: "2026-03-01T03:34:20Z",
      agent: "OPERATOR",
      model: null,
      event_type: "EVACUATION BROADCAST",
      message: "Warnings generated in 3 languages\nvia ElevenLabs TTS:\n🔊 ES: \"¡Evacúen el área!\"     ✓\n🔊 ZH: \"请立即撤离！\"            ✓\n🔊 FR: \"Évacuez la zone !\"      ✓",
      severity_indicator: "operator",
      color: "green",
      flash: false
    },
    {
      t: "00:42",
      timestamp: "2026-03-01T03:34:27Z",
      agent: "VISION",
      model: "pixtral-12b",
      event_type: "SCENE UPDATE",
      message: "Scene clearing. Bystanders\nevacuating intersection.",
      severity_indicator: "info",
      color: "purple",
      flash: false
    },
    {
      t: "00:52",
      timestamp: "2026-03-01T03:34:37Z",
      agent: "FUSION",
      model: null,
      event_type: "SECONDARY EXPLOSION",
      message: "Fireball detected. Structural\ndebris. High-amplitude audio event.",
      severity_indicator: "critical",
      color: "red",
      flash: true
    },
    {
      t: "00:53",
      timestamp: "2026-03-01T03:34:38Z",
      agent: "TRIAGE",
      model: "mistral-lg",
      event_type: "OUTCOME CONFIRMATION",
      message: "Explosion at incident site.\nChecking scene clearance...\n██ ALL PERSONS EVACUATED PRIOR ██\n██ TO DETONATION. ZERO CASUALTIES ██",
      severity_indicator: "critical",
      color: "blue",
      flash: false
    },
    {
      t: "00:55",
      timestamp: "2026-03-01T03:34:40Z",
      agent: "SYSTEM",
      model: null,
      event_type: "SCENE SECURED",
      message: "Case resolved. Report generated.",
      severity_indicator: "info",
      color: "blue",
      flash: false
    }
  ],
  evidence_sources: {
    audio: {
      speaker_count: 4,
      languages: ["EN", "ES", "ZH", "FR"],
      transcript_count: 7,
      speakers: [
        { feed_id: "CH1", language: "ES", label: "female", key_intelligence: "Trapped occupant, location", segment_count: 2 },
        { feed_id: "CH2", language: "ZH", label: "male", key_intelligence: "Child in back seat", segment_count: 1 },
        { feed_id: "CH3", language: "FR", label: "male", key_intelligence: "Engine fire (corroborated by vision)", segment_count: 1 },
        { feed_id: "CH4", language: "EN", label: "multiple", key_intelligence: "Pre-incident stress indicators", segment_count: 3 }
      ]
    },
    vision: {
      frames_analyzed: 4,
      detections: [
        { timestamp_s: 7, type: "collision", confidence: 0.95, description: "collision event (scene change)" },
        { timestamp_s: 25, type: "smoke", confidence: 0.87, description: "smoke detected" },
        { timestamp_s: 38, type: "fire", confidence: 0.99, description: "engine fire detected" },
        { timestamp_s: 52, type: "explosion", confidence: 0.98, description: "secondary explosion detected" }
      ]
    },
    cross_modal: [
      { claim: "Fire Confirmation", modalities: ["Vision", "Audio"], details: "Vision detected at T+38s, Audio (FR) reported at T+36s" },
      { claim: "Collision", modalities: ["Audio", "Vision"], details: "Audio (ES) reported at T+08s, Vision confirmed at T+07s" },
      { claim: "Evacuation Effective", modalities: ["Vision", "Audio"], details: "Vision confirmed scene clear at T+42s" }
    ]
  },
  convergence_tracks: [
    {
      source: "EN", type: "audio", color: "blue", events: [
        { t_seconds: 0, label: "yelling", type: "normal" },
        { t_seconds: 5, label: "pre-crash", type: "normal" }
      ]
    },
    {
      source: "ES", type: "audio", color: "amber", events: [
        { t_seconds: 8, label: "trapped", type: "normal" },
        { t_seconds: 35, label: "evac sent", type: "action" }
      ]
    },
    {
      source: "ZH", type: "audio", color: "emerald", events: [
        { t_seconds: 15, label: "child", type: "normal" },
        { t_seconds: 35, label: "evac sent", type: "action" }
      ]
    },
    {
      source: "FR", type: "audio", color: "purple", events: [
        { t_seconds: 26, label: "fire reported", type: "normal" },
        { t_seconds: 35, label: "evac sent", type: "action" }
      ]
    },
    {
      source: "CAM", type: "vision", color: "cyan", events: [
        { t_seconds: 7, label: "collision", type: "normal" },
        { t_seconds: 25, label: "smoke", type: "normal" },
        { t_seconds: 31, label: "FIRE", type: "critical" },
        { t_seconds: 52, label: "EXPLOSION", type: "critical" }
      ]
    },
    {
      source: "FUSED", type: "fused", color: "gold", events: [
        { t_seconds: 3, label: "watch", type: "normal" },
        { t_seconds: 7, label: "active", type: "normal" },
        { t_seconds: 10, label: "HIGH", type: "normal" },
        { t_seconds: 18, label: "child", type: "normal" },
        { t_seconds: 25, label: "smoke", type: "normal" },
        { t_seconds: 32, label: "FIRE", type: "critical" },
        { t_seconds: 35, label: "evac", type: "action" },
        { t_seconds: 55, label: "SECURED", type: "normal" }
      ]
    }
  ],
  response_actions: [
    { action: "EMS (AMB-7)", unit_type: "Medical", unit_assigned: "AMB-7", status: "CONFIRMED", authorized_at: "T+00:12", authorization_method: "Operator", language: null },
    { action: "Traffic Control", unit_type: "Police", unit_assigned: "PD-2", status: "CONFIRMED", authorized_at: "T+00:12", authorization_method: "Operator", language: null },
    { action: "Pediatric EMS", unit_type: "Medical", unit_assigned: "AMB-11", status: "EXECUTED", authorized_at: "T+00:21", authorization_method: "Operator", language: null },
    { action: "Fire Response", unit_type: "Fire", unit_assigned: "ENG-4", status: "EXECUTED", authorized_at: "T+00:34", authorization_method: "Operator", language: null },
    { action: "Evacuation (ES)", unit_type: "Comm", unit_assigned: "TTS-SYS", status: "BROADCAST", authorized_at: "T+00:35", authorization_method: "Autonomous", language: "ES" },
    { action: "Evacuation (ZH)", unit_type: "Comm", unit_assigned: "TTS-SYS", status: "BROADCAST", authorized_at: "T+00:36", authorization_method: "Autonomous", language: "ZH" },
    { action: "Evacuation (FR)", unit_type: "Comm", unit_assigned: "TTS-SYS", status: "BROADCAST", authorized_at: "T+00:37", authorization_method: "Autonomous", language: "FR" }
  ],
  agent_stats: {
    agents: [
      { agent: "IntakeAgent", model: "elevenlabs-scribe", invocations: 7, avg_latency_seconds: 0.8 },
      { agent: "IntakeAgent", model: "mistral-large", invocations: 7, avg_latency_seconds: 1.2 },
      { agent: "TriageAgent", model: "mistral-large", invocations: 5, avg_latency_seconds: 1.4 },
      { agent: "CaseMatchAgent", model: "mistral-large", invocations: 3, avg_latency_seconds: 0.9 },
      { agent: "EvidenceFusion", model: "mistral-large", invocations: 4, avg_latency_seconds: 1.1 },
      { agent: "VisionAgent", model: "pixtral-12b", invocations: 4, avg_latency_seconds: 2.1 },
      { agent: "DispatchAgent", model: "mistral-large", invocations: 4, avg_latency_seconds: 0.7 },
      { agent: "VoiceAgent", model: "elevenlabs-tts", invocations: 3, avg_latency_seconds: 1.8 }
    ],
    total_invocations: 37,
    total_duration_seconds: 55,
    models_used: [
      { model: "Mistral Large", roles: ["Triage", "intake", "fusion", "dispatch", "case match"] },
      { model: "Pixtral 12B", roles: ["Scene analysis", "hazard detection"] },
      { model: "ElevenLabs Scribe", roles: ["Real-time multilingual transcription"] },
      { model: "ElevenLabs TTS", roles: ["Multilingual voice response generation"] }
    ]
  },
  key_frames: [
    { image_url: "", timestamp_s: 7, elapsed: "T+00:07", detections: [{ type: "collision", confidence: 0.95 }], description: "COLLISION DETECTED", is_hero: false },
    { image_url: "", timestamp_s: 38, elapsed: "T+00:38", detections: [{ type: "fire", confidence: 0.99 }], description: "ENGINE FIRE DETECTED", is_hero: true },
    { image_url: "", timestamp_s: 52, elapsed: "T+00:52", detections: [{ type: "explosion", confidence: 0.98 }], description: "SECONDARY EXPLOSION", is_hero: false }
  ],
  executive_summary: "At 03:33:45 UTC, DISPATCH detected a vehicle collision at Market St & 5th St via concurrent audio and visual monitoring. Over the following 55 seconds, the system processed 7 audio segments in 4 languages (English, Spanish, Mandarin, French), analyzed 4 video frames, and executed 5 evidence fusion cycles. Critical intelligence included a trapped occupant (ES audio), a child in the vehicle (ZH audio), and an engine fire detected independently by both vision (0.99 confidence) and audio (FR speaker). The system autonomously broadcast evacuation warnings in 3 languages, clearing all persons from the scene 10 seconds before a secondary explosion destroyed both vehicles. Zero casualties resulted from this incident."
};

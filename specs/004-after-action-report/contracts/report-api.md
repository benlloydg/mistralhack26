# API Contract: After-Action Report

**Feature**: 004-after-action-report
**Date**: 2026-03-01

## Endpoints

### `POST /api/v1/cases/{case_id}/report`

Generate (or return cached) the full after-action report.

**Path Parameters**:
- `case_id` (string, required) — e.g., `TN-20260301-033345`

**Response** `200 OK`:
```json
{
  "case_id": "TN-20260301-033345",
  "generated_at": "2026-03-01T03:35:12Z",
  "warning": null,

  "header": {
    "case_id": "TN-20260301-033345",
    "incident_type": "vehicle_crash",
    "location": "Market St & 5th St, San Francisco, CA",
    "severity": "critical",
    "status": "resolved_demo",
    "duration_seconds": 55.0,
    "speaker_count": 4,
    "languages": ["en", "es", "zh", "fr"],
    "audio_segments": 7,
    "vision_frames": 4,
    "outcome": "ZERO CASUALTIES — ALL PERSONS EVACUATED"
  },

  "timeline": [
    {
      "t": "00:00",
      "timestamp": "2026-03-01T03:33:45Z",
      "agent": "orchestrator",
      "model": null,
      "event_type": "init",
      "message": "Demo started: TN-20260301-033345",
      "severity_indicator": "regular",
      "color": "blue",
      "flash": false
    },
    {
      "t": "00:08",
      "timestamp": "2026-03-01T03:33:53Z",
      "agent": "voice",
      "model": "scribe-v2",
      "event_type": "transcript_committed",
      "message": "[FEED_1] Committed (es): Mi esposo está atrapado...",
      "severity_indicator": "regular",
      "color": "green",
      "flash": false
    },
    {
      "t": "00:32",
      "timestamp": "2026-03-01T03:34:17Z",
      "agent": "evidence_fusion",
      "model": "mistral-large-latest",
      "event_type": "CROSS_MODAL_CORROBORATION",
      "message": "FIRE confirmed by 2 independent modalities:\n  → Vision: FIRE (0.99) at frame T+38s\n  → Audio: FR speaker reported fire (0.85)\nAutonomous evacuation protocol triggered.",
      "severity_indicator": "critical",
      "color": "red",
      "flash": true
    }
  ],

  "evidence_sources": {
    "audio": {
      "speaker_count": 4,
      "languages": ["en", "es", "zh", "fr"],
      "transcript_count": 7,
      "speakers": [
        {
          "feed_id": "FEED_1",
          "language": "es",
          "label": "Scene Audio (FEED_1)",
          "key_intelligence": "Trapped occupant, location confirmed",
          "segment_count": 2
        }
      ]
    },
    "vision": {
      "frames_analyzed": 4,
      "detections": [
        {
          "timestamp_s": 25.0,
          "type": "smoke",
          "confidence": 0.87,
          "description": "Smoke detected from vehicle engine"
        },
        {
          "timestamp_s": 38.0,
          "type": "engine_fire",
          "confidence": 0.99,
          "description": "Engine fire detected — first detection"
        }
      ]
    },
    "cross_modal": [
      {
        "claim": "fire",
        "modalities": ["vision", "audio"],
        "details": "Vision detected at T+38s, Audio (FR) reported at T+36s"
      }
    ]
  },

  "convergence_tracks": [
    {
      "source": "ES",
      "type": "audio",
      "color": "#F59E0B",
      "events": [
        {"t_seconds": 8.0, "label": "trapped", "type": "detection"},
        {"t_seconds": 35.0, "label": "evac sent", "type": "action"}
      ]
    },
    {
      "source": "CAM",
      "type": "vision",
      "color": "#06B6D4",
      "events": [
        {"t_seconds": 25.0, "label": "smoke", "type": "detection"},
        {"t_seconds": 38.0, "label": "FIRE", "type": "escalation"}
      ]
    },
    {
      "source": "FUSED",
      "type": "fused",
      "color": "#FBBF24",
      "events": [
        {"t_seconds": 0.0, "label": "watch", "type": "state_change"},
        {"t_seconds": 8.0, "label": "active", "type": "state_change"},
        {"t_seconds": 18.0, "label": "CRITICAL", "type": "escalation"},
        {"t_seconds": 32.0, "label": "evacuation", "type": "action"},
        {"t_seconds": 55.0, "label": "SECURED", "type": "state_change"}
      ]
    }
  ],

  "response_actions": [
    {
      "action": "EMS (AMB-7)",
      "unit_type": "EMS",
      "unit_assigned": "AMB-7",
      "status": "confirmed",
      "authorized_at": "00:12",
      "authorization_method": "operator",
      "language": null
    },
    {
      "action": "Evacuation (ES)",
      "unit_type": "Evacuation",
      "unit_assigned": null,
      "status": "broadcast",
      "authorized_at": "00:35",
      "authorization_method": "autonomous",
      "language": "es"
    }
  ],

  "agent_stats": {
    "agents": [
      {
        "agent": "IntakeAgent",
        "model": "mistral-large-latest",
        "invocations": 7,
        "avg_latency_seconds": 1.2
      },
      {
        "agent": "VisionAgent",
        "model": "pixtral-large-latest",
        "invocations": 4,
        "avg_latency_seconds": 2.1
      }
    ],
    "total_invocations": 37,
    "total_duration_seconds": 55.0,
    "models_used": [
      {"model": "Mistral Large", "roles": ["Triage", "Intake", "Fusion", "Dispatch"]},
      {"model": "Pixtral 12B", "roles": ["Scene analysis", "Hazard detection"]},
      {"model": "ElevenLabs Scribe v2", "roles": ["Real-time multilingual transcription"]},
      {"model": "ElevenLabs TTS", "roles": ["Multilingual voice response"]}
    ]
  },

  "key_frames": [
    {
      "image_url": "/frames/TN-20260301-033345_t25s.jpg",
      "timestamp_s": 25.0,
      "elapsed": "00:25",
      "detections": [
        {"type": "smoke", "confidence": 0.87}
      ],
      "description": "Smoke detected from vehicle engine area",
      "is_hero": false
    },
    {
      "image_url": "/frames/TN-20260301-033345_t38s.jpg",
      "timestamp_s": 38.0,
      "elapsed": "00:38",
      "detections": [
        {"type": "engine_fire", "confidence": 0.99}
      ],
      "description": "Engine fire detected — highest confidence detection",
      "is_hero": true
    }
  ],

  "executive_summary": "At 03:33:45 UTC, DISPATCH detected a vehicle collision at Market St & 5th St via concurrent audio and visual monitoring. Over the following 55 seconds, the system processed 7 audio segments in 4 languages (English, Spanish, Mandarin, French), analyzed 4 video frames, and executed 5 evidence fusion cycles. Critical intelligence included a trapped occupant (ES audio), a child in the vehicle (ZH audio), and an engine fire detected independently by both vision (0.99 confidence) and audio (FR speaker). The system autonomously broadcast evacuation warnings in 3 languages, clearing all persons from the scene 10 seconds before a secondary explosion destroyed both vehicles. Zero casualties resulted from this incident."
}
```

**Response** `404 Not Found` (case doesn't exist):
```json
{"detail": "Case not found: TN-INVALID"}
```

---

### `GET /api/v1/cases/{case_id}/report`

Return cached report if it exists, 404 otherwise.

**Response** `200 OK`: Same shape as POST response above.
**Response** `404 Not Found`: Report not yet generated for this case.

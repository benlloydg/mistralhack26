---
title: "TriageNet — Real-Time Emergency Dispatch System"
---
%%{init: {'theme': 'dark', 'themeVariables': { 'primaryColor': '#1e3a5f', 'primaryTextColor': '#e0e0e0', 'primaryBorderColor': '#4a90d9', 'lineColor': '#4a90d9', 'secondaryColor': '#2d1f3d', 'tertiaryColor': '#1a2e1a', 'fontSize': '14px' }}}%%

flowchart TB
    %% ═══════════════════════════════════════════════════════════
    %% TITLE & SPONSORS
    %% ═══════════════════════════════════════════════════════════
    subgraph SPONSORS["🏆 Hackathon Sponsors & Judges"]
        direction LR
        MISTRAL_SPONSOR["<b>Mistral AI</b><br/>LLM Reasoning & Vision"]
        ELEVENLABS_SPONSOR["<b>ElevenLabs</b><br/>Speech-to-Text & Text-to-Speech"]
    end

    %% ═══════════════════════════════════════════════════════════
    %% INPUT LAYER — Video + Audio Source
    %% ═══════════════════════════════════════════════════════════
    subgraph INPUT["📹 Input Layer"]
        VIDEO["🎬 CCTV Video File<br/><i>scene.mp4 / crash_01.mp4</i>"]
        VIDEO -->|"ffmpeg -vn -acodec pcm_s16le<br/>-ar 16000 -ac 1"| PCM["🔊 Raw PCM Audio<br/><i>16kHz · 16-bit · mono</i><br/><i>32,000 bytes/sec</i>"]
        VIDEO -->|"ffmpeg frame extraction<br/>every 3 seconds"| FRAMES["🖼️ Video Frames<br/><i>JPEG · starting at t=3s</i>"]
    end

    %% ═══════════════════════════════════════════════════════════
    %% ELEVENLABS LAYER — Speech Processing
    %% ═══════════════════════════════════════════════════════════
    subgraph ELEVENLABS["🎙️ ElevenLabs API"]
        direction TB
        SCRIBE["<b>Scribe v2 Realtime</b><br/>Model: <code>scribe_v2_realtime</code><br/>WebSocket · VAD Commits<br/><i>silence threshold: 0.8s</i><br/><i>vad threshold: 0.3</i>"]
        TTS["<b>Text-to-Speech</b><br/>Model: <code>eleven_turbo_v2_5</code><br/>Voices: George, Lily,<br/>Charlotte, Brian, Antoni"]
    end

    PCM -->|"100ms chunks at 2× speed<br/>base64-encoded over WebSocket"| SCRIBE

    %% ═══════════════════════════════════════════════════════════
    %% SCRIBE OUTPUTS
    %% ═══════════════════════════════════════════════════════════
    SCRIBE -->|"Partial transcript<br/>(during speech)"| PARTIAL["💬 Live Partial<br/><i>UI shimmer effect</i>"]
    SCRIBE -->|"Committed transcript<br/>(on speech pause)"| COMMITTED["✅ Committed Transcript<br/><i>+ language heuristic detection</i><br/><i>es · fr · zh · en · ar · ru</i>"]

    %% ═══════════════════════════════════════════════════════════
    %% ORCHESTRATOR — Event-Driven Core
    %% ═══════════════════════════════════════════════════════════
    subgraph ORCHESTRATOR["⚡ Event-Driven Orchestrator <i>(Python · FastAPI)</i>"]
        direction TB

        subgraph AUDIO_PIPELINE["🔊 Audio Pipeline — Transcript Processing"]
            direction TB
            RAW_INSERT["1️⃣ Insert Raw Transcript<br/><i>fire-and-forget → Supabase</i>"]

            subgraph PARALLEL_1["⚡ Phase 1: Parallel Execution"]
                direction LR
                TRANSLATE["🌐 <b>Translate to English</b><br/>Model: <code>mistral-large-latest</code><br/><i>skip if already English</i>"]
                INTAKE["📋 <b>Intake Agent</b><br/>Model: <code>mistral-large-latest</code><br/><i>Extract: location, injuries,</i><br/><i>hazards, trapped, children</i>"]
            end

            UI_PUSH["2️⃣ Push Translation + Facts<br/><i>fire-and-forget → Supabase</i>"]

            TRIAGE["🚨 <b>Triage Agent</b><br/>Model: <code>mistral-large-latest</code><br/><i>Severity · hazard flags ·</i><br/><i>recommended units · action plan</i><br/><i>Tools: get_current_state,</i><br/><i>get_all_transcripts,</i><br/><i>get_vision_detections</i>"]

            FUSION_BG["🔗 <b>Evidence Fusion Agent</b><br/>Model: <code>mistral-large-latest</code><br/><i>Background · cross-modal</i><br/><i>corroboration · evacuation check</i><br/><i>Tool: get_all_evidence</i>"]

            RAW_INSERT --> PARALLEL_1
            PARALLEL_1 --> UI_PUSH
            UI_PUSH --> TRIAGE
            TRIAGE -->|"deferred background task"| FUSION_BG
        end

        subgraph VISION_PIPELINE["👁️ Vision Pipeline — Continuous Analysis"]
            direction TB
            VISION_AGENT["🔍 <b>Vision Agent</b><br/>Model: <code>pixtral-large-latest</code><br/><i>Detects: vehicle_collision,</i><br/><i>smoke, engine_fire, persons,</i><br/><i>debris, hazmat_placard</i><br/><i>Async · overlapping API calls</i>"]
            VISION_DELTA["📊 Scene Delta Detection<br/><i>Track fire/smoke escalation</i><br/><i>Re-triage on hazard change</i>"]
            VISION_AGENT --> VISION_DELTA
        end

        subgraph EVACUATION["🚨 Evacuation Protocol"]
            direction TB
            EVAC_CHECK{"Fire + People<br/>at Risk?"}
            EVAC_TTS["📢 <b>TTS Broadcast</b><br/><i>All 4 languages:</i><br/><i>🇬🇧 EN · 🇪🇸 ES · 🇨🇳 ZH · 🇫🇷 FR</i>"]
            EVAC_DISPATCH["🚒 Auto-Dispatch<br/><i>Fire Response unit</i>"]
            EVAC_CHECK -->|"Yes"| EVAC_TTS
            EVAC_CHECK -->|"Yes"| EVAC_DISPATCH
        end

        subgraph POST_AUDIO["📝 Post-Audio Finalization"]
            direction TB
            APPROVAL["⏳ Await Operator Approval<br/><i>30-second timeout</i>"]
            DISPATCH_AGENT["📻 <b>Dispatch Agent</b><br/>Model: <code>mistral-large-latest</code><br/><i>Generate briefs per unit:</i><br/><i>AMB-7, ENG-4, PED-2, TC-3</i><br/><i>Tool: get_case_summary</i>"]
            DISPATCH_TTS["🔊 Generate Voice Briefs<br/>Model: <code>eleven_turbo_v2_5</code>"]
            SUMMARY["📄 Final Operator Summary"]
            APPROVAL --> DISPATCH_AGENT
            DISPATCH_AGENT --> DISPATCH_TTS
            DISPATCH_TTS --> SUMMARY
        end
    end

    COMMITTED --> RAW_INSERT
    PARTIAL --> LIVE_PARTIALS_DB
    FRAMES --> VISION_AGENT
    FUSION_BG --> EVAC_CHECK
    VISION_DELTA --> EVAC_CHECK
    DISPATCH_TTS -.->|"voice generation"| TTS
    EVAC_TTS -.->|"broadcast generation"| TTS

    %% ═══════════════════════════════════════════════════════════
    %% SUPABASE — Database + Realtime
    %% ═══════════════════════════════════════════════════════════
    subgraph SUPABASE["🗄️ Supabase <i>(PostgreSQL + Realtime WebSocket)</i>"]
        direction TB
        INCIDENT_STATE_DB[("📊 <b>incident_state</b><br/><i>status · severity · incident_type</i><br/><i>hazard_flags · vision_detections</i><br/><i>recommended_units · action_plan</i><br/><i>timeline · operator_summary</i>")]
        AGENT_LOGS_DB[("📝 <b>agent_logs</b><br/><i>agent · event_type · message</i><br/><i>data · display_color · flash</i><br/><i>model name</i>")]
        TRANSCRIPTS_DB[("💬 <b>transcripts</b><br/><i>caller_id · language</i><br/><i>original_text · translated_text</i><br/><i>feed_id · facts_extracted</i>")]
        DISPATCHES_DB[("🚑 <b>dispatches</b><br/><i>unit_type · unit_assigned</i><br/><i>eta_minutes · voice_message</i><br/><i>audio_url</i>")]
        LIVE_PARTIALS_DB[("⚡ <b>live_partials</b><br/><i>case_id PK · text</i><br/><i>upserted per case</i>")]
        DEMO_CONTROL_DB[("🎮 <b>demo_control</b><br/><i>status · video_url</i><br/><i>approve_enabled/clicked</i>")]
    end

    %% Orchestrator writes to Supabase
    RAW_INSERT -->|"INSERT"| TRANSCRIPTS_DB
    UI_PUSH -->|"UPDATE"| TRANSCRIPTS_DB
    TRIAGE -->|"UPDATE"| INCIDENT_STATE_DB
    TRIAGE -->|"INSERT"| AGENT_LOGS_DB
    FUSION_BG -->|"UPDATE"| INCIDENT_STATE_DB
    FUSION_BG -->|"INSERT"| AGENT_LOGS_DB
    VISION_DELTA -->|"UPDATE"| INCIDENT_STATE_DB
    VISION_AGENT -->|"INSERT"| AGENT_LOGS_DB
    INTAKE -->|"INSERT"| AGENT_LOGS_DB
    TRANSLATE -->|"INSERT"| AGENT_LOGS_DB
    DISPATCH_AGENT -->|"INSERT"| DISPATCHES_DB
    DISPATCH_AGENT -->|"INSERT"| AGENT_LOGS_DB
    EVAC_DISPATCH -->|"INSERT"| DISPATCHES_DB
    EVAC_TTS -->|"INSERT"| TRANSCRIPTS_DB
    SUMMARY -->|"UPDATE"| INCIDENT_STATE_DB

    %% ═══════════════════════════════════════════════════════════
    %% FRONTEND — Next.js + Supabase Realtime
    %% ═══════════════════════════════════════════════════════════
    subgraph FRONTEND["🖥️ Frontend <i>(Next.js · TypeScript · Supabase Realtime)</i>"]
        direction TB

        subgraph HOOKS["⚡ Real-Time Hooks"]
            direction LR
            HOOK_STATE["useIncidentState<br/><i>UPDATE events</i>"]
            HOOK_LOGS["useAgentLogs<br/><i>INSERT events</i>"]
            HOOK_TRANSCRIPTS["useTranscripts<br/><i>INSERT + UPDATE</i>"]
            HOOK_DISPATCHES["useDispatches<br/><i>INSERT events</i>"]
            HOOK_PARTIALS["useLivePartials<br/><i>UPDATE events</i>"]
        end

        subgraph UI_COMPONENTS["🎨 UI Components"]
            direction TB
            DASHBOARD["📊 <b>Dashboard</b><br/><i>3-column layout · elapsed timer</i><br/><i>INITIATE FEED · APPROVE buttons</i>"]
            CCTV["📹 <b>CCTVPanel</b><br/><i>Video player + CRT overlay</i><br/><i>Real vision detections</i><br/><i>Hazard indicators</i>"]
            TRANSCRIPT_UI["🎙️ <b>TranscriptPanel</b><br/><i>Live partials shimmer</i><br/><i>Committed transcripts</i><br/><i>Translations · language tags</i>"]
            AGENT_TERMINAL["💻 <b>AgentTerminal</b><br/><i>Scrolling agent logs</i><br/><i>Color-coded · flash alerts</i><br/><i>Cross-modal corroboration</i>"]
            CASE_FILE["📁 <b>CaseFilePanel</b><br/><i>Severity badge · units</i><br/><i>Hazard flags · action plan</i>"]
            RESPONSE["🚑 <b>ResponseLanes</b><br/><i>Dispatch cards · ETAs</i><br/><i>Audio playback</i>"]
        end
    end

    %% Supabase Realtime → Frontend Hooks
    INCIDENT_STATE_DB -.->|"Realtime UPDATE"| HOOK_STATE
    AGENT_LOGS_DB -.->|"Realtime INSERT"| HOOK_LOGS
    TRANSCRIPTS_DB -.->|"Realtime INSERT/UPDATE"| HOOK_TRANSCRIPTS
    DISPATCHES_DB -.->|"Realtime INSERT"| HOOK_DISPATCHES
    LIVE_PARTIALS_DB -.->|"Realtime UPDATE"| HOOK_PARTIALS

    %% Hooks → Components
    HOOK_STATE --> DASHBOARD
    HOOK_STATE --> CCTV
    HOOK_STATE --> CASE_FILE
    HOOK_LOGS --> AGENT_TERMINAL
    HOOK_TRANSCRIPTS --> TRANSCRIPT_UI
    HOOK_DISPATCHES --> RESPONSE
    HOOK_PARTIALS --> TRANSCRIPT_UI

    %% ═══════════════════════════════════════════════════════════
    %% STYLING
    %% ═══════════════════════════════════════════════════════════
    classDef sponsor fill:#4a1d96,stroke:#8b5cf6,stroke-width:3px,color:#e0e0e0
    classDef elevenlabs fill:#1a3a2a,stroke:#10b981,stroke-width:2px,color:#e0e0e0
    classDef mistral fill:#1e3a5f,stroke:#3b82f6,stroke-width:2px,color:#e0e0e0
    classDef supabase fill:#1a2e1a,stroke:#22c55e,stroke-width:2px,color:#e0e0e0
    classDef frontend fill:#2d1f3d,stroke:#a78bfa,stroke-width:2px,color:#e0e0e0
    classDef critical fill:#3d1f1f,stroke:#ef4444,stroke-width:2px,color:#e0e0e0
    classDef parallel fill:#1f2d3d,stroke:#38bdf8,stroke-width:2px,color:#e0e0e0
    classDef input fill:#2d2d1f,stroke:#eab308,stroke-width:2px,color:#e0e0e0

    class MISTRAL_SPONSOR,ELEVENLABS_SPONSOR sponsor
    class SCRIBE,TTS elevenlabs
    class TRANSLATE,INTAKE,TRIAGE,FUSION_BG,DISPATCH_AGENT,VISION_AGENT mistral
    class INCIDENT_STATE_DB,AGENT_LOGS_DB,TRANSCRIPTS_DB,DISPATCHES_DB,LIVE_PARTIALS_DB,DEMO_CONTROL_DB supabase
    class DASHBOARD,CCTV,TRANSCRIPT_UI,AGENT_TERMINAL,CASE_FILE,RESPONSE frontend
    class EVAC_CHECK,EVAC_TTS,EVAC_DISPATCH critical
    class PARALLEL_1 parallel
    class VIDEO,PCM,FRAMES input

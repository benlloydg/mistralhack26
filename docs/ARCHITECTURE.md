%%{init: {'theme': 'base', 'themeVariables': { 'primaryColor': '#0a0a0a', 'primaryTextColor': '#f8fafc', 'primaryBorderColor': '#334155', 'lineColor': '#475569', 'secondaryColor': '#1e293b', 'tertiaryColor': '#0f172a', 'clusterBkg': '#09090b', 'clusterBorder': '#27272a', 'fontSize': '13px', 'fontFamily': 'ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace' }}}%%
flowchart TB

    %% Styling Classes
    classDef sponsor fill:#1e1b4b,stroke:#a855f7,stroke-width:2px,color:#f8fafc
    classDef elevenlabs fill:#064e3b,stroke:#10b981,stroke-width:2px,color:#f8fafc
    classDef mistral fill:#1e3a8a,stroke:#3b82f6,stroke-width:2px,color:#f8fafc
    classDef supabase fill:#14532d,stroke:#22c55e,stroke-width:2px,color:#f8fafc
    classDef frontend fill:#4c1d95,stroke:#c084fc,stroke-width:2px,color:#f8fafc
    classDef critical fill:#7f1d1d,stroke:#ef4444,stroke-width:2px,color:#f8fafc
    classDef parallel fill:#0f172a,stroke:#38bdf8,stroke-width:2px,color:#f8fafc
    classDef input fill:#422006,stroke:#eab308,stroke-width:2px,color:#f8fafc
    classDef orchestrator fill:#18181b,stroke:#52525b,stroke-width:1px,color:#e4e4e7
    classDef internaldb fill:#27272a,stroke:#52525b,stroke-width:1px,color:#f8fafc

    %% SPONSORS
    subgraph SPONSORS["Hackathon Core Technologies"]
        direction LR
        MISTRAL_SPONSOR["Mistral AI<br/>LLM Reasoning and<br/>Vision Analysis"]:::sponsor
        ELEVENLABS_SPONSOR["ElevenLabs<br/>Real-Time Scribe and<br/>TTS Generation"]:::sponsor
    end

    %% INPUT
    subgraph INPUT["Input Layer"]
        direction LR
        VIDEO["CCTV Video File<br/>scene.mp4"]:::input
        PCM["Raw PCM Audio<br/>16kHz mono"]:::input
        FRAMES["Video Frames<br/>JPEG extraction"]:::input
        VIDEO -.->|"ffmpeg extraction"| PCM
        VIDEO -.->|"ffmpeg extraction"| FRAMES
    end

    %% ELEVENLABS
    subgraph ELEVENLABS["ElevenLabs Edge API"]
        direction TB
        SCRIBE["Scribe v2 Realtime<br/>scribe_v2_realtime<br/>VAD and core transcription"]:::elevenlabs
        TTS["Text-to-Speech<br/>eleven_turbo_v2_5<br/>Voice synthesis"]:::elevenlabs
    end

    %% CORE ORCHESTRATOR
    subgraph ORCHESTRATOR["Event-Driven Orchestrator (FastAPI / Python)"]
        direction TB

        PARTIAL["Live Partial<br/>UI shimmer"]:::orchestrator
        COMMITTED["Committed Transcript<br/>Language inference"]:::orchestrator

        subgraph AUDIO_PIPELINE["Audio Reasoning Pipeline"]
            direction TB
            RAW_INSERT["1. Ingest Transcript"]:::orchestrator
            PARALLEL_1["Parallel Processing<br/>Translate and intake extract"]:::parallel
            TRIAGE["Triage Agent<br/>Generates action plan"]:::mistral
            FUSION_BG["Evidence Fusion Agent<br/>Cross-modal corroboration"]:::mistral

            RAW_INSERT --> PARALLEL_1 --> TRIAGE
            TRIAGE -.->|"deferred background task"| FUSION_BG
        end

        subgraph VISION_PIPELINE["Vision Analysis Pipeline"]
            direction TB
            VISION_AGENT["Vision Agent<br/>Pixtral Large"]:::mistral
            VISION_DELTA["Scene Delta<br/>Detect hazard escalation"]:::orchestrator
            VISION_AGENT --> VISION_DELTA
        end

        subgraph ACTIONS["Escalation Protocols"]
            direction TB
            EVAC_CHECK{"Hazard and People?"}:::critical
            EVAC_DISPATCH["Auto-Dispatch<br/>Expedited fire unit"]:::critical
            EVAC_TTS["Broadcast Warning<br/>EN, ES, ZH, FR"]:::critical

            EVAC_CHECK -->|"Triggered"| EVAC_DISPATCH
            EVAC_CHECK -->|"Triggered"| EVAC_TTS
        end

        subgraph TERMINAL["Final Resolution Phase"]
            direction LR
            APPROVAL["User Approve"]:::orchestrator
            DISPATCH_AGENT["Dispatch Agent<br/>Unit summaries"]:::mistral
            SUMMARY["Operator Summary"]:::orchestrator

            APPROVAL --> DISPATCH_AGENT --> SUMMARY
        end

        FUSION_BG --> EVAC_CHECK
        VISION_DELTA --> EVAC_CHECK
    end

    PCM ==>|"100ms chunks (WebSocket)"| SCRIBE
    FRAMES ==>|"Base64 images"| VISION_AGENT
    SCRIBE -->|"Speech ongoing"| PARTIAL
    SCRIBE -->|"Speech paused"| COMMITTED
    COMMITTED --> RAW_INSERT
    EVAC_TTS -.->|"generate audio payload"| TTS
    DISPATCH_AGENT -.->|"generate audio payload"| TTS

    %% DATABASE
    subgraph SUPABASE["Supabase Cloud (PostgreSQL)"]
        direction LR
        DB_STATE[("incident_state")]:::internaldb
        DB_LOGS[("agent_logs")]:::internaldb
        DB_TRANSCRIPTS[("transcripts")]:::internaldb
        DB_DISPATCHES[("dispatches")]:::internaldb
        DB_RT["Realtime API<br/>postgres_changes"]:::supabase
    end

    %% DB Connections
    RAW_INSERT -.->|"INSERT"| DB_TRANSCRIPTS
    TRIAGE -.->|"UPDATE"| DB_STATE
    VISION_DELTA -.->|"UPDATE"| DB_STATE
    TRIAGE -.->|"INSERT"| DB_LOGS
    VISION_AGENT -.->|"INSERT"| DB_LOGS
    DISPATCH_AGENT -.->|"INSERT"| DB_DISPATCHES
    FUSION_BG -.->|"INSERT"| DB_LOGS

    %% FRONTEND
    subgraph FRONTEND["Next.js + Tailwind Dashboard"]
        direction TB
        HOOKS["Realtime Connectors<br/>Supabase WebSockets"]:::frontend
        UI["Palantir-Style Data Canvas<br/>CCTVPanel, AgentTerminal, etc."]:::frontend
        HOOKS --> UI
    end

    DB_RT ==>|"postgres_changes (WebSockets)"| HOOKS
    PARTIAL -.->|"Live local state"| UI
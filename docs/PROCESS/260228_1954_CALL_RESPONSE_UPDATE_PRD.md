Three separate questions here. Let me take them in priority order.

**ElevenLabs voice responses — yes, this needs to happen.**

This is a scoring gap. You're competing for the ElevenLabs track and right now ElevenLabs is only doing transcription (input). You need it doing voice output too. The PRD already specifies this — the orchestrator has phases where it generates multilingual voice responses and evacuation warnings in Spanish and Mandarin via ElevenLabs TTS. The VOICE_MAP is already defined in your codebase (es, zh, fr, en mapped to ElevenLabs voice IDs).

What this looks like in the demo: after the system triages and the operator approves, an audio clip plays — ElevenLabs speaking Spanish to Caller 1 confirming help is on the way. Later, when fire is detected, priority interrupt evacuation warnings play in both Spanish and Mandarin. The transcript panel should show these outbound messages too, styled differently from inbound caller messages — maybe right-aligned or with a "DISPATCH →" prefix and a speaker icon.

This is what turns ElevenLabs from "we used their transcription API" into "we built a full multilingual voice loop — callers speak in their language, the system understands, reasons, and responds in their language." That's the demo moment that wins the ElevenLabs prize. The TTS calls are already in your service layer. They just need to be wired into the orchestrator and surfaced in the UI with an audio player.

Tell your UI dev to add a small speaker icon or audio waveform indicator in the transcript panel when an outbound voice response is sent. Something like:

```
[03:34:02] DISPATCH → CALLER 1 (ES)  🔊 Playing
"Ayuda está en camino. Manténgase en la línea."
  ── Translation ──
"Help is on the way. Stay on the line."
```

**Demo selection and reset — yes, but keep it simple.**

Don't build a whole demo management UI. Here's what you actually need:

Add a pre-demo screen — a clean landing page that shows before the demo starts. The DISPATCH logo centered, the tagline "INCIDENT INTELLIGENCE SYSTEM," and either a single START DEMO button or 2–3 scenario cards if you go multi-demo. Something like:

```
┌──────────────────────────────────────────┐
│                                          │
│            ● DISPATCH                    │
│    Incident Intelligence System          │
│                                          │
│  ┌────────────┐  ┌────────────┐          │
│  │ SCENARIO 1 │  │ SCENARIO 2 │          │
│  │ Vehicle    │  │ Industrial │          │
│  │ Collision  │  │ Fire       │          │
│  │ 3 callers  │  │ 2 callers  │          │
│  │ ES/ZH/FR   │  │ EN/ES      │          │
│  └────────────┘  └────────────┘          │
│                                          │
└──────────────────────────────────────────┘
```

Each scenario card hits a different endpoint: `POST /demo/start?scenario=vehicle_collision`. The orchestrator loads different audio files, video, and scripted sequences per scenario. The backend clears the previous case state and creates a fresh incident. The frontend resets all panels to empty and begins subscribing.

But honestly — **focus on one demo and make it flawless.** Having two half-polished demos is worse than one that runs perfectly. The second scenario is a safety net in case you need to run the demo again (judges sometimes ask "can you run that again?"), not a feature to show off. If you have time after the primary demo is perfect, then build a second scenario.

**Run log and report page — yes, and this is a sneaky high-value feature.**

After the demo completes, generate a shareable report at a clean URL like `dispatch.app/cases/TN-2026-00417`. This page should show the final frozen state of the case: full timeline of every event with timestamps, all transcript segments with translations, all vision detections with frame captures, every severity change with the reasoning, every dispatch with confirmation status, and the final action plan.

This is valuable for three reasons. First, judges can pull it up on their own laptops after your demo and examine it closely — you give them the URL on your submission page and they can poke around. Second, it proves the audit trail story from your pitch — "full decision traceability." Third, it's a beautiful artifact for your portfolio and Twitter.

The implementation is straightforward: it's a read-only Next.js page that queries the frozen incident_state, agent_logs, transcripts, and dispatches tables for a given case_id and renders them in a clean, scrollable report format. No real-time subscriptions needed — it's just a static read of the final state. Style it like a professional after-action report.

**Priority order for the next work block:**

First, wire ElevenLabs TTS responses into the orchestrator and surface them in the transcript panel. This directly impacts scoring on the ElevenLabs track and it's already half-built in your codebase.

Second, build the pre-demo landing screen with a START button and a reset flow. You need this to demo cleanly.

Third, if there's time, build the post-demo report page. It's high-impact for judges and portfolio but it doesn't block the live demo.

Fourth, a second scenario only if everything else is polished and rehearsed.
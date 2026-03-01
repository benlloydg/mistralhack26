# TriageNet — Hackathon Operating Guide

> 4:00 PM Saturday → 1:00 PM Sunday
> 21 hours. ~14 working. You will sleep.

---

## The Rule

Claude Code builds. You unblock.

Your job is not to write code. Your job is:
- Set up accounts and get API keys
- Run tests and report results back to Claude Code
- Make creative decisions Claude can't make (voice selection, UI feel, video timing)
- Create the demo assets (audio files, video clip)
- Rehearse the demo

---

## Hour-by-Hour Schedule

### BLOCK 1 — Foundation (4:00 PM – 6:30 PM)

| Time | Claude Code Does | You Do |
|------|-----------------|--------|
| 4:00 | — | **Create Supabase project.** Go to supabase.com → New Project. Copy URL + anon key + service role key. |
| 4:05 | — | **Get Mistral API key.** Go to console.mistral.ai → API Keys. Copy it. |
| 4:10 | — | **Get ElevenLabs API key.** Go to elevenlabs.io → Profile → API Key. Copy it. |
| 4:15 | — | **Create `.env` files** in both `/apps/server/.env` and `/apps/web/.env.local` with all keys. |
| 4:20 | Scaffold repo structure, install deps | Paste the Technical PRD into Claude Code. Say: "Read this PRD. Build Phase 1 — models and config. Run the tests." |
| 4:40 | Phase 1 tests passing | Review test output. Green? Say: "Phase 2 — Supabase migrations and state manager." |
| 4:45 | Runs migrations, builds state.py | **Run migrations yourself in Supabase SQL editor** if Claude Code can't connect directly. Copy SQL from the PRD's migration files and paste into Supabase dashboard → SQL Editor → Run. |
| 5:00 | Phase 2 tests passing | **Verify Realtime is enabled.** Supabase dashboard → Database → Replication → Check all 4 tables are listed (incident_state, agent_logs, transcripts, dispatches). Toggle them on if not. |
| 5:10 | Phase 3 — Mistral API tests | Watch latency numbers. If any call > 5s, note it. |
| 5:30 | Phase 4 — ElevenLabs tests | Watch latency numbers. TTS should be < 3s. |
| 5:45 | Phase 3+4 passing | Say: "Phase 5 — build all Pydantic-AI agents. Run the tests." |
| 6:30 | Phase 5 tests passing | **CHECKPOINT 1: All APIs proven, all agents return typed outputs.** |

**If Phase 5 tests fail:** The most likely failure is Pydantic-AI not parsing Mistral's structured output correctly. Tell Claude Code to add `max_retries=2` on the agent and check the error message. If it's a schema mismatch, simplify the output model (fewer optional fields).

---

### BLOCK 2 — Demo Assets (6:30 PM – 7:30 PM)

> **This is YOUR work. Claude Code can't do this.**

| Task | How | Time |
|------|-----|------|
| **Record caller_1_spanish.mp3** | Use ElevenLabs Speech → Spanish female voice → "¡Ayuda! Ha habido un accidente terrible en Market y la Quinta. ¡Mi esposo está atrapado en el coche! Por favor, envíen ayuda rápido." → Download MP3 | 10 min |
| **Record caller_2_mandarin.mp3** | Use ElevenLabs Speech → Chinese voice → "我在Market街看到了车祸！后座有一个小孩！请快派人来！" → Download MP3 | 10 min |
| **Record caller_3_french.mp3** | Use ElevenLabs Speech → French voice → "Il y a de la fumée qui sort de la voiture accidentée devant ma boutique, à l'angle de Market et de la Cinquième!" → Download MP3 | 10 min |
| **Get crash_video.mp4** | Option A: Find a royalty-free dashcam/CCTV crash clip on Pexels or Pixabay (search "car accident CCTV"). Option B: Use a still image and Claude Code can loop it as video. Either way, it needs to show: a crashed car, then smoke, then visible fire/flames. Even a 15-second clip works — the orchestrator extracts specific frames. | 20 min |
| **Place files** | Copy all 4 files into `/apps/server/assets/` | 2 min |

**Pro tip:** For the video, a short clip is fine. The vision agent analyzes individual frames, not video. If you can't find one with fire progression, use TWO still images — one of a crash, one of a car fire — and Claude Code can extract them as "frame 1" and "frame 2".

---

### BLOCK 3 — Orchestrator + Backend Complete (7:30 PM – 9:30 PM)

| Time | Claude Code Does | You Do |
|------|-----------------|--------|
| 7:30 | Phase 6 — orchestrator, routes, main.py | Say: "Phase 6 — build the orchestrator, routes, and main.py. The media assets are in /apps/server/assets/. Run the server and hit /health." |
| 8:00 | Server running, /health returns green | **Test it yourself.** Open terminal: `curl http://localhost:8000/api/v1/health`. All checks should say "ok". |
| 8:15 | — | **Run the demo once.** `curl -X POST http://localhost:8000/api/v1/demo/start` then watch Supabase dashboard → Table Editor → incident_state. You should see the row updating in real time. |
| 8:20 | — | After ~20s, approve: `curl -X POST http://localhost:8000/api/v1/demo/approve` |
| 8:30 | Debug any orchestrator issues | **Watch the agent_logs table in Supabase.** Are entries appearing? Are they in order? Note any gaps. |
| 9:00 | Phase 6 tests passing | **CHECKPOINT 2: Full backend works. Demo runs start-to-finish. State updates correctly.** |
| 9:15 | Run full e2e test | Watch timing. The whole sequence should complete in roughly 2 minutes. If it's taking 4+ minutes, the Mistral calls are stacking up — tell Claude Code to add caching or reduce agent calls. |
| 9:30 | Backend locked | **Take a break. Eat something. You're ahead of schedule.** |

---

### BLOCK 4 — Frontend (9:30 PM – 12:00 AM)

| Time | Claude Code Does | You Do |
|------|-----------------|--------|
| 9:30 | Phase 7 — Next.js scaffold, layout, theme | Say: "Phase 7 — build the frontend. Start with the layout, theme (dark/light), and Supabase client. Then build useIncidentState hook first — I want to see state updates in the browser before we build any panels." |
| 10:00 | Basic page rendering with realtime state | **Open http://localhost:3000 in browser.** Start a demo from the backend. Do you see ANY data updating on screen? Even raw JSON is fine. This proves the Supabase Realtime pipeline works end-to-end. |
| 10:15 | AgentTerminal component | **This is the most important panel.** It should show colored log entries appearing in real time. If this works, everything else is UI polish. |
| 10:45 | CaseFilePanel, SeverityBadge | Watch severity badge animate when it changes. |
| 11:00 | TranscriptPanel with caller tabs | Each caller should get a tab. Text appears in original language. |
| 11:15 | ResponseLanes (dispatch cards) | Cards should show Recommended → Confirmed state transitions. |
| 11:30 | ActionButton (START DEMO / APPROVE) | **Click START DEMO in the browser.** Then click APPROVE when prompted. This is the full flow. |
| 11:45 | CCTVPanel (video + overlay) | The video plays. Red flash when fire detected. |
| 12:00 | — | **CHECKPOINT 3: Full demo runs in the browser. All panels update.** |

**If Supabase Realtime isn't working in the frontend:** This is the #1 risk. Check:
1. `.env.local` has the correct `NEXT_PUBLIC_SUPABASE_URL` and `NEXT_PUBLIC_SUPABASE_ANON_KEY`
2. Realtime is enabled on all 4 tables in Supabase dashboard
3. The Supabase client is using the anon key (not service key) in the frontend
4. Row Level Security (RLS) — either disable it on all tables for the hackathon, or add a policy allowing `SELECT` for `anon` role

**To disable RLS quickly (fine for hackathon):**
```sql
ALTER TABLE incident_state DISABLE ROW LEVEL SECURITY;
ALTER TABLE agent_logs DISABLE ROW LEVEL SECURITY;
ALTER TABLE transcripts DISABLE ROW LEVEL SECURITY;
ALTER TABLE dispatches DISABLE ROW LEVEL SECURITY;
```

---

### BLOCK 5 — Sleep (12:00 AM – 7:00 AM)

**Sleep.** Seriously.

Before bed:
- Run the full demo one more time
- Note what's broken or ugly
- Write 3 bullet points for Claude Code to fix in the morning
- Set alarm for 7:00 AM

The demo works. It will still work at 7 AM.

---

### BLOCK 6 — Polish (7:00 AM – 10:00 AM)

| Time | Claude Code Does | You Do |
|------|-----------------|--------|
| 7:00 | Fix the 3 things from last night | Coffee. Review overnight notes. |
| 7:30 | UI animations — flash effects, severity pulse, smooth scrolls | **Pick the dark mode color palette.** Should the fire detection flash be red? Orange? How long should it pulse? These are feel decisions. |
| 8:00 | Loading states, error boundaries | Run the demo and look for ugly moments — blank screens, janky transitions, text overflow |
| 8:30 | Typography and spacing polish | **Screenshot everything.** You'll want these for the submission. |
| 9:00 | — | **Full dress rehearsal #1.** Run the complete demo. Time it. It should be ~2 minutes. |
| 9:15 | Fix issues from rehearsal | Note anything that felt wrong. |
| 9:30 | — | **Full dress rehearsal #2.** This one should be smooth. |
| 9:45 | Final fixes | — |
| 10:00 | — | **CHECKPOINT 4: Demo is polished and rehearsed.** |

---

### BLOCK 7 — Submission Prep (10:00 AM – 1:00 PM)

| Time | You Do |
|------|--------|
| 10:00 | **Write the submission description.** 3 paragraphs: What it does, how it works, why it matters. Mention: multi-caller, multilingual, Mistral vision + reasoning, ElevenLabs voice agents, real-time corroboration, human-in-the-loop. |
| 10:30 | **Record the demo video.** Screen record the full 2-minute demo with voiceover. Use OBS or Loom. Record at 1080p minimum. |
| 11:00 | **Watch the recording.** Does it make sense to someone who hasn't seen it before? Re-record if needed. |
| 11:30 | **Take screenshots** for the submission gallery. Key moments: initial state, severity escalation, fire detection, corroboration event, final summary. |
| 12:00 | **Write the README.** Quick setup instructions, tech stack list, architecture diagram (even ASCII art). |
| 12:30 | **Final test.** One more demo run. Everything works. |
| 1:00 | **DONE.** Submission ready. |

---

## Quick-Reference Troubleshooting

| Problem | Fix |
|---------|-----|
| Mistral calls > 5s | Switch triage to `mistral-medium-latest` (faster, cheaper, still good) |
| Pydantic-AI structured output fails | Add `max_retries=3` to agent. Simplify output model if needed. |
| Supabase Realtime not firing | Check RLS is disabled. Check Realtime enabled on tables. Check anon key. |
| ElevenLabs voice sounds wrong | Change voice ID in `tts.py`. Browse voices at elevenlabs.io/voice-library. |
| Demo takes > 3 minutes | Reduce `asyncio.sleep()` pauses. Run triage fewer times. Cache repeated calls. |
| Vision returns garbage | Use a clearer frame. Add more explicit JSON format instructions in the vision prompt. |
| Frontend blank on load | Check CORS in main.py includes `http://localhost:3000`. Check Supabase URL in `.env.local`. |
| Demo crashes mid-run | Check server logs. Most likely: unhandled API error from Mistral/ElevenLabs. Wrap in try/except with fallback state update. |

---

## What Specifically YOU Do (Not Claude Code)

| # | Task | When | Why Claude Code Can't |
|---|------|------|-----------------------|
| 1 | Create Supabase project | 4:00 PM | Needs your browser/account |
| 2 | Get API keys (Mistral, ElevenLabs) | 4:05 PM | Needs your accounts |
| 3 | Write .env files | 4:15 PM | Has your secrets |
| 4 | Enable Realtime in Supabase dashboard | 5:00 PM | UI-only setting |
| 5 | Disable RLS on tables | 5:00 PM | Dashboard or SQL editor |
| 6 | Record 3 caller audio files via ElevenLabs | 6:30 PM | Creative + account access |
| 7 | Find/download crash video clip | 7:00 PM | Creative judgment |
| 8 | Test /health endpoint manually | 8:00 PM | Sanity check |
| 9 | Watch demo in Supabase table editor | 8:15 PM | Visual verification |
| 10 | Click APPROVE during demo runs | Every run | The human-in-the-loop IS you |
| 11 | Pick color palette / animation feel | 7:30 AM | Aesthetic judgment |
| 12 | Run dress rehearsals and time them | 9:00 AM | Judgment call |
| 13 | Record demo video for submission | 10:30 AM | Voiceover + screen recording |
| 14 | Write submission description | 10:00 AM | Narrative storytelling |
| 15 | Write README | 12:00 PM | Project context |

Everything else? Claude Code.

---

## The Three Things That Will Break

I'm telling you now so you're not surprised.

**1. Supabase Realtime will be silent on first try.** It's always RLS or the table not being added to the realtime publication. Disable RLS. Run migration 005. Check the dashboard. This will cost you 15 minutes.

**2. One Mistral agent call will be slow.** The triage agent with tools has to make 2-3 round trips (call tool → get result → call tool → get result → final answer). This can take 4-8 seconds. That's fine for the demo — the frontend is updating continuously from other agents while triage thinks. But if the TOTAL demo exceeds 3 minutes, reduce triage to a single-shot call without tools (pass all context in the prompt instead).

**3. The video frame extraction will need tuning.** The orchestrator extracts frames at hardcoded timestamps (58s, 66s). If your video clip is shorter, those timestamps are wrong. Tell Claude Code the actual duration and which seconds show smoke vs fire. This is a 2-minute fix once you have the actual video.

---

## If Everything Goes Wrong

Absolute worst case — it's 11 AM Sunday and the frontend doesn't work:

**Fallback plan:** Demo from the terminal + Supabase dashboard.

1. Split screen: terminal on left, Supabase table editor on right
2. `curl -X POST http://localhost:8000/api/v1/demo/start`
3. Watch incident_state row update in real time in Supabase
4. Click APPROVE via curl
5. Narrate what's happening as the data changes

This still shows: multi-caller processing, multilingual transcription, Mistral reasoning, real-time state evolution, human approval, vision detection, evidence fusion. It just shows it as raw data instead of a polished dashboard. Judges who understand engineering will still be impressed.

You won't need this fallback. But knowing it exists means you won't panic.

---

*Now go build it. Phase 1 starts at 4:20 PM.*
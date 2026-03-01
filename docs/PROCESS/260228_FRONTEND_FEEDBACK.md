# Frontend Feedback — Connecting to Backend & Supabase Realtime

> **For**: Gemini agent working on `apps/web/`
> **From**: Backend analysis of `apps/server/`
> **Date**: 2026-02-28

---

## Summary

The frontend is well-structured. Supabase Realtime hooks are correctly implemented with proper channel subscriptions and cleanup. There are **4 specific issues** to fix before the frontend will connect to the live backend.

---

## Issue 1: Case ID Must Come From Backend (CRITICAL)

**Current** (Dashboard.tsx line 15):
```ts
const DEMO_CASE_ID = 'DEMO-SF-2024-001'
```

**Required**: The case ID is now **dynamic** — each demo run generates a unique ID like `TN-20260228-214532`. The frontend must:

1. Call `POST /api/v1/demo/start` and read `case_id` from the response:
```ts
const res = await fetch('http://localhost:8000/api/v1/demo/start', { method: 'POST' });
const { case_id } = await res.json();
// Use this case_id for all Supabase subscriptions
```

2. Store the `case_id` in React state and pass it to all hooks:
```ts
const [caseId, setCaseId] = useState<string | null>(null);
// After start: setCaseId(case_id)
// Pass to hooks: useIncidentState(caseId), useAgentLogs(caseId), etc.
```

All Supabase Realtime subscriptions filter by `case_id`, so using the wrong ID means zero data flows.

---

## Issue 2: API Endpoint Paths (CRITICAL)

**Current** (Dashboard.tsx):
```ts
fetch('http://localhost:8000/api/demo/start', { method: 'POST' })
fetch('http://localhost:8000/api/demo/approve', { method: 'POST' })
```

**Required**:
```ts
fetch('http://localhost:8000/api/v1/demo/start', { method: 'POST' })
fetch('http://localhost:8000/api/v1/demo/approve', { method: 'POST' })
```

The backend mounts routers under `/api/v1` prefix (see `src/main.py` lines 15-16). Missing `/v1/` causes 404 errors.

Also add a status endpoint call if needed:
```ts
fetch('http://localhost:8000/api/v1/demo/status')
```

---

## Issue 3: Missing `.env.local` File (CRITICAL)

Create `apps/web/.env.local` with:
```env
NEXT_PUBLIC_SUPABASE_URL=<your-supabase-url>
NEXT_PUBLIC_SUPABASE_ANON_KEY=<your-supabase-anon-key>
```

Without this, the Supabase client falls back to placeholder values and nothing connects.

---

## Issue 4: CCTV Panel — Use Real Vision Detections (ENHANCEMENT)

**Current**: CCTVPanel.tsx has hardcoded simulated detections (PERSON 95%, VEHICLE 88%).

**What the backend provides**: The `incident_state` row has a `vision_detections` array field that gets populated during Phase 4 (0:56-1:18) of the demo. The orchestrator writes detections like:

```json
[
  {"label": "smoke", "confidence": 0.87, "source": "pixtral_frame_58s"},
  {"label": "fire", "confidence": 0.92, "source": "pixtral_frame_66s"}
]
```

**Recommended change**: Read `vision_detections` from the `incidentState` prop (which already comes from the `useIncidentState` hook) and render real detections instead of hardcoded ones. Keep the simulated detections as fallback when the array is empty.

---

## What's Already Correct (No Changes Needed)

### Supabase Realtime Hooks ✓
All 4 hooks are correctly implemented:

| Hook | Table | Event | Filter | Channel |
|------|-------|-------|--------|---------|
| `useIncidentState` | `incident_state` | `UPDATE` | `case_id=eq.{caseId}` | `incident_{caseId}` |
| `useAgentLogs` | `agent_logs` | `INSERT` | `case_id=eq.{caseId}` | `logs_{caseId}` |
| `useTranscripts` | `transcripts` | `INSERT` | `case_id=eq.{caseId}` | `transcripts_{caseId}` |
| `useDispatches` | `dispatches` | `INSERT` | `case_id=eq.{caseId}` | `dispatches_{caseId}` |

### Type Definitions ✓
The `types.ts` interfaces match the backend Pydantic models:
- `IncidentState` — matches `src/models/incident.py`
- `AgentLog` — matches `src/models/events.py`
- `Transcript` — matches `src/models/caller.py` + orchestrator insert fields
- `Dispatch` — matches `src/models/dispatch.py`

### Status Enums ✓
- `IncidentStatus`: `intake → active → escalated → critical → resolved_demo`
- `Severity`: `unknown → low → medium → high → critical`

### Component Architecture ✓
All panels correctly consume hook data and will animate on Realtime updates.

---

## Backend Data Flow Reference

During the 120-second demo, the backend writes to Supabase in this order:

| Time | Table | What Gets Written |
|------|-------|-------------------|
| 0:00 | `incident_state` | Initial row (status: `intake`) |
| 0:00 | `agent_logs` | Init event |
| 0:12 | `transcripts` | Caller 1 Spanish transcript |
| 0:12 | `agent_logs` | transcript_received, facts_extracted |
| 0:12 | `incident_state` | Updated with location, severity → `active` |
| 0:30 | `agent_logs` | awaiting_approval |
| 0:30 | `dispatches` | Recommended units (EMS, Engine) |
| 0:38 | `transcripts` | Caller 2 Mandarin transcript |
| 0:38 | `agent_logs` | case_match, severity_changed |
| 0:38 | `incident_state` | Severity escalated → `escalated`, child present |
| 0:56 | `transcripts` | Caller 3 French transcript |
| 0:58 | `incident_state` | vision_detections updated (smoke) |
| 1:06 | `incident_state` | vision_detections updated (fire), status → `critical` |
| 1:18 | `dispatches` | Fire response units |
| 1:36 | `incident_state` | Final summary, status → `resolved_demo` |

The frontend hooks will receive all these updates automatically via Supabase Realtime once the case ID is corrected.

---

## New API Endpoints (for case history & reports)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/demo/start` | POST | Returns `{ case_id, status }` — use this case_id for subscriptions |
| `/api/v1/demo/approve` | POST | Unblocks dispatch phase |
| `/api/v1/demo/status` | GET | Current active demo state |
| `/api/v1/demo/reset` | POST | Stop active demo (data preserved) |
| `/api/v1/demo/cases` | GET | List all past runs, newest first |
| `/api/v1/demo/cases/{case_id}` | GET | Full report: state + logs + transcripts + dispatches |

The `/cases/{case_id}` endpoint is designed for the post-demo report page — a read-only view of a completed case.

---

## Outbound Dispatch Transcripts

The `transcripts` table now includes **outbound dispatch messages** with:
- `caller_id = "dispatch"` and `caller_label = "DISPATCH"`
- These should be styled differently from inbound caller messages (right-aligned, "DISPATCH →" prefix)
- The `agent_logs` data field may contain `audio_url` for TTS playback

---

## Quick Fix Checklist

- [ ] Get `case_id` dynamically from `POST /api/v1/demo/start` response (not hardcoded)
- [ ] Change API URLs from `/api/demo/` to `/api/v1/demo/`
- [ ] Create `.env.local` with Supabase credentials
- [ ] Style outbound transcripts (caller_id="dispatch") differently from inbound
- [ ] (Optional) Replace hardcoded CCTV detections with real `vision_detections` from state
- [ ] (Optional) Build post-demo report page using `GET /api/v1/demo/cases/{case_id}`

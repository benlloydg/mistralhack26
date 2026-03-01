# CLAUDE.md

## Spec-Driven Development (MANDATORY)

This project uses [GitHub Spec Kit](https://github.com/github/spec-kit) for spec-driven development.

**For every new feature**, you MUST follow the spec-kit workflow before writing any implementation code:

1. `/speckit.specify` - Define requirements (what and why)
2. `/speckit.plan` - Create technical implementation plan
3. `/speckit.tasks` - Generate actionable task breakdown
4. `/speckit.implement` - Execute implementation

Optional quality gates (use when appropriate):
- `/speckit.clarify` - Resolve ambiguous specs before planning
- `/speckit.analyze` - Cross-artifact consistency check after tasks
- `/speckit.checklist` - Validate requirements completeness

## Project Structure

```
/docs              - Documentation
/apps              - All applications
/apps/web          - Next.js frontend (App Router, TypeScript)
/apps/server       - Python backend (FastAPI, uv)
```

## Tech Stack

### Frontend (apps/web)
- Next.js + App Router
- TypeScript (strict)
- Global themes: light/dark mode, global styles
- Apple-level polish
- Supabase Realtime subscriptions for live data

### Backend (apps/server)
- Python with uv package manager
- FastAPI
- dotenv for env config
- pydantic-ai agents (deps, tools, structured outputs)
- Orchestrator + sub-agents architecture

### Database & Realtime
- Supabase as the backend database
- Agents write to Supabase
- Frontend reacts via Supabase Realtime

## Git Workflow (Hackathon Mode)
- Work directly on `main` — no feature branches
- Commit after each feature passes tests
- Spec-kit is used for planning only (spec.md, plan.md, tasks.md) — skip branch creation
- One commit per feature: `feat(NNN): description`

## Execution Speed
- Always use sub-agents to speed things up when applicable
- Parallelize independent file creation and independent tasks

## Testing Requirements
- Every feature MUST have E2E tests with timestamps/timing for each step
- Tests print elapsed time per operation (e.g., `[00:02.3s] Supabase write completed`)
- Tests print total elapsed time summary at the end
- Every feature MUST include user testing instructions (step-by-step manual verification guide)
- After each feature is implemented, run all its tests and save logs to `apps/server/test-results/`
- Log naming: `YYYYMMDD_HHMMSS_<phase>_<name>.log` (e.g., `20260228_181041_phase5_agents.log`)
- Test results are committed with the feature for grounding/traceability

## Pydantic-AI Reference
- All pydantic-ai agents MUST follow `docs/MASTER/PYDANTIC_AI_DOCS.md` — this is the authoritative API reference
- Use `result.output` (NOT `result.data`), `@agent.tool` with `RunContext`, and `Agent(model, deps_type=..., output_type=...)`

## Constitution
See `.specify/memory/constitution.md` for project principles and governance.

## Active Technologies
- Python 3.12 + FastAPI 0.115+, pydantic 2.10+, pydantic-settings 2.6+, pydantic-ai[mistral] 0.2+, mistralai 1.12+, supabase 2.11+, httpx 0.28+, python-dotenv 1.0+, elevenlabs 2.37+ (001-backend-foundation, 001-scribe-v2)
- Supabase (Postgres + Realtime) — 6 tables: incident_state, agent_logs, transcripts, dispatches, live_partials, demo_control (001-scribe-v2)

## Recent Changes
- 001-backend-foundation: Added Python 3.12 + FastAPI 0.115+, pydantic 2.10+, pydantic-settings 2.6+, pydantic-ai[mistral] 0.2+, mistralai 1.12+, supabase 2.11+, httpx 0.28+, python-dotenv 1.0+
- 001-scribe-v2-realtime: Added elevenlabs 2.37+ (Scribe v2 Realtime WebSocket), event-driven orchestrator, PCM audio extraction, Mistral translation, live_partials + demo_control tables

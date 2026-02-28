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

## Constitution
See `.specify/memory/constitution.md` for project principles and governance.

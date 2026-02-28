# Mistralhack26 Constitution

## Core Principles

### I. Spec-Driven Development
Every new feature MUST go through the spec-kit workflow before implementation:
1. `/speckit.constitution` - Review project principles
2. `/speckit.specify` - Define requirements (the "what" and "why")
3. `/speckit.plan` - Create technical implementation plan
4. `/speckit.tasks` - Generate actionable task breakdown
5. `/speckit.implement` - Execute implementation

### II. Repository Structure
```
/docs              - Documentation
/apps              - All applications
/apps/web          - Next.js frontend (App Router, TypeScript)
/apps/server       - Python backend (FastAPI, uv)
```

### III. Frontend Stack (apps/web)
- **Framework**: Next.js with App Router
- **Language**: TypeScript (strict)
- **Styling**: Global themes with light/dark mode support, global styles
- **Design**: Apple-level polish and attention to detail
- **Realtime**: Supabase Realtime subscriptions for live data

### IV. Backend Stack (apps/server)
- **Runtime**: Python with uv package manager
- **Framework**: FastAPI
- **Configuration**: dotenv for environment variables
- **AI Agents**: pydantic-ai with structured outputs, deps, and tools
- **Agent Architecture**: Orchestrator + sub-agents pattern
- **Database**: Supabase (agents write to Supabase)

### V. Architecture Pattern
- Backend agents write data to Supabase
- Frontend reads and reacts to Supabase Realtime
- Agents use pydantic-ai with dependencies, tools, structured outputs
- Orchestrator agent delegates to specialized sub-agents

### VI. Test-First
- Tests written before implementation where practical
- Red-Green-Refactor cycle encouraged

### VII. Simplicity
- Start simple, follow YAGNI principles
- No premature abstractions
- Minimum complexity needed for the current task

## Governance
- Constitution supersedes all other practices
- Amendments require documentation and approval

**Version**: 1.0.0 | **Ratified**: 2026-02-28

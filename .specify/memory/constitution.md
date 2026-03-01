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

### IV-A. Pydantic-AI Agent Implementation Rules (MANDATORY)
All pydantic-ai agents MUST be built against the documentation in `docs/MASTER/PYDANTIC_AI_DOCS.md`. This is the authoritative reference for correct API usage. Key rules:
- **Agent definition**: Use `Agent(model, deps_type=..., output_type=..., system_prompt=...)` pattern
- **Tools**: Decorate with `@agent.tool` and use `RunContext[DepsType]` as first parameter
- **Running agents**: Use `await agent.run(prompt, deps=deps)` (async) or `agent.run_sync(prompt, deps=deps)` (sync)
- **Structured outputs**: Set `output_type=YourPydanticModel` — pydantic-ai handles validation + retry automatically
- **Dependencies**: Define a dataclass as deps_type, pass via `deps=` parameter at run time
- **DO NOT** invent API patterns not documented in `docs/MASTER/PYDANTIC_AI_DOCS.md`
- **DO NOT** use `result.data` — the correct accessor is `result.output`
- **DO NOT** confuse pydantic-ai with the native Mistral Agents SDK — they are different libraries

### V. Architecture Pattern
- Backend agents write data to Supabase
- Frontend reads and reacts to Supabase Realtime
- Agents use pydantic-ai with dependencies, tools, structured outputs
- Orchestrator agent delegates to specialized sub-agents

### VI. Test-First
- Tests written before implementation where practical
- Red-Green-Refactor cycle encouraged

### VI-A. E2E Testing with Timestamps (MANDATORY)
- Every feature MUST include E2E tests that log timestamps and timing for each step
- Tests MUST print elapsed time for each operation (e.g., "[00:02.3s] Supabase write completed")
- Tests MUST include a total elapsed time summary at the end
- Every feature MUST include user testing instructions: a step-by-step guide a human can follow to manually verify the feature works (placed in the feature's spec directory or test file docstrings)

### VII. Simplicity
- Start simple, follow YAGNI principles
- No premature abstractions
- Minimum complexity needed for the current task

## Governance
- Constitution supersedes all other practices
- Amendments require documentation and approval

**Version**: 1.0.0 | **Ratified**: 2026-02-28

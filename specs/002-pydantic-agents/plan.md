# Implementation Plan: Pydantic-AI Agent Definitions

## Technical Context

- **Language**: Python 3.12
- **Framework**: pydantic-ai for structured LLM agents, native mistralai SDK for vision
- **Dependencies**: pydantic-ai, mistralai, supabase (all installed in Feature 1)
- **Model**: Mistral Large (triage/intake/dispatch/fusion), Mistral Small (vision/Pixtral)

## Architecture

### Agent Pattern (pydantic-ai)
```
Agent(model, deps_type=TriageNetDeps, output_type=PydanticModel, system_prompt=...)
  └── @agent.tool with RunContext[TriageNetDeps] for DB access
```

### Vision Pattern (native SDK)
```
mistral_client.chat.complete(model, messages=[{content: [text, image_url]}])
  └── Returns JSON → parsed into FrameAnalysis
```

## File Structure

```
apps/server/src/agents/
├── __init__.py          # Re-exports all agents
├── shared_deps.py       # TriageNetDeps (exists from Feature 1)
├── triage_agent.py      # Core triage — 3 tools
├── intake_agent.py      # Caller fact extraction — no tools
├── vision_agent.py      # Pixtral vision — native SDK
├── dispatch_agent.py    # Dispatch briefs — 1 tool
└── case_match_agent.py  # Evidence fusion — 1 tool

apps/server/src/tests/
└── test_phase5_agents.py  # All agent tests with timing
```

## Implementation Order

1. intake_agent.py (simplest — no tools)
2. triage_agent.py (3 tools, core agent)
3. dispatch_agent.py (1 tool)
4. case_match_agent.py (1 tool)
5. vision_agent.py (native SDK, different pattern)
6. __init__.py (re-exports)
7. test_phase5_agents.py (all agent tests)

# Research: Backend Foundation

## R1: Pydantic-AI with Mistral Models

**Decision**: Use `pydantic-ai[mistral]` for all agent definitions except vision (which uses native `mistralai` client for multimodal content arrays).

**Rationale**: Pydantic-AI provides typed deps injection via `RunContext[DepsType]`, automatic structured output validation with retry, and auto-generated tool schemas from type hints. The native Mistral SDK lacks these features. However, Pydantic-AI doesn't support Mistral's multimodal content-array format needed for Pixtral vision calls.

**Alternatives considered**:
- Native Mistral Agents SDK: No typed deps, no auto-retry on validation, no RunContext
- LangChain: Too heavy for a hackathon, unnecessary abstraction layers

**Key API patterns** (from docs/MASTER/PYDANTIC_AI_DOCS.md):
- `Agent(model, deps_type=..., output_type=..., system_prompt=...)`
- `@agent.tool` with `RunContext[DepsType]` as first parameter
- `result = await agent.run(prompt, deps=deps)` → access `result.output` (NOT `result.data`)

## R2: Supabase Python Client

**Decision**: Use `supabase-py` v2.11+ with service role key for backend writes.

**Rationale**: Direct Supabase client is the simplest approach. Service role key bypasses RLS for backend writes. Frontend uses anon key with RLS for reads.

**Alternatives considered**:
- Raw psycopg2/asyncpg: More control but loses Supabase's Realtime integration
- Prisma Python: Overkill for this use case

## R3: ElevenLabs API Integration

**Decision**: Use httpx direct HTTP calls to ElevenLabs REST API for both transcription (Scribe v1) and TTS (Turbo v2.5).

**Rationale**: ElevenLabs Python SDK exists but httpx is lighter and gives us full control over the request. Two endpoints: `/v1/speech-to-text` for transcription, `/v1/text-to-speech/{voice_id}` for TTS.

**Alternatives considered**:
- elevenlabs Python SDK: Adds a dependency we don't need; httpx is already in our deps
- Whisper local: No ElevenLabs integration, demo requires ElevenLabs

## R4: Configuration Management

**Decision**: Use `pydantic-settings` BaseSettings with `.env` file loading.

**Rationale**: Provides validation at startup, type coercion, and clear error messages for missing required fields. Standard pattern for FastAPI apps.

**Alternatives considered**:
- Raw os.environ: No validation, easy to miss typos
- python-decouple: Less integration with Pydantic ecosystem

## R5: Test Timing Strategy

**Decision**: Use a custom `TimedTest` context manager that prints `[elapsed] message` for each operation and a total summary at the end.

**Rationale**: Constitution requires E2E tests with timestamps. A simple context manager wrapping `time.time()` is the minimum viable approach.

**Alternatives considered**:
- pytest-benchmark: Overkill, measures statistical benchmarks not wall-clock for demo
- Custom pytest plugin: Unnecessary complexity for a hackathon

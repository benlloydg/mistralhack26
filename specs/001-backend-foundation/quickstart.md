# Quickstart: Backend Foundation

## Prerequisites

1. Python 3.12+
2. [uv](https://docs.astral.sh/uv/) package manager installed
3. Supabase project created with Realtime enabled
4. Mistral API key (from [console.mistral.ai](https://console.mistral.ai))
5. ElevenLabs API key (from [elevenlabs.io](https://elevenlabs.io))

## Setup

### 1. Create environment file

```bash
cd apps/server
cp .env.example .env  # Then fill in your real keys
```

Required values:
```env
MISTRAL_API_KEY=your_key
ELEVENLABS_API_KEY=your_key
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your_service_role_key
```

### 2. Install dependencies

```bash
cd apps/server
uv sync --dev
```

### 3. Run SQL migrations

Open Supabase SQL Editor and paste each migration file in order:
1. `supabase/migrations/001_incident_state.sql`
2. `supabase/migrations/002_agent_logs.sql`
3. `supabase/migrations/003_transcripts.sql`
4. `supabase/migrations/004_dispatches.sql`
5. `supabase/migrations/005_enable_realtime.sql`

Confirm Realtime is enabled on all 4 tables in Supabase Dashboard → Database → Replication.

### 4. Run tests

```bash
cd apps/server
uv run pytest src/tests/test_phase1_models.py -v -s          # Models (offline)
uv run pytest src/tests/test_phase2_supabase.py -v -s        # Supabase (needs DB)
uv run pytest src/tests/test_phase3_mistral.py -v -s         # Mistral (needs API key)
uv run pytest src/tests/test_phase4_elevenlabs.py -v -s      # ElevenLabs (needs API key)
```

All tests log timestamps and elapsed time per operation.

### 5. Run all tests together

```bash
cd apps/server
uv run pytest src/tests/ -v -s -k "phase1 or phase2 or phase3 or phase4"
```

## User Testing Instructions

### Manual Verification Steps

1. **Config validation**: Delete `MISTRAL_API_KEY` from `.env`, run `python -c "from src.config import settings"` — should error naming the missing variable. Restore it.

2. **Model validation**: Run `uv run pytest src/tests/test_phase1_models.py -v -s` — all model tests pass with timing.

3. **Supabase round-trip**: Run `uv run pytest src/tests/test_phase2_supabase.py -v -s` — verify:
   - Incident record created in Supabase dashboard
   - Record updated (severity changed)
   - Agent log entry visible in agent_logs table
   - Test cleans up after itself
   - All operations complete in < 2 seconds each

4. **Mistral connectivity**: Run `uv run pytest src/tests/test_phase3_mistral.py -v -s` — verify:
   - Structured output returned and validated
   - Response time logged

5. **ElevenLabs connectivity**: Run `uv run pytest src/tests/test_phase4_elevenlabs.py -v -s` — verify:
   - TTS generates audio bytes
   - Response time logged

# Test Storage Standard

## Purpose

All test results are stored as timestamped logs for grounding and traceability. This provides a verifiable record of what worked, when it worked, and how fast it was.

## Location

```
apps/server/test-results/
```

## Naming Convention

```
YYYYMMDD_HHMMSS_<phase>_<name>.log
```

Examples:
- `20260228_181041_phase1_models.log`
- `20260228_181100_phase3_mistral.log`
- `20260228_181154_phase5_agents.log`
- `20260228_181530_phase6_orchestrator.log`

## What Gets Logged

Each log file captures the full pytest output including:
- Test names and PASS/FAIL status
- `[elapsed]` timestamps per operation (e.g., `[1.903s] intake_agent.run()`)
- Total elapsed summary per test
- Structured output previews (e.g., severity, location, unit assignments)
- Error tracebacks if any test fails

## When to Log

- After implementing each feature (spec-kit feature)
- Run all tests for that feature and pipe output to a timestamped log file
- Commit the logs with the feature

## How to Generate

```bash
cd apps/server
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
.venv/bin/python -m pytest src/tests/test_<phase>.py -v -s 2>&1 | tee "test-results/${TIMESTAMP}_<phase>_<name>.log"
```

## Test Timing Requirements

Every test MUST include:
1. **Per-operation timing**: Each step wrapped in `TimedStep.step()` context manager
2. **Total elapsed summary**: Printed at end of each test
3. **Performance assertions**: Key operations have time budgets (e.g., agent calls < 8s)

## TimedStep Pattern

All test files use this pattern for consistent timing:

```python
class TimedStep:
    def __init__(self):
        self.steps: list[tuple[str, float]] = []
        self.total_start = time.time()

    def step(self, label: str):
        return _StepCtx(self, label)

    def summary(self):
        total = time.time() - self.total_start
        print(f"\n{'='*60}")
        print(f"TOTAL ELAPSED: [{total:.3f}s]")
        for label, elapsed in self.steps:
            print(f"  [{elapsed:.3f}s] {label}")
        print(f"{'='*60}")
```

## Current Test Inventory

| Phase | File | Tests | Status |
|-------|------|-------|--------|
| 1 - Models | `test_phase1_models.py` | 23 | All pass |
| 2 - Supabase | `test_phase2_supabase.py` | 5 | Awaiting SQL migrations |
| 3 - Mistral | `test_phase3_mistral.py` | 2 | All pass |
| 4 - ElevenLabs | `test_phase4_elevenlabs.py` | 1 | Pass (run individually) |
| 5 - Agents | `test_phase5_agents.py` | 5 | All pass |
| 6 - Orchestrator | `test_phase6_orchestrator.py` | 4 | All pass |

# Quickstart: After-Action Report

## Prerequisites

- Python 3.12 with uv
- Running Supabase instance with migrations 001-007 applied
- `.env` configured with `MISTRAL_API_KEY`, `ELEVENLABS_API_KEY`, `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`
- At least one completed demo run (case in `resolved_demo` status)

## Test the report endpoint

```bash
# Start the server
cd apps/server && uv run uvicorn src.main:app --reload

# Run a demo first (if no completed cases exist)
curl -X POST http://localhost:8000/api/v1/demo/start
# Wait for demo to complete...

# Generate the report
curl -s http://localhost:8000/api/v1/cases/TN-XXXXXXXX-XXXXXX/report | python -m json.tool

# Check key_frames section has image URLs
curl -s http://localhost:8000/api/v1/cases/TN-XXXXXXXX-XXXXXX/report | python -c "
import json, sys
r = json.load(sys.stdin)
print(f'Sections: {len([k for k in r if k not in (\"case_id\", \"generated_at\", \"warning\")])}')
print(f'Timeline events: {len(r[\"timeline\"])}')
print(f'Key frames: {len(r[\"key_frames\"])}')
print(f'Executive summary: {r[\"executive_summary\"][:80]}...')
"
```

## Verify frame serving

```bash
# Check frames directory exists after demo
ls assets/frames/

# Fetch a frame via the static mount
curl -I http://localhost:8000/frames/TN-XXXXXXXX-XXXXXX_t38s.jpg
# Should return 200 with Content-Type: image/jpeg
```

## Run tests

```bash
cd apps/server
PYTHONPATH=. uv run pytest src/tests/ -v -k "report"
```

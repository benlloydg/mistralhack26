import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from .routes import demo, health, report
from .services.tts import GENERATED_AUDIO_DIR


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    yield
    # Shutdown — clean up active orchestrator / Scribe connections
    if demo._active_orchestrator:
        demo._active_orchestrator.cancel()
        # Disconnect Scribe WebSocket if active
        scribe = getattr(demo._active_orchestrator, "_scribe", None)
        if scribe:
            try:
                await scribe.disconnect()
            except Exception:
                pass
        demo._active_orchestrator = None


app = FastAPI(title="TriageNet API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(demo.router, prefix="/api/v1")
app.include_router(health.router, prefix="/api/v1")
app.include_router(report.router)

# Serve generated TTS audio files at /audio/{filename}
os.makedirs(GENERATED_AUDIO_DIR, exist_ok=True)
app.mount("/audio", StaticFiles(directory=GENERATED_AUDIO_DIR), name="audio")

# Serve saved vision frames at /frames/{filename}
FRAMES_DIR = os.path.join(os.path.dirname(__file__), "..", "assets", "frames")
os.makedirs(FRAMES_DIR, exist_ok=True)
app.mount("/frames", StaticFiles(directory=FRAMES_DIR), name="frames")

# Serve video/media assets at /assets/{filename}
ASSETS_DIR = os.path.join(os.path.dirname(__file__), "..", "assets")
os.makedirs(ASSETS_DIR, exist_ok=True)
app.mount("/assets", StaticFiles(directory=ASSETS_DIR), name="assets")

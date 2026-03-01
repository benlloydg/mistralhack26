import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from .routes import demo, health, report
from .services.tts import GENERATED_AUDIO_DIR

app = FastAPI(title="TriageNet API", version="1.0.0")

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

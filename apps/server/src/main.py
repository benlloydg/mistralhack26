from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes import demo, health

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

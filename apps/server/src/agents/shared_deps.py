from __future__ import annotations
import os
from dataclasses import dataclass
from supabase import Client as SupabaseClient
from mistralai import Mistral
from ..config import settings

# pydantic-ai's MistralProvider reads MISTRAL_API_KEY from env at Agent() creation time
os.environ.setdefault("MISTRAL_API_KEY", settings.mistral_api_key)


@dataclass
class TriageNetDeps:
    """Injected into every Pydantic-AI agent via RunContext[TriageNetDeps]."""
    supabase: SupabaseClient
    mistral_client: Mistral          # For Pixtral vision calls only
    case_id: str
    session_start_time: float        # time.time() at demo start, for elapsed time calc
    elevenlabs_api_key: str

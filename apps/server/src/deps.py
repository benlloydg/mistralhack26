from supabase import create_client, Client as SupabaseClient
from mistralai import Mistral
from .config import settings


def get_supabase() -> SupabaseClient:
    return create_client(settings.supabase_url, settings.supabase_service_key)


def get_mistral() -> Mistral:
    return Mistral(api_key=settings.mistral_api_key)

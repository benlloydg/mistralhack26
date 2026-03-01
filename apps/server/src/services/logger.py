"""
Standalone logging helpers for writing agent_logs to Supabase.
"""
from supabase import Client as SupabaseClient
from ..models.events import AgentLogEntry


def write_agent_log(supabase: SupabaseClient, entry: AgentLogEntry):
    """Write a single agent log entry to Supabase."""
    supabase.table("agent_logs").insert(entry.model_dump()).execute()


def write_agent_logs(supabase: SupabaseClient, entries: list[AgentLogEntry]):
    """Write multiple agent log entries to Supabase."""
    rows = [e.model_dump() for e in entries]
    supabase.table("agent_logs").insert(rows).execute()

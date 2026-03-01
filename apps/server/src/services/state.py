"""
All state mutations go through this module. It writes to Supabase and logs the change.
"""
from supabase import Client as SupabaseClient
from ..models.incident import IncidentState, TimelineEvent
from ..models.events import AgentLogEntry
import time


class StateManager:
    def __init__(self, supabase: SupabaseClient, case_id: str, start_time: float):
        self.sb = supabase
        self.case_id = case_id
        self.start_time = start_time

    def elapsed(self) -> str:
        """Returns elapsed time as MM:SS string."""
        s = int(time.time() - self.start_time)
        return f"{s // 60:02d}:{s % 60:02d}"

    def get_state(self) -> IncidentState:
        result = self.sb.table("incident_state") \
            .select("*").eq("case_id", self.case_id).single().execute()
        return IncidentState(**result.data)

    def update_state(self, **kwargs) -> IncidentState:
        """Partial update. Pass any IncidentState fields as kwargs."""
        self.sb.table("incident_state") \
            .update(kwargs).eq("case_id", self.case_id).execute()
        return self.get_state()

    def append_timeline(self, agent: str, event: str):
        """Append a timeline event. Uses JSONB append in Postgres."""
        state = self.get_state()
        timeline = state.timeline
        timeline.append(TimelineEvent(t=self.elapsed(), agent=agent, event=event))
        self.update_state(timeline=[t.model_dump() for t in timeline])

    def log_agent(self, entry: AgentLogEntry):
        """Write to agent_logs table."""
        self.sb.table("agent_logs").insert(entry.model_dump()).execute()

    def log(self, agent: str, event_type: str, message: str,
            data: dict = None, color: str = "blue", flash: bool = False):
        """Convenience: log + timeline in one call."""
        self.log_agent(AgentLogEntry(
            case_id=self.case_id,
            agent=agent,
            event_type=event_type,
            message=message,
            data=data or {},
            display_color=color,
            display_flash=flash,
        ))
        self.append_timeline(agent, message)

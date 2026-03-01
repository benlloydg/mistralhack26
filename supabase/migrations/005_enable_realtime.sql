-- Enable Supabase Realtime on all tables the frontend subscribes to.
-- CRITICAL: Without this, the frontend gets nothing.
ALTER PUBLICATION supabase_realtime ADD TABLE incident_state;
ALTER PUBLICATION supabase_realtime ADD TABLE agent_logs;
ALTER PUBLICATION supabase_realtime ADD TABLE transcripts;
ALTER PUBLICATION supabase_realtime ADD TABLE dispatches;

import { useEffect, useState } from 'react';
import { supabase } from '@/lib/supabase';
import { AgentLog } from '@/lib/types';

export function useAgentLogs(caseId: string) {
  const [logs, setLogs] = useState<AgentLog[]>([]);

  useEffect(() => {
    // Initial fetch
    supabase
      .from('agent_logs')
      .select('*')
      .eq('case_id', caseId)
      .order('created_at', { ascending: true })
      .then(({ data }) => {
        if (data) setLogs(data as AgentLog[]);
      });

    // Realtime — listen for new inserts
    const channel = supabase
      .channel(`logs_${caseId}`)
      .on(
        'postgres_changes',
        {
          event: 'INSERT',
          schema: 'public',
          table: 'agent_logs',
          filter: `case_id=eq.${caseId}`,
        },
        (payload) => {
          setLogs((prev) => [...prev, payload.new as AgentLog]);
        }
      )
      .subscribe();

    return () => {
      supabase.removeChannel(channel);
    };
  }, [caseId]);

  return logs;
}

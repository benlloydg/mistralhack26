import { useEffect, useState } from 'react';
import { supabase } from '@/lib/supabase';
import { IncidentState } from '@/lib/types';

export function useIncidentState(caseId: string) {
  const [state, setState] = useState<IncidentState | null>(null);

  useEffect(() => {
    // Initial fetch
    supabase
      .from('incident_state')
      .select('*')
      .eq('case_id', caseId)
      .single()
      .then(({ data }) => {
        if (data) setState(data as IncidentState);
      });

    // Realtime subscription
    const channel = supabase
      .channel(`incident_${caseId}`)
      .on(
        'postgres_changes',
        {
          event: 'UPDATE',
          schema: 'public',
          table: 'incident_state',
          filter: `case_id=eq.${caseId}`,
        },
        (payload) => {
          setState(payload.new as IncidentState);
        }
      )
      .subscribe();

    return () => {
      supabase.removeChannel(channel);
    };
  }, [caseId]);

  return state;
}

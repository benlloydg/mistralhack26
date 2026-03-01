import { useEffect, useState } from 'react';
import { supabase } from '@/lib/supabase';
import { Dispatch } from '@/lib/types';

export function useDispatches(caseId: string) {
  const [dispatches, setDispatches] = useState<Dispatch[]>([]);

  useEffect(() => {
    // Initial fetch
    supabase
      .from('dispatches')
      .select('*')
      .eq('case_id', caseId)
      .order('created_at', { ascending: true })
      .then(({ data }) => {
        if (data) setDispatches(data as Dispatch[]);
      });

    // Realtime — listen for new inserts
    const channel = supabase
      .channel(`dispatches_${caseId}`)
      .on(
        'postgres_changes',
        {
          event: 'INSERT',
          schema: 'public',
          table: 'dispatches',
          filter: `case_id=eq.${caseId}`,
        },
        (payload) => {
          setDispatches((prev) => [...prev, payload.new as Dispatch]);
        }
      )
      .subscribe();

    return () => {
      supabase.removeChannel(channel);
    };
  }, [caseId]);

  return dispatches;
}

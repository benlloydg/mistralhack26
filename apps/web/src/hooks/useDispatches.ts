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

    // Realtime — listen for inserts and updates
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
      .on(
        'postgres_changes',
        {
          event: 'UPDATE',
          schema: 'public',
          table: 'dispatches',
          filter: `case_id=eq.${caseId}`,
        },
        (payload) => {
          setDispatches((prev) =>
            prev.map((d) => (d.id === (payload.new as Dispatch).id ? (payload.new as Dispatch) : d))
          );
        }
      )
      .subscribe();

    return () => {
      supabase.removeChannel(channel);
    };
  }, [caseId]);

  return dispatches;
}

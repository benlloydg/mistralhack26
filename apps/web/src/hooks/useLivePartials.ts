import { useEffect, useState } from 'react';
import { supabase } from '@/lib/supabase';

interface LivePartial {
  case_id: string;
  text: string;
  timestamp: number;
  updated_at: string;
}

export function useLivePartials(caseId: string) {
  const [partial, setPartial] = useState<string | null>(null);

  useEffect(() => {
    if (!caseId) return;

    // Initial fetch
    supabase
      .from('live_partials')
      .select('*')
      .eq('case_id', caseId)
      .single()
      .then(({ data }) => {
        if (data) setPartial((data as LivePartial).text);
      });

    // Realtime — listen for inserts AND updates (upsert pattern)
    const channel = supabase
      .channel(`live_partials_${caseId}`)
      .on(
        'postgres_changes',
        {
          event: '*',
          schema: 'public',
          table: 'live_partials',
          filter: `case_id=eq.${caseId}`,
        },
        (payload) => {
          const data = payload.new as LivePartial;
          if (data?.text) {
            setPartial(data.text);
          }
        }
      )
      .subscribe();

    return () => {
      supabase.removeChannel(channel);
    };
  }, [caseId]);

  return partial;
}

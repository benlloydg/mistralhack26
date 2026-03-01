import { useEffect, useState } from 'react';
import { supabase } from '@/lib/supabase';
import { Transcript } from '@/lib/types';

export function useTranscripts(caseId: string) {
  const [transcripts, setTranscripts] = useState<Transcript[]>([]);

  useEffect(() => {
    // Initial fetch
    supabase
      .from('transcripts')
      .select('*')
      .eq('case_id', caseId)
      .order('created_at', { ascending: true })
      .then(({ data }) => {
        if (data) setTranscripts(data as Transcript[]);
      });

    // Realtime — listen for new inserts
    const channel = supabase
      .channel(`transcripts_${caseId}`)
      .on(
        'postgres_changes',
        {
          event: 'INSERT',
          schema: 'public',
          table: 'transcripts',
          filter: `case_id=eq.${caseId}`,
        },
        (payload) => {
          setTranscripts((prev) => [...prev, payload.new as Transcript]);
        }
      )
      .subscribe();

    return () => {
      supabase.removeChannel(channel);
    };
  }, [caseId]);

  return transcripts;
}

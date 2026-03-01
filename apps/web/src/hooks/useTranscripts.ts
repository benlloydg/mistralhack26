import { useEffect, useState } from 'react';
import { supabase } from '@/lib/supabase';
import { Transcript } from '@/lib/types';

export function useTranscripts(caseId: string) {
  const [transcripts, setTranscripts] = useState<Transcript[]>([]);

  useEffect(() => {
    if (!caseId) return;

    // Initial fetch
    supabase
      .from('transcripts')
      .select('*')
      .eq('case_id', caseId)
      .order('created_at', { ascending: true })
      .then(({ data }) => {
        if (data) setTranscripts(data as Transcript[]);
      });

    // Realtime — listen for inserts AND updates (translation arrives via UPDATE)
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
      .on(
        'postgres_changes',
        {
          event: 'UPDATE',
          schema: 'public',
          table: 'transcripts',
          filter: `case_id=eq.${caseId}`,
        },
        (payload) => {
          // Replace the existing transcript with the updated version
          setTranscripts((prev) =>
            prev.map((t) =>
              t.id === (payload.new as Transcript).id
                ? (payload.new as Transcript)
                : t
            )
          );
        }
      )
      .subscribe();

    return () => {
      supabase.removeChannel(channel);
    };
  }, [caseId]);

  return transcripts;
}

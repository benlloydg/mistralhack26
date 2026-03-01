import { Transcript } from "@/lib/types";
import { cn } from "@/lib/utils";
import { useEffect, useRef, useState } from "react";
import { Volume2 } from "lucide-react";

export function TranscriptPanel({ transcripts }: { transcripts: Transcript[] }) {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.scrollTo({
        top: containerRef.current.scrollHeight,
        behavior: 'smooth'
      });
    }
  }, [transcripts]);

  // Filter out any outbound DISPATCH messages since they move to Action column
  const inboundTranscripts = transcripts.filter(t => (t.caller_label || t.caller_id)?.toLowerCase() !== 'dispatch');


  return (
    <div className="flex flex-col h-full tech-glass">
      <div className="border-b dark:border-white/10 border-black/10 p-3 px-4 flex justify-between items-center dark:bg-black/40 bg-zinc-100">
        <h2 className="text-xs font-mono uppercase tracking-widest dark:text-white/50 text-slate-500 font-semibold">Scene Audio</h2>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-[2px] h-3 mr-2">
             <div className="w-[2px] h-full bg-blue-500/50 animate-[pulse_1s_ease-in-out_infinite]"></div>
             <div className="w-[2px] h-2/3 bg-blue-500/50 animate-[pulse_1.2s_ease-in-out_infinite_0.2s]"></div>
             <div className="w-[2px] h-1/2 bg-blue-500/50 animate-[pulse_0.8s_ease-in-out_infinite_0.4s]"></div>
             <div className="w-[2px] h-full bg-blue-500/50 animate-[pulse_1.5s_ease-in-out_infinite_0.1s]"></div>
             <div className="w-[2px] h-3/4 bg-blue-500/50 animate-[pulse_1.1s_ease-in-out_infinite_0.3s]"></div>
             <div className="w-[2px] h-full bg-blue-500/50 animate-[pulse_0.9s_ease-in-out_infinite_0.2s]"></div>
             <div className="w-[2px] h-2/3 bg-blue-500/50 animate-[pulse_1.3s_ease-in-out_infinite_0.1s]"></div>
             <div className="w-[2px] h-1/2 bg-blue-500/50 animate-[pulse_1.4s_ease-in-out_infinite_0.3s]"></div>
             <div className="w-[2px] h-3/4 bg-blue-500/50 animate-[pulse_1.0s_ease-in-out_infinite_0.5s]"></div>
             <div className="w-[2px] h-full bg-blue-500/50 animate-[pulse_1.2s_ease-in-out_infinite]"></div>
          </div>
          <div className="text-xs font-mono font-bold text-red-500 flex items-center gap-2">
            <span className="w-1.5 h-1.5 rounded-full bg-red-500 animate-[pulse_2s_ease-in-out_infinite]"></span>
            LIVE
          </div>
        </div>
      </div>

      <div 
        ref={containerRef}
        className="flex-1 overflow-y-auto p-4 space-y-4 font-mono text-xs"
      >
        {inboundTranscripts.length === 0 ? (
          <div className="dark:text-white/20 text-black/30 italic">Waiting for audio transmission...</div>
        ) : (
          inboundTranscripts.map((t) => (
              <div 
                key={t.id} 
                className="flex flex-col gap-1 pb-2 border-b dark:border-white/5 border-black/5 last:border-0 animate-in fade-in duration-300"
              >
                <div className="flex items-center gap-2">
                  <span className="dark:text-white/30 text-black/40">[{new Date(t.created_at).toISOString().substring(11, 19)}]</span>
                  <span className="uppercase text-blue-500 dark:text-blue-400 font-bold tracking-wider">
                    {t.language.toUpperCase()} · {t.caller_label?.toLowerCase().includes('caller') ? 'BYSTANDER' : (t.caller_label || t.caller_id).toUpperCase()}
                  </span>
                </div>
                
                <div className="leading-relaxed dark:text-white/70 text-black/70 pl-[90px]">
                  {t.language !== 'en' && t.translated_text ? (
                    <div className="flex flex-col gap-1 mt-1">
                      <div className="dark:text-white/40 text-black/40">"{t.original_text}"</div>
                      <div className="dark:text-white text-black font-sans text-sm">"{t.translated_text}"</div>
                    </div>
                  ) : (
                    <div className="dark:text-white text-black font-sans text-sm">"{t.original_text}"</div>
                  )}
                </div>
                {t.entities && t.entities.length > 0 && (
                  <div className="mt-1.5 flex flex-wrap gap-1.5 pl-[90px]">
                    {t.entities.map((entity, idx) => (
                      <span 
                        key={`${t.id}-${entity}`} 
                        className="text-[9px] px-1 bg-black/5 dark:bg-white/5 text-slate-500 dark:text-slate-400 border border-black/10 dark:border-white/10 rounded uppercase"
                      >
                        [{entity}]
                      </span>
                    ))}
                  </div>
                )}
              </div>
          ))
        )}
      </div>
    </div>
  );
}

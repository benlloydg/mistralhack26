import { Transcript } from "@/lib/types";
import { cn } from "@/lib/utils";
import { useEffect, useRef, useState } from "react";
import { Volume2, AlertTriangle } from "lucide-react";

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

  // Group dispatch messages together
  const renderItems: any[] = [];
  let dispatchGroup: any = null;

  transcripts.forEach((t) => {
    const isDispatch = (t.caller_label || t.caller_id)?.toLowerCase() === 'dispatch';
    if (isDispatch) {
      if (!dispatchGroup) {
        dispatchGroup = {
          id: `dispatch-${t.id}`,
          isDispatch: true,
          created_at: t.created_at,
          languages: [t.language.toUpperCase()],
        };
        renderItems.push(dispatchGroup);
      } else {
        if (!dispatchGroup.languages.includes(t.language.toUpperCase())) {
            dispatchGroup.languages.push(t.language.toUpperCase());
        }
      }
    } else {
      dispatchGroup = null;
      renderItems.push({ ...t, isDispatch: false });
    }
  });
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
        {renderItems.length === 0 ? (
          <div className="dark:text-white/20 text-black/30 italic text-sm font-sans">Waiting for audio transmission...</div>
        ) : (
          renderItems.map((item) => {
            if (item.isDispatch) {
              return (
                <div key={item.id} className="flex flex-col pb-3 mb-3 border-b dark:border-white/5 border-black/5 last:border-0 last:mb-0 last:pb-0 animate-in fade-in duration-300">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2 text-xs">
                      <span className="dark:text-white/30 text-black/40 font-mono">[{new Date(item.created_at).toISOString().substring(11, 19)}]</span>
                      <span className="uppercase text-amber-500 font-mono font-bold tracking-wider flex items-center gap-1.5">
                        <AlertTriangle className="w-3 h-3" /> DISPATCH → SCENE
                      </span>
                    </div>
                    <span className="text-[9px] font-mono tracking-widest uppercase bg-amber-500/10 text-amber-500 px-1.5 py-0.5 rounded">
                      EVACUATION
                    </span>
                  </div>
                  <div className="pl-[82px] flex items-center gap-2 text-xs font-mono font-bold dark:text-white/80 text-black/80">
                    <Volume2 className="w-3.5 h-3.5 text-blue-500 dark:text-blue-400" />
                    {item.languages.map((lang: string, idx: number) => (
                      <span key={lang} className="flex items-center gap-1">
                        {lang} <span className="text-emerald-500">✓</span>
                        {idx < item.languages.length - 1 && <span className="opacity-40 mx-1">·</span>}
                      </span>
                    ))}
                  </div>
                </div>
              );
            } else {
              const t = item as Transcript;
              return (
                <div key={t.id} className="flex flex-col pb-3 mb-3 border-b dark:border-white/5 border-black/5 last:border-0 last:mb-0 last:pb-0 animate-in fade-in duration-300">
                  <div className="flex items-center justify-between mb-1.5">
                    <div className="flex items-center gap-2 text-xs">
                      <span className="dark:text-white/30 text-black/40 font-mono">[{new Date(t.created_at).toISOString().substring(11, 19)}]</span>
                      <span className="uppercase text-blue-500 dark:text-blue-400 font-mono font-bold tracking-wider">
                        {t.language.toUpperCase()}
                      </span>
                    </div>
                    {t.translated_text && t.language !== 'en' && (
                      <span className="text-[9px] font-mono tracking-widest uppercase bg-black/5 dark:bg-white/5 px-1.5 py-0.5 rounded text-slate-500 dark:text-slate-400">
                        TRANSLATED
                      </span>
                    )}
                  </div>
                  
                  <div className="flex flex-col gap-1 pl-[82px]">
                    {t.language !== 'en' && t.translated_text ? (
                      <>
                        <div className="dark:text-white/50 text-black/50 text-[11px] leading-relaxed font-sans">"{t.original_text}"</div>
                        <div className="dark:text-white/90 text-black/90 font-sans text-sm font-medium">{t.translated_text}</div>
                      </>
                    ) : (
                      <div className="dark:text-white/90 text-black/90 font-sans text-sm font-medium">{t.original_text}</div>
                    )}
                  </div>
                </div>
              );
            }
          })
        )}
      </div>
    </div>
  );
}

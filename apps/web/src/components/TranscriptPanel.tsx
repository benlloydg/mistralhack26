import { Transcript } from "@/lib/types";
import { cn } from "@/lib/utils";
import { useEffect, useRef, useState } from "react";
import { Volume2, AlertTriangle } from "lucide-react";

export function TranscriptPanel({ transcripts, spectrum }: { transcripts: Transcript[], spectrum?: number[] }) {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.scrollTo({
        top: 0,
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
          <div className="flex items-center gap-[2px] h-3 mr-2 items-center h-[12px]">
            {(spectrum || new Array(10).fill(0.1)).map((val, i) => (
              <div 
                key={i} 
                className="w-[2px] bg-blue-500/80 transition-all duration-75"
                style={{ height: `${Math.max(15, val * 100)}%` }}
              ></div>
            ))}
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
          [...renderItems].reverse().map((item) => {
            if (item.isDispatch) {
              return (
                <div key={item.id} className="flex flex-col pb-3 mb-3 border-b dark:border-white/5 border-black/5 last:border-0 last:mb-0 last:pb-0 animate-in fade-in slide-in-from-top-2 duration-300">
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
                <div key={t.id} className="flex flex-col pb-3 mb-3 border-b dark:border-white/5 border-black/5 last:border-0 last:mb-0 last:pb-0 animate-in fade-in slide-in-from-top-2 duration-300">
                  <div className="flex items-start justify-between mb-1.5">
                    <div className="flex items-start gap-2 text-xs flex-1">
                      <span className="dark:text-white/30 text-black/40 font-mono mt-[2px] shrink-0">[{new Date(t.created_at).toISOString().substring(11, 19)}]</span>
                      <div className="dark:text-white/70 text-black/70 text-[15px] font-semibold tracking-tight">
                        "{t.original_text}"
                      </div>
                    </div>
                    {t.translated_text && t.language !== 'en' ? (
                      <span className="text-[9px] font-mono tracking-widest uppercase bg-blue-500/10 dark:bg-blue-400/10 px-1.5 py-0.5 rounded text-blue-600 dark:text-blue-400 font-bold shrink-0 ml-3 mt-[1px]">
                        {t.language.toUpperCase()} → EN
                      </span>
                    ) : (
                      <span className="text-[9px] font-mono tracking-widest uppercase bg-black/5 dark:bg-white/5 px-1.5 py-0.5 rounded text-slate-500 dark:text-slate-400 font-bold shrink-0 ml-3 mt-[1px]">
                        {t.language.toUpperCase()}
                      </span>
                    )}
                  </div>
                  
                  {t.translated_text && t.language !== 'en' && (
                    <div className="dark:text-white/90 text-black/90 font-sans text-sm leading-tight mt-1">
                      {t.translated_text}
                    </div>
                  )}
                </div>
              );
            }
          })
        )}
      </div>
    </div>
  );
}

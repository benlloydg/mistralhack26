import { Transcript } from "@/lib/types";
import { cn } from "@/lib/utils";
import { useEffect, useRef, useState } from "react";
import { Volume2 } from "lucide-react";

export function TranscriptPanel({ transcripts }: { transcripts: Transcript[] }) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [activeTab, setActiveTab] = useState<string>('all');
  const [newCallers, setNewCallers] = useState<Set<string>>(new Set());
  const prevCallersRef = useRef<string[]>([]);

  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.scrollTo({
        top: containerRef.current.scrollHeight,
        behavior: 'smooth'
      });
    }
  }, [transcripts, activeTab]);

  // Extract unique callers, ignoring 'dispatch' for tab generation
  const callers = Array.from(new Set(transcripts.map(t => t.caller_label || t.caller_id)))
    .filter(c => c && c.toLowerCase() !== 'dispatch');

  useEffect(() => {
    // Detect new callers
    if (prevCallersRef.current.length > 0 && callers.length > prevCallersRef.current.length) {
      const newlyAdded = callers.find(c => !prevCallersRef.current.includes(c));
      if (newlyAdded && newlyAdded !== activeTab && newlyAdded !== 'Operator') {
        setNewCallers(prev => new Set(prev).add(newlyAdded));
      }
    }
    prevCallersRef.current = callers;
  }, [callers.length, activeTab]);

  const handleTabChange = (tab: string) => {
    setActiveTab(tab);
    if (newCallers.has(tab)) {
      setNewCallers(prev => {
        const next = new Set(prev);
        next.delete(tab);
        return next;
      });
    }
  };

  const filteredTranscripts = activeTab === 'all' 
    ? transcripts 
    : transcripts.filter(t => {
        const label = t.caller_label || t.caller_id;
        return label === activeTab || label?.toLowerCase() === 'dispatch';
      });

  return (
    <div className="flex flex-col h-full tech-glass">
      <div className="border-b dark:border-white/10 border-black/10 p-0 flex justify-between items-center dark:bg-black/40 bg-zinc-100 pr-4">
        <div className="flex">
          <button 
            onClick={() => handleTabChange('all')}
            className={cn(
              "px-4 py-3 text-xs font-mono uppercase tracking-widest font-semibold border-r dark:border-white/10 border-black/10 transition-colors",
              activeTab === 'all' ? "dark:bg-white/10 bg-black/10 dark:text-white text-black" : "dark:text-white/40 text-black/40 hover:text-black/60 dark:hover:text-white/60 dark:hover:bg-white/5 hover:bg-black/5"
            )}
          >
            All Comm
          </button>
          {callers.map(caller => (
            <button 
              key={caller}
              onClick={() => handleTabChange(caller)}
              className={cn(
                "relative px-4 py-3 text-xs font-mono uppercase tracking-widest font-semibold border-r dark:border-white/10 border-black/10 transition-colors flex items-center gap-2",
                activeTab === caller ? "dark:bg-white/10 bg-black/10 dark:text-white text-black" : "dark:text-white/40 text-black/40 hover:text-black/60 dark:hover:text-white/60 dark:hover:bg-white/5 hover:bg-black/5"
              )}
            >
              {newCallers.has(caller) && (
                <span className="absolute top-2 right-2 w-1.5 h-1.5 rounded-full bg-blue-500 animate-pulse shadow-[0_0_8px_rgba(59,130,246,0.8)]"></span>
              )}
              {caller}
            </button>
          ))}
        </div>
        <div className="text-xs font-mono font-bold dark:text-white/20 text-black/30 flex items-center gap-2">
          <Volume2 className="w-3.5 h-3.5" />
          Live
        </div>
      </div>

      <div 
        ref={containerRef}
        className="flex-1 overflow-y-auto p-5 space-y-4"
      >
        {filteredTranscripts.length === 0 ? (
          <div className="dark:text-white/20 text-black/30 italic font-mono text-xs">Waiting for audio transmission...</div>
        ) : (
          filteredTranscripts.map((t) => {
            const isDispatch = (t.caller_label || t.caller_id)?.toLowerCase() === 'dispatch';
            
            return (
              <div 
                key={t.id} 
                className={cn("flex flex-col gap-1 pb-4 animate-in fade-in duration-300", isDispatch && "items-end text-right")}
              >
                <div className={cn("flex items-center gap-2", isDispatch && "flex-row-reverse")}>
                  <span className="text-[10px] font-mono dark:text-white/30 text-black/40">[{new Date(t.created_at).toISOString().substring(11, 19)}]</span>
                  <span className={cn(
                    "text-[10px] uppercase font-mono px-1.5 py-0.5 rounded font-bold tracking-wider flex items-center gap-1.5",
                    isDispatch ? "bg-cyan-500/10 text-cyan-600 dark:text-cyan-400 border border-cyan-500/20" :
                    t.caller_label === 'Operator' ? "bg-blue-500/20 text-blue-600 dark:text-blue-400" : "dark:bg-white/10 bg-black/5 dark:text-white/60 text-black/60"
                  )}>
                    {isDispatch && <Volume2 className="w-3 h-3" />}
                    {isDispatch ? `DISPATCH → ${t.language.toUpperCase()}` : (t.caller_label || t.caller_id)}
                  </span>
                  {!isDispatch && t.language !== 'en' && t.translated_text && (
                    <span className="text-[10px] font-mono text-amber-500 border border-amber-500/30 px-1 rounded-sm bg-amber-500/10">
                      TRANSLATED: {t.language.toUpperCase()}
                    </span>
                  )}
                </div>
                
                <div className={cn("text-sm leading-relaxed dark:text-white/90 text-black/90", isDispatch ? "pr-[110px]" : "pl-[90px]")}>
                  {isDispatch && t.original_text && t.translated_text ? (
                    <div className="flex flex-col gap-1 mt-1">
                      <div className="text-cyan-700 dark:text-cyan-300">"{t.original_text}"</div>
                      <div className="text-[10px] font-mono dark:text-white/30 text-black/30 flex items-center justify-end gap-2 mt-1">
                        <span className="h-px w-4 dark:bg-white/20 bg-black/20"></span>
                        Translation
                        <span className="h-px w-4 dark:bg-white/20 bg-black/20"></span>
                      </div>
                      <div className="dark:text-white/70 text-black/70 italic text-xs">"{t.translated_text}"</div>
                    </div>
                  ) : (
                    t.translated_text || t.original_text
                  )}
                
                {t.entities && t.entities.length > 0 && !isDispatch && (
                  <div className="mt-2 flex flex-wrap gap-1.5">
                    {t.entities.map((entity, idx) => (
                      <span 
                        key={`${t.id}-${entity}`} 
                        className="text-[10px] font-mono px-1.5 py-0.5 bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20 rounded animate-in fade-in slide-in-from-bottom-2 duration-500 fill-mode-both"
                        style={{ animationDelay: `${500 + (idx * 200)}ms` }}
                      >
                        {entity}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>
          );
        })
        )}
      </div>
    </div>
  );
}

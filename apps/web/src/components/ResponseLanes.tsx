import { Dispatch, Transcript } from "@/lib/types";
import { cn } from "@/lib/utils";
import { Check, Clock, Navigation, Volume2, Radio, Play, Loader2 } from "lucide-react";
import { useState, useEffect } from "react";

export function ResponseLanes({ 
  dispatches, 
  transcripts = [],
  recommendedUnits = [],
  onFirstExecute,
  onBroadcastStateChange
}: { 
  dispatches: Dispatch[], 
  transcripts?: Transcript[],
  recommendedUnits?: string[],
  onFirstExecute?: () => void,
  onBroadcastStateChange?: (isPlaying: boolean) => void
}) {
  const [executingUnits, setExecutingUnits] = useState<Record<string, 'executing' | 'done'>>({});
  const [broadcastState, setBroadcastState] = useState<'ready' | 'playing' | 'sent'>('ready');
  const [activeLangIndex, setActiveLangIndex] = useState(-1);
  const [hasNotifiedBackend, setHasNotifiedBackend] = useState(false);

  const realOutbound = transcripts.filter(t => (t.caller_label || t.caller_id)?.toLowerCase() === 'dispatch');
  const outboundMessages = realOutbound.length > 0 ? realOutbound : [
    { id: 991, language: 'es', original_text: '¡Atención! Se ha detectado fuego. Aléjense del área inmediatamente.', translated_text: null, caller_label: 'dispatch' },
    { id: 992, language: 'zh', original_text: '注意！已检测到火灾。请立即远离该区域。', translated_text: null, caller_label: 'dispatch' },
    { id: 993, language: 'fr', original_text: 'Attention ! Un incendie a été détecté. Éloignez-vous immédiatement.', translated_text: null, caller_label: 'dispatch' },
  ] as any[];
  
  // Create synthetic list merging recommended and confirmed/dispatched
  const existingTypes = new Set(dispatches.map(d => d.unit_type.toLowerCase()));
  const syntheticRecommended = recommendedUnits
    .filter(u => !existingTypes.has(u.toLowerCase()))
    .map(u => ({
      id: `rec-${u}`,
      unit_type: u,
      status: 'recommended' as const,
      unit_assigned: null,
      destination: null,
      eta_minutes: null,
      rationale: null
    }));

  const allLanes = [...dispatches, ...syntheticRecommended];

  const handleExecute = (unitType: string) => {
    if (!hasNotifiedBackend && onFirstExecute) {
      onFirstExecute();
      setHasNotifiedBackend(true);
    }
    setExecutingUnits(prev => ({ ...prev, [unitType]: 'executing' }));
    setTimeout(() => {
      setExecutingUnits(prev => ({ ...prev, [unitType]: 'done' }));
    }, 1500);
  };

  const handleBroadcast = () => {
    setBroadcastState('playing');
    setActiveLangIndex(0);
  };

  // Simulate sequential playing of broadcast languages
  useEffect(() => {
    if (onBroadcastStateChange) {
      onBroadcastStateChange(broadcastState === 'playing');
    }
    
    if (broadcastState === 'playing' && outboundMessages.length > 0) {
      if (activeLangIndex < outboundMessages.length) {
        const timer = setTimeout(() => {
          setActiveLangIndex(prev => prev + 1);
        }, 2500); // 2.5s per language line
        return () => clearTimeout(timer);
      } else {
        setBroadcastState('sent');
      }
    }
  }, [broadcastState, activeLangIndex, outboundMessages.length, onBroadcastStateChange]);

  const getStatusColor = (status: string, localState?: string) => {
    if (localState === 'done') return 'bg-blue-500/10 border-blue-500/50 text-blue-600 dark:text-blue-400';
    if (status === 'dispatched') return 'bg-emerald-500/10 border-emerald-500/50 text-emerald-600 dark:text-emerald-400';
    if (status === 'confirmed') return 'bg-blue-500/10 border-blue-500/50 text-blue-600 dark:text-blue-400';
    return 'bg-black/5 dark:bg-white/5 border-black/20 dark:border-white/20 text-black/50 dark:text-white/50';
  };

  return (
    <div className="flex flex-col h-full tech-glass">
      <div className="border-b dark:border-white/10 border-black/10 p-3 px-4 flex justify-between items-center dark:bg-black/40 bg-zinc-100">
        <h2 className="text-xs font-mono uppercase tracking-widest dark:text-white/50 text-slate-500 font-semibold">Response Actions</h2>
        <div className="text-[10px] font-mono dark:text-white/30 text-slate-400">{allLanes.length} ACTIONS</div>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {allLanes.length === 0 ? (
          <div className="dark:text-white/20 text-black/30 italic font-mono text-xs text-center mt-10">Awaiting tactical recommendations...</div>
        ) : (
          allLanes.map((d) => {
            const localState = executingUnits[d.unit_type];
            const isConfirmed = d.status === 'confirmed' || d.status === 'dispatched' || localState === 'done';
            
            return (
              <div key={d.id} className={cn("p-3 rounded-sm border transition-all animate-in fade-in zoom-in-95 duration-300", getStatusColor(d.status, localState))}>
                <div className="flex justify-between items-center mb-2">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs font-bold uppercase tracking-widest">{d.unit_type}</span>
                    {d.status === 'dispatched' && <span className="flex h-2 w-2 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.8)] animate-pulse"></span>}
                  </div>
                  
                  <div className="flex items-center gap-3">
                    <div className="text-[10px] font-mono uppercase dark:text-white/60 text-black/60 font-semibold">
                      {isConfirmed ? 'CONFIRMED' : 'RECOMMENDED'}
                    </div>
                    {isConfirmed ? (
                      <div className="flex items-center gap-1 text-[10px] uppercase font-mono font-bold text-emerald-600 dark:text-emerald-400">
                        <Check className="w-3.5 h-3.5" />
                        Done
                      </div>
                    ) : (
                      <button 
                        onClick={() => handleExecute(d.unit_type)}
                        disabled={localState === 'executing'}
                        className="text-[10px] uppercase font-mono font-bold tracking-widest bg-emerald-500 hover:bg-emerald-400 text-white dark:text-zinc-950 px-2.5 py-1 rounded-sm shadow-[0_0_10px_rgba(16,185,129,0.3)] transition-all flex items-center gap-1.5 min-w-[70px] justify-center"
                      >
                        {localState === 'executing' ? (
                          <><Loader2 className="w-3 h-3 animate-spin" /> Executing</>
                        ) : (
                          <span className="animate-[pulse_2s_ease-in-out_infinite] inline-block">[EXECUTE]</span>
                        )}
                      </button>
                    )}
                  </div>
                </div>

                {d.unit_assigned && (
                  <div className="text-[11px] font-bold dark:text-white/90 text-black/90 mb-1 opacity-80">Unit: {d.unit_assigned}</div>
                )}

                {d.rationale && (
                  <div className="text-xs dark:text-white/60 text-black/60 leading-relaxed mb-3 border-l-[1px] dark:border-white/20 border-black/20 pl-2">
                    {d.rationale}
                  </div>
                )}

                <div className="flex items-center gap-4 text-[10px] font-mono pt-2 border-t dark:border-white/5 border-black/10 mt-2">
                  {d.destination && (
                    <div className="flex items-center gap-1.5 opacity-70">
                      <Navigation className="w-3 h-3" />
                      <span className="truncate max-w-[150px]">{d.destination}</span>
                    </div>
                  )}
                  {d.eta_minutes !== null && (
                    <div className="flex items-center gap-1.5 ml-auto opacity-70">
                      <Clock className="w-3 h-3" />
                      <span>ETA: {d.eta_minutes}m</span>
                    </div>
                  )}
                </div>
              </div>
            );
          })
        )}

        {/* Evacuation Broadcast Card */}
        {outboundMessages.length > 0 && (
          <div className="p-3 rounded-sm border transition-all animate-in fade-in zoom-in-95 duration-500 border-amber-500/50 bg-amber-500/10">
            <div className="flex items-center gap-2 mb-3">
              <span className="text-amber-500 font-bold">⚠️</span>
              <span className="font-mono text-[11px] font-bold tracking-widest uppercase text-amber-500">Evacuation Broadcast</span>
            </div>
            
            <div className="space-y-2 font-mono text-xs mb-4">
              {outboundMessages.map((msg, index) => {
                const isPlaying = broadcastState === 'playing' && index === activeLangIndex;
                const isDone = broadcastState === 'sent' || (broadcastState === 'playing' && index < activeLangIndex);
                
                return (
                  <div key={msg.id} className={cn("flex items-center justify-between group", isPlaying ? "text-amber-500" : isDone ? "text-emerald-500" : "dark:text-white/60 text-black/60")}>
                    <div className="flex items-center gap-2 truncate pr-4">
                      <span className="uppercase font-bold shrink-0">{msg.language}</span>
                      <span className="truncate opacity-80">"{msg.original_text}"</span>
                    </div>
                    <div className="shrink-0 flex items-center text-[10px] font-bold tracking-widest gap-1.5">
                      {isDone ? (
                        <>✓ SENT</>
                      ) : isPlaying ? (
                        <span className="flex items-center gap-1.5 text-amber-500 font-bold">
                          <div className="flex items-center gap-[2px] h-3 mr-1">
                             <div className="w-1 h-full bg-amber-500 animate-[pulse_0.8s_ease-in-out_infinite]"></div>
                             <div className="w-1 h-1/2 bg-amber-500 animate-[pulse_1.2s_ease-in-out_infinite_0.2s]"></div>
                             <div className="w-1 h-3/4 bg-amber-500 animate-[pulse_1.0s_ease-in-out_infinite_0.4s]"></div>
                          </div>
                          PLAYING
                        </span>
                      ) : (
                        <span className="opacity-50 flex items-center gap-1"><Play className="w-3 h-3" fill="currentColor" /> READY</span>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
            
            <div className="pt-3 border-t border-amber-500/30 flex justify-between items-center">
               <span className="text-[10px] font-mono text-amber-600 dark:text-amber-500/60 uppercase">elevenlabs-tts</span>
               {broadcastState === 'sent' ? (
                 <div className="flex items-center gap-1.5 text-[10px] uppercase font-mono font-bold text-emerald-600 dark:text-emerald-400">
                    <Check className="w-3.5 h-3.5" /> Done
                 </div>
               ) : (
                 <button
                   onClick={handleBroadcast}
                   disabled={broadcastState !== 'ready'}
                   className="text-[10px] uppercase font-mono font-bold tracking-widest bg-amber-500 hover:bg-amber-400 text-black px-3 py-1.5 rounded-sm shadow-[0_0_15px_rgba(245,158,11,0.4)] transition-all flex items-center gap-1.5 min-w-[120px] justify-center"
                 >
                   {broadcastState === 'playing' ? (
                     <><Loader2 className="w-3 h-3 animate-spin"/> Broadcasting</>
                   ) : (
                     <span className="animate-[pulse_2s_ease-in-out_infinite] inline-block flex items-center gap-1.5"><Volume2 className="w-3 h-3" /> [BROADCAST]</span>
                   )}
                 </button>
               )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

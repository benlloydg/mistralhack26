import { cn } from "@/lib/utils";
import { AgentLog } from "@/lib/types";
import { useEffect, useRef } from "react";

export function AgentTerminal({ logs }: { logs: AgentLog[] }) {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.scrollTo({
        top: 0,
        behavior: 'smooth'
      });
    }
  }, [logs]);

  const getColor = (colorStr: string) => {
    switch (colorStr) {
      case 'red': return 'text-red-500';
      case 'amber': return 'text-amber-500';
      case 'green': return 'text-emerald-500';
      case 'purple': return 'text-purple-500';
      case 'blue': default: return 'text-blue-500';
    }
  };

  const getBgColor = (colorStr: string) => {
    switch (colorStr) {
      case 'red': return 'bg-red-500';
      case 'amber': return 'bg-amber-500';
      case 'green': return 'bg-emerald-500';
      case 'purple': return 'bg-purple-500';
      case 'blue': default: return 'bg-blue-500';
    }
  };

  const getModelName = (agent: string) => {
    switch (agent.toLowerCase()) {
      case 'triageagent': 
      case 'evidencefusion': 
      case 'casematchagent':
        return 'mistral-lg';
      case 'visionagent': 
        return 'pixtral-12b';
      case 'voiceagent': 
      case 'prioritybroadcast':
        return '11labs-scribe';
      default: 
        return 'core';
    }
  };

  return (
    <div className="flex flex-col h-full tech-glass">
      <div className="border-b dark:border-white/10 border-black/10 p-3 px-4 flex items-center justify-between dark:bg-black/40 bg-zinc-100">
        <div className="flex items-center gap-3">
          <div className="flex gap-1.5">
            <div className="w-2.5 h-2.5 rounded-full bg-red-500/80"></div>
            <div className="w-2.5 h-2.5 rounded-full bg-amber-500/80"></div>
            <div className="w-2.5 h-2.5 rounded-full bg-emerald-500/80"></div>
          </div>
          <h2 className="text-xs font-mono uppercase tracking-widest dark:text-white/50 text-slate-500 font-semibold">Dispatch // Agent Terminal</h2>
        </div>
        <div className="text-[10px] font-mono dark:text-white/30 text-slate-400">sys.log</div>
      </div>
      
      <div 
        ref={containerRef}
        className="flex-1 overflow-y-auto p-4 space-y-3 font-mono text-[11px] sm:text-xs leading-relaxed"
      >
        {/* Blinking Cursor */}
        <div className="flex items-center gap-2 mb-3 pb-3 border-b dark:border-white/5 border-black/5 opacity-60 animate-in fade-in duration-300">
          <span className="dark:text-white/30 text-black/30 font-bold">&gt;</span>
          <span className="w-1.5 h-3.5 dark:bg-white/50 bg-black/50 animate-pulse"></span>
        </div>

        {logs.length === 0 ? (
          <div className="dark:text-white/20 text-black/30 italic">Awaiting telemetry...</div>
        ) : (
          [...logs].reverse().map((log, i) => (
            <div 
              key={log.id} 
              className={cn(
                "flex flex-col gap-1.5 pb-3 mb-3 animate-in fade-in slide-in-from-top-2 duration-300",
                i !== logs.length - 1 && "border-b dark:border-white/5 border-black/5",
                log.display_flash && i === 0 && "animate-pulse"
              )}
            >
              <div className="flex items-center gap-2">
                <span className="dark:text-white/30 text-black/40">[{new Date(log.created_at).toISOString().substring(11, 23)}]</span>
                <span className="uppercase dark:text-white/50 text-black/60 font-bold px-1.5 py-0.5 rounded dark:bg-white/5 bg-black/5 border dark:border-white/10 border-black/10 tracking-wider">
                  {log.agent}
                </span>
                <span className="text-[10px] dark:text-white/30 text-black/30">•</span>
                <span className="text-[10px] dark:text-cyan-500/60 text-cyan-600/80 uppercase tracking-widest">{getModelName(log.agent)}</span>
                <span className="text-[10px] dark:text-white/30 text-black/30">•</span>
                <span className={cn("flex items-center gap-1.5 uppercase font-semibold", getColor(log.display_color))}>
                  <span className={cn("w-1.5 h-1.5 rounded-full shadow-[0_0_8px_currentColor]", getBgColor(log.display_color))}></span>
                  {log.event_type}
                </span>
              </div>
              <div className="dark:text-white/80 text-black/80 pl-[125px] sm:pl-[145px]">
                {log.message}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

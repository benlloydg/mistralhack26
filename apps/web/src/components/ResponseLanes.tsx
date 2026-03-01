import { Dispatch } from "@/lib/types";
import { cn } from "@/lib/utils";
import { Check, Clock, Navigation } from "lucide-react";

export function ResponseLanes({ dispatches }: { dispatches: Dispatch[] }) {
  
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'dispatched': return 'bg-emerald-500/10 border-emerald-500/50 text-emerald-600 dark:text-emerald-400';
      case 'confirmed': return 'bg-blue-500/10 border-blue-500/50 text-blue-600 dark:text-blue-400';
      case 'recommended': default: return 'bg-black/5 dark:bg-white/5 border-black/20 dark:border-white/20 text-black/50 dark:text-white/50';
    }
  };

  return (
    <div className="flex flex-col h-full tech-glass">
      <div className="border-b dark:border-white/10 border-black/10 p-3 px-4 flex justify-between items-center dark:bg-black/40 bg-zinc-100">
        <h2 className="text-xs font-mono uppercase tracking-widest dark:text-white/50 text-slate-500 font-semibold">Deployments // Logistics</h2>
        <div className="text-[10px] font-mono dark:text-white/30 text-slate-400">{dispatches.length} UNITS</div>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {dispatches.length === 0 ? (
          <div className="dark:text-white/20 text-black/30 italic font-mono text-xs text-center mt-10">Awaiting tactical recommendations...</div>
        ) : (
          dispatches.map((d) => (
            <div key={d.id} className={cn("p-3 rounded-sm border transition-all", getStatusColor(d.status))}>
              <div className="flex justify-between items-start mb-2">
                <div className="flex items-center gap-2">
                  <span className="font-mono text-xs font-bold uppercase tracking-widest">{d.unit_type}</span>
                  {d.status === 'dispatched' && <span className="flex h-2 w-2 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.8)]"></span>}
                </div>
                <div className="text-[10px] font-mono px-1.5 py-0.5 rounded dark:bg-black/30 bg-white/50 border dark:border-white/5 border-black/10 uppercase">
                  {d.status}
                </div>
              </div>

              {d.unit_assigned && (
                <div className="text-sm font-semibold dark:text-white/90 text-black/90 mb-1">Unit: {d.unit_assigned}</div>
              )}

              {d.rationale && (
                <div className="text-xs dark:text-white/60 text-black/60 leading-relaxed mb-3 border-l-[1px] dark:border-white/20 border-black/20 pl-2">
                  {d.rationale}
                </div>
              )}

              <div className="flex items-center gap-4 text-[10px] font-mono mt-3 pt-3 border-t dark:border-white/5 border-black/10">
                {d.destination && (
                  <div className="flex items-center gap-1.5">
                    <Navigation className="w-3 h-3 opacity-50" />
                    <span className="truncate max-w-[150px]">{d.destination}</span>
                  </div>
                )}
                {d.eta_minutes !== null && (
                  <div className="flex items-center gap-1.5 ml-auto">
                    <Clock className="w-3 h-3 opacity-50" />
                    <span>ETA: {d.eta_minutes}m</span>
                  </div>
                )}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

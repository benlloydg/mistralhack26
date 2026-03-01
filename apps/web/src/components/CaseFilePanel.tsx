import { IncidentState } from "@/lib/types";
import { SeverityBadge } from "./SeverityBadge";
import { MapPin, Users, AlertTriangle, Flame } from "lucide-react";

export function CaseFilePanel({ state }: { state: IncidentState | null }) {
  if (!state) {
    return (
      <div className="flex flex-col h-full tech-glass p-6 items-center justify-center dark:text-white/30 text-black/40 font-mono text-sm">
        Initializing Case File...
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full tech-glass">
      <div className="border-b dark:border-white/10 border-black/10 p-3 px-4 flex justify-between items-center dark:bg-black/40 bg-zinc-100">
        <h2 className="text-xs font-mono uppercase tracking-widest dark:text-white/50 text-slate-500 font-semibold">Triage // Case File</h2>
        <div className="text-xs font-mono font-bold text-blue-500">{state.case_id}</div>
      </div>

      <div className="p-5 flex-1 overflow-y-auto space-y-6">
        {/* Header Section */}
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight uppercase dark:text-white/90 text-black/90">
              {state.status === 'intake' 
                ? 'INCOMING CALL' 
                : state.incident_type 
                  ? `${state.incident_type.replace(/_/g, ' ')}${state.hazard_flags.includes('engine_fire') ? ' + FIRE' : ''}` 
                  : 'UNCLASSIFIED INCIDENT'}
            </h1>
            <div className="flex items-center gap-2 mt-2 dark:text-white/60 text-slate-600 font-mono text-xs">
              <MapPin className="w-3.5 h-3.5" />
              <span>{state.location_normalized || state.location_raw || 'Awaiting location data...'}</span>
            </div>
          </div>
          <SeverityBadge severity={state.severity} />
        </div>

        {/* Metrics Grid */}
        <div className="grid grid-cols-2 gap-3">
          <div className="border dark:border-white/10 border-black/10 rounded-sm p-3 dark:bg-white/5 bg-black/5">
            <div className="text-[10px] uppercase font-mono dark:text-white/40 text-black/50 mb-1">Callers</div>
            <div className="text-lg font-mono font-bold">{state.caller_count}</div>
          </div>
          <div className="border dark:border-white/10 border-black/10 rounded-sm p-3 dark:bg-white/5 bg-black/5">
            <div className="text-[10px] uppercase font-mono dark:text-white/40 text-black/50 mb-1 flex items-center gap-1.5">
              <Users className="w-3 h-3" /> People Est.
            </div>
            <div className="text-lg font-mono font-bold">{state.people_count_estimate || '--'}</div>
          </div>
        </div>

        {/* Flags Section */}
        <div className="space-y-4">
          {state.hazard_flags.length > 0 && (
            <div>
              <div className="text-xs font-mono uppercase text-red-400 mb-2 flex items-center gap-1.5"><Flame className="w-3.5 h-3.5" /> Active Hazards</div>
              <div className="flex flex-wrap gap-2">
                {state.hazard_flags.map((h, idx) => (
                  <span 
                    key={h} 
                    className="bg-red-500/10 border border-red-500/30 text-red-500 text-[10px] font-mono uppercase px-2 py-1 rounded-sm animate-in fade-in zoom-in-75 duration-300 fill-mode-both"
                    style={{ animationDelay: `${idx * 150}ms` }}
                  >
                    {h.replace(/_/g, ' ')}
                  </span>
                ))}
              </div>
            </div>
          )}

          {state.injury_flags.length > 0 && (
            <div>
              <div className="text-xs font-mono uppercase text-amber-400 mb-2 flex items-center gap-1.5"><AlertTriangle className="w-3.5 h-3.5" /> Injury Flags</div>
              <div className="flex flex-wrap gap-2">
                {state.injury_flags.map((i, idx) => (
                  <span 
                    key={i} 
                    className="bg-amber-500/10 border border-amber-500/30 text-amber-500 text-[10px] font-mono uppercase px-2 py-1 rounded-sm animate-in fade-in zoom-in-75 duration-300 fill-mode-both"
                    style={{ animationDelay: `${idx * 150}ms` }}
                  >
                    {i.replace(/_/g, ' ')}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Operator Summary */}
        {state.operator_summary && (
          <div className="mt-8 pt-6 border-t dark:border-white/10 border-black/10">
            <div className="text-[10px] font-mono uppercase dark:text-white/40 text-black/50 mb-2">Operator Summary</div>
            <p className="text-sm leading-relaxed dark:text-white/80 text-black/80 border-l-2 border-emerald-500 pl-3">
              {state.operator_summary}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

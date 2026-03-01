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
      <div className="p-4 flex-1 overflow-y-auto flex flex-col justify-center">
        {/* Header Section */}
        <div className="flex items-start justify-between mb-3">
          <div>
            <div className="text-[10px] font-mono uppercase tracking-widest dark:text-white/50 text-slate-500 font-semibold mb-1">
              TRIAGE // CASE FILE
            </div>
            <h1 className="text-xl font-bold tracking-tight uppercase dark:text-white/90 text-black/90 leading-none mb-2">
              {state.status === 'intake' 
                ? 'SCENE MONITORING' 
                : state.incident_type 
                  ? `${state.incident_type.replace(/_/g, ' ')}${state.hazard_flags.includes('engine_fire') ? ' + FIRE' : ''}` 
                  : 'UNCLASSIFIED INCIDENT'}
            </h1>
            <div className="flex items-center gap-2 dark:text-white/60 text-slate-600 font-mono text-[11px]">
              <MapPin className="w-3 h-3" />
              <span>{state.location_normalized || state.location_raw || 'Market St & 5th St'}</span>
              <span className="opacity-50">·</span>
              <span className="uppercase tracking-widest">SPEAKERS: {state.caller_count}</span>
              <span className="opacity-50">·</span>
              <span className="uppercase tracking-widest flex items-center gap-1"><Users className="w-3 h-3"/> {state.people_count_estimate || '--'}</span>
            </div>
          </div>
          <div className="flex flex-col items-end gap-2">
            <div className="text-[10px] font-mono font-bold text-blue-500 tracking-widest">{state.case_id}</div>
            <SeverityBadge severity={state.severity} />
          </div>
        </div>

        {/* Combined Flags Row */}
        {(state.hazard_flags.length > 0 || state.injury_flags.length > 0) && (
          <div className="flex flex-wrap gap-1.5 items-center">
            {state.hazard_flags.length > 0 && <AlertTriangle className="w-3.5 h-3.5 text-red-500 mr-1 animate-pulse" />}
            {state.hazard_flags.map((h, idx) => (
              <span 
                key={h} 
                className="bg-red-500/20 border border-red-500/50 text-red-500 font-bold tracking-widest text-[9px] font-mono uppercase px-2 py-0.5 rounded-sm animate-in fade-in zoom-in-75 duration-300 fill-mode-both shadow-[0_0_10px_rgba(239,68,68,0.3)]"
                style={{ animationDelay: `${idx * 150}ms` }}
              >
                {h.replace(/_/g, ' ')}
              </span>
            ))}
            {state.injury_flags.map((i, idx) => (
              <span 
                key={i} 
                className="bg-red-500/20 border border-red-500/50 text-red-500 font-bold tracking-widest text-[9px] font-mono uppercase px-2 py-0.5 rounded-sm animate-in fade-in zoom-in-75 duration-300 fill-mode-both shadow-[0_0_10px_rgba(239,68,68,0.3)]"
                style={{ animationDelay: `${(state.hazard_flags.length + idx) * 150}ms` }}
              >
                {i.replace(/_/g, ' ')}
              </span>
            ))}
          </div>
        )}

        {/* Operator Summary */}
        {state.operator_summary && (
          <div className="mt-6 pt-4 border-t dark:border-white/10 border-black/10">
            <div className="text-[10px] font-mono uppercase dark:text-white/40 text-black/50 mb-2">Operator Summary</div>
            <p className="text-xs leading-relaxed dark:text-white/80 text-black/80 border-l-2 border-emerald-500 pl-3">
              {state.operator_summary}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

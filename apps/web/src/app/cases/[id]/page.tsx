import { supabase } from '@/lib/supabase';
import { IncidentState, AgentLog, Transcript, Dispatch } from '@/lib/types';
import { ThemeToggle } from '@/components/ThemeToggle';
import { ShieldAlert, MapPin, Users, Activity, CheckCircle2, Navigation, Clock, Flame, AlertTriangle, FileText, ActivitySquare, TerminalSquare } from 'lucide-react';
import { cn } from '@/lib/utils';

// Helper to disable cache to ensure we get fresh state for the report
export const revalidate = 0;

export default async function CaseReportPage({ params }: { params: { id: string } }) {
  const caseId = params.id;
  
  // Parallel fetch all case data
  const [stateRes, transcriptRes, logsRes, dispatchRes] = await Promise.all([
    supabase.from('incident_state').select('*').eq('case_id', caseId).single(),
    supabase.from('transcripts').select('*').eq('case_id', caseId).order('created_at', { ascending: true }),
    supabase.from('agent_logs').select('*').eq('case_id', caseId).order('created_at', { ascending: true }),
    supabase.from('dispatches').select('*').eq('case_id', caseId).order('created_at', { ascending: true })
  ]);

  const state = stateRes.data as IncidentState;
  const transcripts = (transcriptRes.data || []) as Transcript[];
  const agentLogs = (logsRes.data || []) as AgentLog[];
  const dispatches = (dispatchRes.data || []) as Dispatch[];

  if (!state) {
    return (
      <div className="h-screen w-full flex flex-col items-center justify-center dark:bg-zinc-950 bg-zinc-50 font-mono text-sm dark:text-white/50 text-black/50">
        <div>ERROR 404 // CASE RECORD NOT FOUND</div>
        <div className="text-[10px] mt-2 opacity-50">{caseId}</div>
      </div>
    );
  }

  const getSeverityColor = (severity: string) => {
    switch(severity?.toLowerCase()) {
      case 'critical': return 'text-red-500 border-red-500 bg-red-500/10';
      case 'high': return 'text-orange-500 border-orange-500 bg-orange-500/10';
      case 'medium': return 'text-amber-500 border-amber-500 bg-amber-500/10';
      default: return 'text-emerald-500 border-emerald-500 bg-emerald-500/10';
    }
  };

  const getModelName = (agent: string) => {
    switch (agent.toLowerCase()) {
      case 'triageagent': 
      case 'evidencefusion': 
      case 'casematchagent': return 'mistral-large';
      case 'visionagent': return 'pixtral-12b';
      case 'voiceagent': 
      case 'prioritybroadcast': return 'elevenlabs-scribe';
      default: return 'triage-os-core';
    }
  };

  return (
    <div className="min-h-screen dark:bg-zinc-950 bg-zinc-50 selection:bg-blue-500/30 overflow-x-hidden relative">
      {/* Top Header */}
      <header className="sticky top-0 z-50 dark:bg-zinc-950/80 bg-zinc-50/80 backdrop-blur-md border-b dark:border-white/10 border-black/10 px-6 py-4 flex justify-between items-center">
        <div className="flex items-center gap-4">
          <div className="text-xl font-bold tracking-tight uppercase flex items-center gap-2 dark:text-white text-black">
            <span className="w-3 h-3 rounded-full bg-blue-500 shadow-[0_0_10px_rgba(59,130,246,0.8)]"></span>
            Dispatch
          </div>
          <div className="h-4 w-[1px] dark:bg-white/20 bg-black/20 mx-2"></div>
          <div className="font-mono text-xs font-bold tracking-widest dark:text-white/60 text-slate-500 uppercase">
            After-Action Report // {caseId}
          </div>
        </div>
        <div className="flex items-center gap-4">
          <div className="font-mono text-[10px] tracking-widest uppercase dark:text-emerald-400 text-emerald-600 border dark:border-emerald-500/30 border-emerald-600/30 dark:bg-emerald-500/10 bg-emerald-600/10 px-2 py-1 rounded-sm flex items-center gap-2">
            <CheckCircle2 className="w-3 h-3" />
            Case Closed
          </div>
          <ThemeToggle />
        </div>
      </header>

      <main className="max-w-5xl mx-auto p-6 md:p-12 flex flex-col gap-12">
        
        {/* Dossier Header: High Level Summary */}
        <section className="flex flex-col gap-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
          <div>
            <h1 className="text-4xl md:text-5xl font-bold tracking-tight uppercase dark:text-white text-black mb-4">
              {state.incident_type ? state.incident_type.replace(/_/g, ' ') : 'Unclassified Incident'}
            </h1>
            <p className="font-mono text-sm leading-relaxed dark:text-white/60 text-black/60 max-w-2xl border-l-[2px] border-blue-500 pl-4 py-1">
              {state.operator_summary || "No executive summary automatically generated for this incident."}
            </p>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="dark:bg-white/5 bg-black/5 border dark:border-white/10 border-black/10 p-4 rounded-sm flex flex-col gap-2">
              <span className="text-[10px] font-mono tracking-widest uppercase dark:text-white/40 text-black/50">Final Severity</span>
              <span className={cn("text-sm font-mono font-bold uppercase tracking-widest px-2 py-1 rounded-sm self-start border", getSeverityColor(state.severity))}>
                {state.severity || 'Unknown'}
              </span>
            </div>
            <div className="dark:bg-white/5 bg-black/5 border dark:border-white/10 border-black/10 p-4 rounded-sm flex flex-col gap-2">
              <span className="text-[10px] font-mono tracking-widest uppercase dark:text-white/40 text-black/50">Normalized Location</span>
              <span className="text-sm font-semibold dark:text-white/90 text-black/90 flex items-center gap-2">
                <MapPin className="w-4 h-4 dark:text-blue-400 text-blue-600" />
                {state.location_normalized || 'Unknown'}
              </span>
            </div>
            <div className="dark:bg-white/5 bg-black/5 border dark:border-white/10 border-black/10 p-4 rounded-sm flex flex-col gap-2">
              <span className="text-[10px] font-mono tracking-widest uppercase dark:text-white/40 text-black/50">Est. Casualties</span>
              <span className="text-sm font-semibold dark:text-white/90 text-black/90 flex items-center gap-2">
                <Users className="w-4 h-4 dark:text-blue-400 text-blue-600" />
                {state.people_count_estimate || 0}
              </span>
            </div>
            <div className="dark:bg-white/5 bg-black/5 border dark:border-white/10 border-black/10 p-4 rounded-sm flex flex-col gap-2">
              <span className="text-[10px] font-mono tracking-widest uppercase dark:text-white/40 text-black/50">Callers Processed</span>
              <span className="text-sm font-semibold dark:text-white/90 text-black/90 flex items-center gap-2">
                <Activity className="w-4 h-4 dark:text-blue-400 text-blue-600" />
                {state.caller_count || 0}
              </span>
            </div>
          </div>

          {(state.hazard_flags.length > 0 || state.injury_flags.length > 0) && (
            <div className="flex flex-col md:flex-row gap-6">
              {state.hazard_flags.length > 0 && (
                <div className="flex-1 flex flex-col gap-3">
                   <div className="text-xs font-mono uppercase text-red-500 font-bold flex items-center gap-2">
                     <Flame className="w-4 h-4" /> Active Hazards Logged
                   </div>
                   <div className="flex flex-wrap gap-2">
                     {state.hazard_flags.map((h) => (
                       <span key={h} className="bg-red-500/10 border border-red-500/30 text-red-500 text-xs font-mono uppercase px-2 py-1 rounded-sm">
                         {h.replace(/_/g, ' ')}
                       </span>
                     ))}
                   </div>
                </div>
              )}
              {state.injury_flags.length > 0 && (
                <div className="flex-1 flex flex-col gap-3">
                   <div className="text-xs font-mono uppercase text-amber-500 font-bold flex items-center gap-2">
                     <AlertTriangle className="w-4 h-4" /> Injury Flags Validated
                   </div>
                   <div className="flex flex-wrap gap-2">
                     {state.injury_flags.map((i) => (
                       <span key={i} className="bg-amber-500/10 border border-amber-500/30 text-amber-500 text-xs font-mono uppercase px-2 py-1 rounded-sm">
                         {i.replace(/_/g, ' ')}
                       </span>
                     ))}
                   </div>
                </div>
              )}
            </div>
          )}
        </section>

        <hr className="dark:border-white/10 border-black/10" />

        {/* Action Plan & Dispatches */}
        <section className="flex flex-col gap-6">
          <div className="flex items-center gap-3 dark:text-white text-black">
            <ActivitySquare className="w-5 h-5 dark:text-blue-400 text-blue-600" />
            <h2 className="text-xl font-bold tracking-tight uppercase">Confirmed Deployments</h2>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {dispatches.length === 0 ? (
              <div className="col-span-2 p-6 border dark:border-white/10 border-black/10 border-dashed text-center font-mono text-sm dark:text-white/40 text-black/40">
                NO UNITS DISPATCHED
              </div>
            ) : (
              dispatches.map(d => (
                <div key={d.id} className="p-4 rounded-sm border dark:border-white/10 border-black/10 dark:bg-white/5 bg-black/5 flex flex-col gap-3">
                  <div className="flex justify-between items-center">
                    <span className="font-mono text-sm font-bold uppercase tracking-widest dark:text-white text-black">
                      {d.unit_type}
                    </span>
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded uppercase font-bold tracking-widest bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20">
                      {d.status}
                    </span>
                  </div>
                  {d.unit_assigned && (
                    <div className="text-sm font-semibold dark:text-white/80 text-black/80">Unit: {d.unit_assigned}</div>
                  )}
                  {d.rationale && (
                    <div className="text-xs dark:text-white/60 text-black/60 leading-relaxed border-l-[1px] dark:border-white/20 border-black/20 pl-2">
                      {d.rationale}
                    </div>
                  )}
                  <div className="flex items-center justify-between text-[10px] font-mono mt-2 pt-2 border-t dark:border-white/10 border-black/10 dark:text-white/50 text-black/50">
                    <div className="flex items-center gap-1.5 truncate max-w-[200px]">
                      <Navigation className="w-3 h-3 shrink-0" />
                      <span className="truncate">{d.destination || 'Unspecified'}</span>
                    </div>
                    {d.eta_minutes && (
                      <div className="flex items-center gap-1.5 shrink-0">
                        <Clock className="w-3 h-3" />
                        ETA: {d.eta_minutes}m
                      </div>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        </section>

        <hr className="dark:border-white/10 border-black/10" />

        {/* Transcripts Record */}
        <section className="flex flex-col gap-6">
          <div className="flex items-center gap-3 dark:text-white text-black">
            <FileText className="w-5 h-5 dark:text-blue-400 text-blue-600" />
            <h2 className="text-xl font-bold tracking-tight uppercase">Communications Transcript</h2>
          </div>
          
          <div className="flex flex-col gap-6 bg-white dark:bg-black border dark:border-white/10 border-black/10 p-4 md:p-6 rounded-sm">
            {transcripts.length === 0 ? (
               <div className="text-center font-mono text-sm dark:text-white/40 text-black/40 py-8">
                 NO COMMUNICATIONS RECORDED
               </div>
            ) : (
              transcripts.map(t => {
                const isDispatch = (t.caller_label || t.caller_id)?.toLowerCase() === 'dispatch';
                return (
                  <div key={t.id} className={cn("flex flex-col gap-1.5", isDispatch && "items-end text-right")}>
                    <div className={cn("flex items-center gap-2", isDispatch && "flex-row-reverse")}>
                      <span className="text-[10px] font-mono dark:text-white/30 text-black/40">[{new Date(t.created_at).toISOString().substring(11, 19)}]</span>
                      <span className={cn(
                        "text-[10px] uppercase font-mono px-2 py-0.5 rounded-sm font-bold tracking-wider",
                        isDispatch ? "bg-cyan-500/10 text-cyan-600 dark:text-cyan-400 border border-cyan-500/20" :
                        "dark:bg-white/10 bg-black/5 dark:text-white/60 text-black/60"
                      )}>
                        {isDispatch ? `DISPATCH → ${t.language.toUpperCase()}` : (t.caller_label || t.caller_id)}
                      </span>
                      {!isDispatch && t.language !== 'en' && t.translated_text && (
                        <span className="text-[10px] font-mono text-amber-500 border border-amber-500/30 px-1 rounded-sm bg-amber-500/10">
                          RAW: {t.language.toUpperCase()}
                        </span>
                      )}
                    </div>
                    
                    <div className={cn("text-sm leading-relaxed dark:text-white/90 text-black/90 max-w-3xl", isDispatch ? "pr-[130px]" : "pl-[100px]")}>
                      {isDispatch && t.original_text && t.translated_text ? (
                        <div className="flex flex-col gap-1 mt-1">
                          <div className="text-cyan-700 dark:text-cyan-400">"{t.original_text}"</div>
                          <div className="dark:text-white/50 text-black/50 italic text-[11px] mt-1">Translation: "{t.translated_text}"</div>
                        </div>
                      ) : (
                        t.translated_text || t.original_text
                      )}
                      
                      {t.entities && t.entities.length > 0 && !isDispatch && (
                        <div className="mt-2 flex flex-wrap gap-1.5">
                          {t.entities.map(entity => (
                            <span key={`${t.id}-${entity}`} className="text-[10px] font-mono px-1.5 py-0.5 bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20 rounded">
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
        </section>

        <hr className="dark:border-white/10 border-black/10" />

        {/* System Telemetry / Agent Logs */}
        <section className="flex flex-col gap-6">
          <div className="flex items-center gap-3 dark:text-white text-black">
            <TerminalSquare className="w-5 h-5 dark:text-blue-400 text-blue-600" />
            <h2 className="text-xl font-bold tracking-tight uppercase">System Telemetry & Audit Trail</h2>
          </div>
          
          <div className="bg-black text-white p-6 rounded-sm font-mono text-xs overflow-x-auto shadow-inner border dark:border-white/20 border-black/20">
            {agentLogs.length === 0 ? (
               <div className="text-white/40 italic">NO AUDIT LOGS FOUND</div>
            ) : (
              <div className="flex flex-col min-w-max">
                {agentLogs.map((log, i) => (
                  <div key={log.id} className={cn("flex flex-col py-2", i !== agentLogs.length - 1 && "border-b border-white/10")}>
                    <div className="flex items-center gap-3 mb-1">
                      <span className="text-white/40">[{new Date(log.created_at).toISOString().substring(11, 23)}]</span>
                      <span className="uppercase text-white/70 font-bold px-1.5 py-0.5 rounded bg-white/10 tracking-widest w-[160px] text-center">
                        {log.agent}
                      </span>
                      <span className="text-[10px] text-cyan-400/80 uppercase tracking-widest w-[120px]">
                        {getModelName(log.agent)}
                      </span>
                      <span className="uppercase font-semibold text-blue-400 w-[180px]">
                        {log.event_type}
                      </span>
                      <span className="text-white/90">
                        {log.message}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </section>

      </main>
    </div>
  );
}

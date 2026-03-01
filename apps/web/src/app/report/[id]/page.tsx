import { notFound } from 'next/navigation';
import { ThemeToggle } from '@/components/ThemeToggle';
import { ShieldAlert, MapPin, Users, Activity, CheckCircle2, Navigation, Clock, Flame, AlertTriangle, FileText, ActivitySquare, TerminalSquare, Video } from 'lucide-react';
import { cn } from '@/lib/utils';
import Image from 'next/image';

// Report JSON Type definitions based on contract
interface ReportData {
  case_id: string;
  generated_at: string;
  warning: string | null;
  header: {
    case_id: string;
    incident_type: string;
    location: string;
    severity: string;
    status: string;
    duration_seconds: number;
    speaker_count: number;
    languages: string[];
    audio_segments: number;
    vision_frames: number;
    outcome: string;
  };
  timeline: {
    t: string;
    timestamp: string;
    agent: string;
    model: string | null;
    event_type: string;
    message: string;
    severity_indicator: string;
    color: string;
    flash: boolean;
  }[];
  evidence_sources: {
    audio: {
      speaker_count: number;
      languages: string[];
      transcript_count: number;
      speakers: {
        feed_id: string;
        language: string;
        label: string;
        key_intelligence: string;
        segment_count: number;
      }[];
    };
    vision: {
      frames_analyzed: number;
      detections: {
        timestamp_s: number;
        type: string;
        confidence: number;
        description: string;
      }[];
    };
    cross_modal: {
      claim: string;
      modalities: string[];
      details: string;
    }[];
  };
  convergence_tracks: {
    source: string;
    type: string;
    color: string;
    events: {
      t_seconds: number;
      label: string;
      type: string;
    }[];
  }[];
  response_actions: {
    action: string;
    unit_type: string;
    unit_assigned: string | null;
    status: string;
    authorized_at: string;
    authorization_method: string;
    language: string | null;
  }[];
  agent_stats: {
    agents: {
      agent: string;
      model: string;
      invocations: number;
      avg_latency_seconds: number;
    }[];
    total_invocations: number;
    total_duration_seconds: number;
    models_used: {
      model: string;
      roles: string[];
    }[];
  };
  key_frames: {
    image_url: string;
    timestamp_s: number;
    elapsed: string;
    detections: {
      type: string;
      confidence: number;
    }[];
    description: string;
    is_hero: boolean;
  }[];
  executive_summary: string;
}

export const revalidate = 0;

async function fetchReport(caseId: string): Promise<ReportData | null> {
  try {
    const res = await fetch(`http://localhost:8000/api/v1/cases/${caseId}/report`, {
      method: 'POST',
      cache: 'no-store'
    });
    
    if (!res.ok) {
      // Fallback to GET if POST fails (maybe was already generated)
      const fallback = await fetch(`http://localhost:8000/api/v1/cases/${caseId}/report`, {
        cache: 'no-store'
      });
      if (!fallback.ok) return null;
      return fallback.json();
    }
    
    return res.json();
  } catch (error) {
    console.error("Failed to fetch report:", error);
    return null;
  }
}

export default async function AfterActionReport({ params }: { params: { id: string } }) {
  const caseId = params.id;
  const report = await fetchReport(caseId);

  if (!report) {
    notFound();
  }

  const getSeverityStyle = (severity: string) => {
    switch(severity?.toLowerCase()) {
      case 'critical': return 'text-red-500 border-red-500 bg-red-500/10 shadow-[0_0_15px_rgba(239,68,68,0.5)]';
      case 'high': return 'text-orange-500 border-orange-500 bg-orange-500/10';
      case 'medium': return 'text-amber-500 border-amber-500 bg-amber-500/10';
      case 'low': return 'text-emerald-500 border-emerald-500 bg-emerald-500/10';
      default: return 'text-slate-500 border-slate-500 bg-slate-500/10';
    }
  };

  const getLogColorStyle = (color: string) => {
    switch (color) {
      case 'red': return 'text-red-500 bg-red-500/10 border-red-500/30';
      case 'amber': return 'text-amber-500 bg-amber-500/10 border-amber-500/30';
      case 'green': return 'text-emerald-500 bg-emerald-500/10 border-emerald-500/30';
      case 'purple': return 'text-purple-500 bg-purple-500/10 border-purple-500/30';
      case 'blue': default: return 'text-blue-500 bg-blue-500/10 border-blue-500/30';
    }
  };

  return (
    <div className="min-h-screen dark:bg-[#0a0a0a] bg-zinc-50 selection:bg-blue-500/30 overflow-x-hidden print:bg-white text-zinc-900 dark:text-zinc-100">
      
      {/* ────────────────────────────────────────────────────────── */}
      {/* 1. HEADER SECTION                                          */}
      {/* ────────────────────────────────────────────────────────── */}
      <header className="sticky top-0 z-50 dark:bg-[#0a0a0a]/90 bg-zinc-50/90 backdrop-blur-xl border-b dark:border-white/10 border-black/10 px-6 py-4 flex justify-between items-center print:hidden">
        <div className="flex items-center gap-4">
          <div className="text-xl font-bold tracking-tight uppercase flex items-center gap-2">
            <span className="w-3 h-3 rounded-full bg-blue-500 shadow-[0_0_10px_rgba(59,130,246,0.8)]"></span>
            Dispatch
          </div>
          <div className="h-4 w-[1px] dark:bg-white/20 bg-black/20 mx-2"></div>
          <div className="font-mono text-xs tracking-widest dark:text-white/60 text-slate-500 uppercase">
            After-Action Report
          </div>
        </div>
        <div className="flex items-center gap-4">
          <ThemeToggle />
        </div>
      </header>

      <main className="max-w-5xl mx-auto p-6 md:p-12 md:py-16 flex flex-col gap-16 print:p-0 print:max-w-none">

        {/* Hero Info */}
        <section className="flex flex-col gap-6 animate-in fade-in slide-in-from-bottom-4 duration-700">
          <div className="flex items-center justify-between border-b-2 dark:border-white/20 border-black/20 pb-4 mb-2">
            <h1 className="font-mono text-sm tracking-widest uppercase dark:text-white/60 text-black/60">
              CASE ID <span className="dark:text-white text-black font-bold ml-4">{report.header.case_id}</span>
            </h1>
            <div className="font-mono text-xs dark:text-white/40 text-black/40">
              Generated: {new Date(report.generated_at).toISOString().replace('T', ' ').substring(0, 19)} UTC
            </div>
          </div>

          <div className="flex flex-col gap-2">
            <div className="flex items-center gap-3">
              <span className={cn("px-3 py-1 text-[11px] font-mono tracking-widest uppercase rounded-sm border", getSeverityStyle(report.header.severity))}>
                {report.header.severity}
              </span>
              <span className="dark:text-white/40 text-black/40 text-sm font-mono tracking-widest uppercase">
                {report.header.status.replace(/_/g, ' ')}
              </span>
            </div>
            
            <h2 className="text-4xl md:text-5xl font-bold tracking-tight uppercase mt-2">
              {report.header.incident_type.replace(/_/g, ' ')}
            </h2>
            
            <div className="flex items-center gap-2 text-sm font-mono tracking-wider dark:text-white/70 text-black/70 mt-2">
              <MapPin className="w-4 h-4 text-blue-500" />
              {report.header.location}
            </div>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-px bg-black/10 dark:bg-white/10 border border-black/10 dark:border-white/10 rounded-sm overflow-hidden mt-4">
            <div className="bg-white dark:bg-[#0a0a0a] p-4 flex flex-col gap-1">
              <span className="font-mono text-[10px] tracking-widest uppercase dark:text-white/40 text-black/50">Duration</span>
              <span className="text-xl font-bold font-mono">{report.header.duration_seconds}s</span>
            </div>
            <div className="bg-white dark:bg-[#0a0a0a] p-4 flex flex-col gap-1">
              <span className="font-mono text-[10px] tracking-widest uppercase dark:text-white/40 text-black/50">Audio</span>
              <span className="text-xl font-bold font-mono">{report.header.audio_segments} <span className="text-sm dark:text-white/40 text-black/40 font-sans">events</span></span>
            </div>
            <div className="bg-white dark:bg-[#0a0a0a] p-4 flex flex-col gap-1">
              <span className="font-mono text-[10px] tracking-widest uppercase dark:text-white/40 text-black/50">Languages</span>
              <span className="text-xl font-bold font-mono">{report.header.languages.length} <span className="text-sm dark:text-white/40 text-black/40 font-sans uppercase">({report.header.languages.join(',')})</span></span>
            </div>
            <div className="bg-white dark:bg-[#0a0a0a] p-4 flex flex-col gap-1">
              <span className="font-mono text-[10px] tracking-widest uppercase dark:text-white/40 text-black/50">Vision</span>
              <span className="text-xl font-bold font-mono">{report.header.vision_frames} <span className="text-sm dark:text-white/40 text-black/40 font-sans">frames</span></span>
            </div>
          </div>

          <div className="mt-8 bg-emerald-500/10 border border-emerald-500/30 p-6 rounded-sm flex items-center justify-center text-center shadow-[0_0_30px_rgba(16,185,129,0.15)]">
            <h2 className="text-2xl md:text-3xl font-bold uppercase tracking-tight text-emerald-600 dark:text-emerald-400">
              {report.header.outcome}
            </h2>
          </div>
        </section>

        {/* ────────────────────────────────────────────────────────── */}
        {/* 2. TIMELINE SECTION                                        */}
        {/* ────────────────────────────────────────────────────────── */}
        <section className="flex flex-col gap-6">
          <div className="flex items-center gap-3 border-b-2 dark:border-white/20 border-black/20 pb-4">
            <ActivitySquare className="w-6 h-6 dark:text-blue-400 text-blue-600" />
            <h2 className="text-2xl font-bold tracking-tight uppercase">Incident Timeline</h2>
          </div>
          
          <div className="relative pl-6 md:pl-8 border-l-2 dark:border-white/10 border-black/10 ml-4 py-4 space-y-8 font-mono text-sm max-w-4xl">
            {report.timeline.map((entry, i) => {
               // Determine visual accents based on severity/type
               const isCritical = entry.severity_indicator === 'critical';
               const isOperator = entry.severity_indicator === 'operator';
               
               let accentBorder = '';
               // If it's critical, override the container border
               if (isCritical) accentBorder = 'border-l-4 border-l-red-500 pl-4 -ml-[5px]';
               if (isOperator) accentBorder = 'border-l-4 border-l-emerald-500 pl-4 -ml-[5px]';

               return (
                 <div key={i} className={cn("relative flex flex-col gap-2", accentBorder)}>
                   {/* Timeline node dot */}
                   <div className={cn(
                     "absolute w-3 h-3 rounded-full border-2 dark:bg-[#0a0a0a] bg-zinc-50 -left-[32px] md:-left-[40px] top-1",
                     isCritical ? "border-red-500 bg-red-500" : 
                     isOperator ? "border-emerald-500 bg-emerald-500" : 
                     "dark:border-white/50 border-black/50"
                   )}>
                     {entry.flash && (
                       <span className="absolute inset-0 rounded-full animate-ping bg-current opacity-50"></span>
                     )}
                   </div>

                   {/* Header Row */}
                   <div className="flex items-center flex-wrap gap-x-3 gap-y-1">
                     <span className="font-bold dark:text-white/90 text-black/90 tracking-widest w-12 shrink-0">T+{entry.t}</span>
                     
                     <span className={cn(
                       "text-[10px] font-bold uppercase tracking-widest px-2 py-0.5 rounded-sm border",
                       getLogColorStyle(entry.color)
                     )}>
                       {entry.agent}
                     </span>
                     
                     {entry.model && (
                       <span className="text-[10px] dark:text-white/40 text-black/40 uppercase tracking-widest">
                         {entry.model}
                       </span>
                     )}
                   </div>

                   {/* Body Row */}
                   <div className="pl-[58px] mt-1 pr-4">
                     {isCritical && entry.event_type ? (
                       <div className="text-red-500 font-bold tracking-widest uppercase mb-2">
                         ── {entry.event_type.replace(/_/g, ' ')} ──
                       </div>
                     ) : isOperator && entry.event_type ? (
                       <div className="text-emerald-500 font-bold tracking-widest uppercase mb-2">
                         ── {entry.event_type.replace(/_/g, ' ')} ──
                       </div>
                     ) : null}
                     
                     <div className="dark:text-white/80 text-black/80 leading-relaxed whitespace-pre-wrap">
                       {entry.message}
                     </div>
                   </div>
                 </div>
               );
            })}
          </div>
        </section>

        {/* ────────────────────────────────────────────────────────── */}
        {/* 3. EVIDENCE SOURCES                                        */}
        {/* ────────────────────────────────────────────────────────── */}
        <section className="flex flex-col gap-6">
          <div className="flex items-center gap-3 border-b-2 dark:border-white/20 border-black/20 pb-4">
            <FileText className="w-6 h-6 dark:text-blue-400 text-blue-600" />
            <h2 className="text-2xl font-bold tracking-tight uppercase">Evidence Sources</h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {/* Audio Stream */}
            <div className="flex flex-col gap-4 p-5 bg-black/5 dark:bg-white/5 border border-black/10 dark:border-white/10 rounded-sm">
              <div className="flex items-center gap-2 border-b dark:border-white/10 border-black/10 pb-3">
                <Activity className="w-4 h-4 text-blue-500" />
                <h3 className="font-mono text-sm tracking-widest uppercase font-bold">Audio Stream</h3>
              </div>
              
              <div className="flex flex-col gap-3 font-mono text-sm">
                <div className="grid grid-cols-[120px_1fr] gap-2">
                  <span className="dark:text-white/40 text-black/50">Speakers:</span>
                  <span className="font-bold">{report.evidence_sources.audio.speaker_count}</span>
                </div>
                <div className="grid grid-cols-[120px_1fr] gap-2">
                  <span className="dark:text-white/40 text-black/50">Languages:</span>
                  <span className="font-bold">{report.evidence_sources.audio.languages.join(', ')}</span>
                </div>
                <div className="grid grid-cols-[120px_1fr] gap-2">
                  <span className="dark:text-white/40 text-black/50">Transcripts:</span>
                  <span className="font-bold">{report.evidence_sources.audio.transcript_count} committed</span>
                </div>
                
                <div className="mt-2 pt-3 border-t dark:border-white/10 border-black/10 flex flex-col gap-2">
                  <span className="dark:text-white/40 text-black/50 uppercase text-xs mb-1">Key Intelligence:</span>
                  {report.evidence_sources.audio.speakers.map((speaker, i) => (
                    <div key={i} className="flex gap-2 text-xs">
                      <span className="shrink-0">• {speaker.language} {speaker.label}:</span>
                      <span className="dark:text-white/80 text-black/80">{speaker.key_intelligence}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Visual Feed */}
            <div className="flex flex-col gap-4 p-5 bg-black/5 dark:bg-white/5 border border-black/10 dark:border-white/10 rounded-sm">
              <div className="flex items-center gap-2 border-b dark:border-white/10 border-black/10 pb-3">
                <Video className="w-4 h-4 text-cyan-500" />
                <h3 className="font-mono text-sm tracking-widest uppercase font-bold">Visual Feed</h3>
              </div>
              
              <div className="flex flex-col gap-3 font-mono text-sm">
                <div className="grid grid-cols-[120px_1fr] gap-2">
                  <span className="dark:text-white/40 text-black/50">Analyzed:</span>
                  <span className="font-bold">{report.evidence_sources.vision.frames_analyzed} frames</span>
                </div>
                
                <div className="mt-2 pt-3 border-t dark:border-white/10 border-black/10 flex flex-col gap-2">
                  <span className="dark:text-white/40 text-black/50 uppercase text-xs mb-1">Detections:</span>
                  {report.evidence_sources.vision.detections.map((det, i) => (
                    <div key={i} className="flex gap-2 text-xs">
                      <span className="shrink-0 font-bold dark:text-white text-black w-14">T+{det.timestamp_s.toString().padStart(2, '0')}s:</span>
                      <div className="flex flex-col">
                        <span className="dark:text-white/80 text-black/80">{det.description}</span>
                        {det.confidence >= 0.9 && (
                          <span className="text-[10px] text-cyan-500 uppercase tracking-widest mt-0.5">High Confidence ({det.confidence})</span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Cross-Modal */}
            <div className="flex flex-col gap-4 p-5 bg-black/5 dark:bg-white/5 border border-black/10 dark:border-white/10 rounded-sm">
              <div className="flex items-center gap-2 border-b dark:border-white/10 border-black/10 pb-3">
                <Navigation className="w-4 h-4 text-purple-500" />
                <h3 className="font-mono text-sm tracking-widest uppercase font-bold">Cross-Modal Logic</h3>
              </div>
              
              <div className="flex flex-col gap-4 pt-1">
                {report.evidence_sources.cross_modal.map((cm, i) => (
                  <div key={i} className="flex flex-col gap-1.5 font-mono text-xs">
                    <span className="font-bold border-b border-black/5 dark:border-white/5 pb-1">
                      {cm.claim}
                    </span>
                    <span className="dark:text-white/70 text-black/70 mt-1 leading-relaxed">
                      {cm.details}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>

        {/* ────────────────────────────────────────────────────────── */}
        {/* 4. SOURCE CONVERGENCE TIMELINE                             */}
        {/* ────────────────────────────────────────────────────────── */}
        <section className="flex flex-col gap-6">
          <div className="flex items-center gap-3 border-b-2 dark:border-white/20 border-black/20 pb-4">
            <Activity className="w-6 h-6 dark:text-blue-400 text-blue-600" />
            <h2 className="text-2xl font-bold tracking-tight uppercase">Source Convergence</h2>
          </div>
          
          <div className="bg-black/5 dark:bg-[#111] border border-black/10 dark:border-white/10 rounded-sm p-6 overflow-x-auto">
            <div className="min-w-[800px] font-mono text-xs flex flex-col gap-6 relative">
              
              {/* Header ticks */}
              <div className="flex relative pl-[60px] dark:text-white/30 text-black/40 h-4 border-b dark:border-white/10 border-black/10 mb-2">
                {[0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55].map(t => (
                  <div key={t} className="absolute flex flex-col items-center -ml-3" style={{ left: `${(t / 55) * 100}%` }}>
                    <span>T+{t.toString().padStart(2, '0')}</span>
                    <div className="w-px h-2 dark:bg-white/20 bg-black/20 mt-1"></div>
                  </div>
                ))}
              </div>

              {/* Tracks */}
              {report.convergence_tracks.map((track, i) => {
                // Determine styling based on color
                let trackLineColor = 'dark:bg-white/10 bg-black/10';
                let dotBaseColor = 'bg-white border-black dark:bg-[#111] dark:border-white';
                
                if (track.color === 'cyan') { trackLineColor = 'bg-cyan-500/30'; dotBaseColor = 'bg-cyan-500 border-cyan-500 shadow-[0_0_8px_rgba(6,182,212,0.8)]'; }
                if (track.color === 'purple') { trackLineColor = 'bg-purple-500/30'; dotBaseColor = 'bg-purple-500 border-purple-500 shadow-[0_0_8px_rgba(168,85,247,0.8)]'; }
                if (track.color === 'emerald') { trackLineColor = 'bg-emerald-500/30'; dotBaseColor = 'bg-emerald-500 border-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.8)]'; }
                if (track.color === 'amber') { trackLineColor = 'bg-amber-500/30'; dotBaseColor = 'bg-amber-500 border-amber-500 shadow-[0_0_8px_rgba(245,158,11,0.8)]'; }
                if (track.color === 'gold' || track.color === 'yellow') { trackLineColor = 'bg-amber-400/50 h-[3px]'; dotBaseColor = 'bg-amber-400 border-amber-400 shadow-[0_0_12px_rgba(251,191,36,1)] w-3 h-3 -mt-1.5'; }
                if (track.color === 'blue') { trackLineColor = 'bg-blue-500/30'; dotBaseColor = 'bg-blue-400 border-blue-400 shadow-[0_0_8px_rgba(96,165,250,0.8)]'; }

                const isFused = track.source === 'FUSED';

                return (
                  <div key={i} className="flex items-center relative h-10 group">
                    {/* Track Label */}
                    <div className="w-[60px] shrink-0 font-bold uppercase tracking-widest z-10">
                      {track.source}
                    </div>
                    
                    {/* Track Line */}
                    <div className={cn("absolute left-[60px] right-4 h-px top-1/2 -translate-y-1/2", trackLineColor)}></div>
                    
                    {/* Events */}
                    <div className="absolute left-[60px] right-4 h-full">
                      {track.events.map((evt, j) => {
                        const percentLeft = (evt.t_seconds / 55) * 100;
                        return (
                          <div key={j} className="absolute flex flex-col items-center" style={{ left: `${percentLeft}%` }}>
                            {/* Marker */}
                            <div className={cn("w-2 h-2 rounded-full absolute -ml-1 top-[16px]", dotBaseColor, isFused && "w-3 h-3 -ml-1.5 top-[14px]")}></div>
                            {/* Label */}
                            <div className={cn(
                              "absolute whitespace-nowrap pt-[26px] -translate-x-1/2 lowercase",
                              isFused ? "font-bold uppercase tracking-widest text-amber-500/90" : "dark:text-white/60 text-black/60",
                              evt.type === 'critical' ? 'font-bold dark:text-white text-black text-[10px]' : ''
                            )}>
                              {evt.label}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                );
              })}

            </div>
          </div>
        </section>

        {/* ────────────────────────────────────────────────────────── */}
        {/* 5. RESPONSE ACTIONS SUMMARY                                */}
        {/* ────────────────────────────────────────────────────────── */}
        <section className="flex flex-col gap-6">
          <div className="flex items-center gap-3 border-b-2 dark:border-white/20 border-black/20 pb-4">
            <Users className="w-6 h-6 dark:text-blue-400 text-blue-600" />
            <h2 className="text-2xl font-bold tracking-tight uppercase">Response Actions</h2>
          </div>
          
          <div className="flex flex-col lg:flex-row gap-8">
            <div className="flex-1 w-full overflow-x-auto">
              <table className="w-full text-left font-mono text-sm">
                <thead>
                  <tr className="border-b dark:border-white/20 border-black/20 dark:text-white/50 text-black/50 uppercase tracking-widest text-xs">
                    <th className="font-normal py-3 pl-2">Action</th>
                    <th className="font-normal py-3">Status</th>
                    <th className="font-normal py-3">Authorized</th>
                    <th className="font-normal py-3">Method</th>
                  </tr>
                </thead>
                <tbody className="divide-y dark:divide-white/10 divide-black/10">
                  {report.response_actions.map((act, i) => (
                    <tr key={i} className="group hover:bg-black/5 dark:hover:bg-white/5 transition-colors">
                      <td className="py-3 pl-2 max-w-[200px] pr-4">
                        <div className="font-bold">{act.action}</div>
                        {act.unit_assigned && (
                          <div className="text-[10px] dark:text-white/40 text-black/40 uppercase mt-0.5">{act.unit_assigned}</div>
                        )}
                        {act.language && (
                          <div className="text-[10px] dark:text-white/40 text-black/40 uppercase mt-0.5">{act.language} broadcast</div>
                        )}
                      </td>
                      <td className="py-3">
                        <span className={cn(
                          "px-2 py-0.5 rounded-sm text-[10px] tracking-widest uppercase border",
                          act.status === 'EXECUTED' || act.status === 'BROADCAST' 
                            ? 'bg-emerald-500/10 text-emerald-500 border-emerald-500/30' 
                            : 'bg-blue-500/10 text-blue-500 border-blue-500/30'
                        )}>
                          {act.status}
                        </span>
                      </td>
                      <td className="py-3 max-w-[120px]">
                        <div className="truncate pr-2">{act.authorized_at.split(' ')[0]} <span className="dark:text-white/50 text-black/50 ml-1">{act.authorized_at.split(' ')[1]}</span></div>
                      </td>
                      <td className="py-3">
                        <span className={cn(
                          "uppercase tracking-widest text-xs",
                          act.authorization_method === 'Autonomous' 
                            ? 'text-amber-500 font-bold' 
                            : 'dark:text-white/60 text-black/60'
                        )}>
                          {act.authorization_method}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="lg:w-80 shrink-0 flex flex-col gap-4">
              <div className="p-5 border border-black/10 dark:border-white/10 rounded-sm bg-black/5 dark:bg-white/5 h-full">
                <h3 className="font-mono text-xs uppercase tracking-widest border-b dark:border-white/10 border-black/10 pb-3 mb-4 font-bold flex items-center justify-between">
                  Authorization Model
                  <ShieldAlert className="w-4 h-4 dark:text-white/40 text-black/40" />
                </h3>
                
                <div className="flex flex-col gap-3 font-mono text-sm">
                  <div className="flex justify-between items-center group">
                    <span className="dark:text-white/50 text-black/50 group-hover:dark:text-white group-hover:text-black transition-colors">Operator-authorized</span>
                    <span className="font-bold">{report.response_actions.filter(a => a.authorization_method === 'Operator').length}</span>
                  </div>
                  <div className="flex justify-between items-center group">
                    <span className="text-amber-500 font-bold">Autonomous</span>
                    <span className="font-bold text-amber-500">{report.response_actions.filter(a => a.authorization_method === 'Autonomous').length}</span>
                  </div>
                </div>

                <div className="mt-6 pt-4 border-t dark:border-white/10 border-black/10">
                  <p className="font-mono text-[10px] leading-relaxed dark:text-white/40 text-black/50 uppercase">
                    Autonomous actions triggered under condition:
                    <br/><br/>
                    <span className="text-amber-500/70">hazard_type = FIRE AND</span><br/>
                    <span className="text-amber-500/70">persons_at_risk = TRUE AND</span><br/>
                    <span className="text-amber-500/70">evacuation_delay_risk {'>'} threshold</span>
                  </p>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* ────────────────────────────────────────────────────────── */}
        {/* 6. AGENT & MODEL UTILIZATION                               */}
        {/* ────────────────────────────────────────────────────────── */}
        <section className="flex flex-col gap-6">
          <div className="flex items-center gap-3 border-b-2 dark:border-white/20 border-black/20 pb-4">
            <TerminalSquare className="w-6 h-6 dark:text-blue-400 text-blue-600" />
            <h2 className="text-2xl font-bold tracking-tight uppercase">Agent Utilization</h2>
          </div>
          
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            <div className="lg:col-span-2 overflow-x-auto">
              <table className="w-full text-left font-mono text-sm">
                <thead>
                  <tr className="border-b dark:border-white/20 border-black/20 dark:text-white/50 text-black/50 uppercase tracking-widest text-xs">
                    <th className="font-normal py-3 pl-2">Agent</th>
                    <th className="font-normal py-3">Model</th>
                    <th className="font-normal py-3 text-right">Invocations</th>
                    <th className="font-normal py-3 text-right pr-2">Avg Latency</th>
                  </tr>
                </thead>
                <tbody className="divide-y dark:divide-white/10 divide-black/10">
                  {report.agent_stats.agents.map((ag, i) => (
                    <tr key={i} className="hover:bg-black/5 dark:hover:bg-white/5 transition-colors">
                      <td className="py-3 pl-2 font-bold">{ag.agent}</td>
                      <td className="py-3 dark:text-white/60 text-black/60">{ag.model}</td>
                      <td className="py-3 text-right">{ag.invocations}</td>
                      <td className="py-3 text-right pr-2">{ag.avg_latency_seconds}s</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <div className="font-mono text-xs uppercase tracking-widest text-right mt-4 pt-4 border-t dark:border-white/10 border-black/10 font-bold text-blue-500">
                TOTAL {report.agent_stats.total_invocations} INVOCATIONS IN {report.agent_stats.total_duration_seconds} SECONDS
              </div>
            </div>

            <div className="flex flex-col gap-4">
              <div className="p-5 border border-black/10 dark:border-white/10 rounded-sm bg-black/5 dark:bg-white/5 h-full">
                <h3 className="font-mono text-xs uppercase tracking-widest border-b dark:border-white/10 border-black/10 pb-3 mb-4 font-bold flex items-center gap-2">
                  <ActivitySquare className="w-4 h-4" />
                  Models Deployed
                </h3>
                
                <div className="flex flex-col gap-4">
                  {report.agent_stats.models_used.map((mu, i) => (
                    <div key={i} className="flex flex-col gap-1 font-mono text-sm">
                      <span className="font-bold">{mu.model}</span>
                      <span className="text-xs dark:text-white/50 text-black/50 leading-tight">
                        {mu.roles.join(', ')}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* ────────────────────────────────────────────────────────── */}
        {/* 7. KEY FRAMES                                              */}
        {/* ────────────────────────────────────────────────────────── */}
        <section className="flex flex-col gap-6">
          <div className="flex items-center gap-3 border-b-2 dark:border-white/20 border-black/20 pb-4">
            <Video className="w-6 h-6 dark:text-blue-400 text-blue-600" />
            <h2 className="text-2xl font-bold tracking-tight uppercase">Key Evidence Frames</h2>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {report.key_frames.map((frame, i) => (
              <div key={i} className={cn(
                "flex flex-col border dark:border-white/10 border-black/10 rounded-sm overflow-hidden",
                frame.is_hero ? "ring-2 ring-red-500/50 dark:bg-white/5 bg-black/5 shadow-[0_0_30px_rgba(239,68,68,0.1)]" : "bg-black/5 dark:bg-white/5"
              )}>
                {/* Simulated frame / actual image */}
                <div className="aspect-video bg-black/50 relative overflow-hidden group">
                  {frame.image_url ? (
                    <Image src={frame.image_url} alt={frame.description} fill className="object-cover" />
                  ) : (
                    <div className="absolute inset-0 flex items-center justify-center font-mono text-xs text-white/20 uppercase tracking-widest">
                      [ Image Data Unavailable ]
                    </div>
                  )}
                  
                  <div className="absolute top-2 left-2 bg-black/80 px-2 py-1 font-mono text-[10px] text-white tracking-widest rounded-sm border border-white/20">
                    T+{frame.timestamp_s.toString().padStart(2, '0')}s
                  </div>
                  
                  {frame.is_hero && (
                    <div className="absolute inset-0 border-[3px] border-red-500/80 pointer-events-none"></div>
                  )}
                  
                  {/* Fake bounding box for hero if no real image detection boxing is available */}
                  {frame.is_hero && !frame.image_url && (
                    <div className="absolute top-[30%] left-[40%] w-[30%] h-[40%] border-2 border-red-500 border-dashed bg-red-500/10 flex flex-col items-center justify-center animate-pulse">
                      <div className="bg-red-500 text-white font-mono text-[8px] px-1 py-0.5 whitespace-nowrap -mt-6">0.99 FIRE</div>
                    </div>
                  )}
                </div>
                
                <div className="p-4 flex flex-col gap-2 font-mono text-sm">
                  <div className={cn(
                    "font-bold uppercase tracking-widest pb-1 border-b dark:border-white/10 border-black/10",
                    frame.is_hero ? "text-red-500" : ""
                  )}>
                    {frame.description}
                  </div>
                  
                  <div className="flex justify-between items-center text-xs dark:text-white/60 text-black/60 mt-1">
                    <span>{frame.elapsed}</span>
                    <span>Confidence: {Math.max(...frame.detections.map(d => d.confidence))}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* ────────────────────────────────────────────────────────── */}
        {/* 8. EXECUTIVE SUMMARY                                       */}
        {/* ────────────────────────────────────────────────────────── */}
        <section className="flex flex-col gap-6 mt-8">
          <div className="flex items-center gap-3 border-b-2 dark:border-white/20 border-black/20 pb-4">
            <CheckCircle2 className="w-6 h-6 dark:text-blue-400 text-blue-600" />
            <h2 className="text-2xl font-bold tracking-tight uppercase">Executive Summary</h2>
          </div>
          
          <div className="p-6 md:p-8 bg-blue-500/5 border border-blue-500/20 rounded-sm">
            <p className="text-lg md:text-xl leading-relaxed font-serif dark:text-white/90 text-black/90">
              {report.executive_summary}
            </p>
          </div>
        </section>

      </main>

      {/* ────────────────────────────────────────────────────────── */}
      {/* 9. FOOTER                                                  */}
      {/* ────────────────────────────────────────────────────────── */}
      <footer className="border-t dark:border-white/10 border-black/10 py-12 mt-12 mb-12">
        <div className="max-w-5xl mx-auto px-6 md:px-12 flex flex-col md:flex-row justify-between items-center gap-6 font-mono text-xs dark:text-white/40 text-black/40">
          <div className="flex flex-col gap-1 items-center md:items-start text-center md:text-left">
            <strong className="dark:text-white/60 text-black/60 uppercase tracking-widest">DISPATCH v2.0.4 · Incident Intelligence System</strong>
            <span>Powered by Mistral Large · Pixtral 12B · ElevenLabs Scribe & TTS</span>
            <span>Report generated {new Date(report.generated_at).toISOString().replace('T', ' ').substring(0, 19)} UTC</span>
          </div>
          
          <div className="flex gap-4 object-right z-10 print:hidden relative">
            <a href="/" className="px-4 py-2 border dark:border-white/20 border-black/20 hover:bg-black/5 dark:hover:bg-white/5 transition-colors uppercase tracking-widest rounded-sm cursor-pointer block">
              ← Dashboard
            </a>
            <button 
              onClick={() => window.print()}
              className="px-4 py-2 bg-blue-500 text-white hover:bg-blue-600 transition-colors uppercase tracking-widest rounded-sm cursor-pointer"
            >
              Print Report
            </button>
          </div>
        </div>
      </footer>
    </div>
  );
}

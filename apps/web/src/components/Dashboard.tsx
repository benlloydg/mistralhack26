"use client";

import { useState, useEffect } from "react";
import { Play, Loader2, RotateCcw } from "lucide-react";
import { CaseFilePanel } from "./CaseFilePanel";
import { AgentTerminal } from "./AgentTerminal";
import { CCTVPanel } from "./CCTVPanel";
import { TranscriptPanel } from "./TranscriptPanel";
import { ResponseLanes } from "./ResponseLanes";
import { useIncidentState } from "@/hooks/useIncidentState";
import { useAgentLogs } from "@/hooks/useAgentLogs";
import { useTranscripts } from "@/hooks/useTranscripts";
import { useDispatches } from "@/hooks/useDispatches";
import { useLivePartials } from "@/hooks/useLivePartials";
import { ThemeToggle } from "./ThemeToggle";

export function Dashboard() {
  const [isStarting, setIsStarting] = useState(false);
  const [isApproving, setIsApproving] = useState(false);
  const [elapsedTime, setElapsedTime] = useState(0);
  const [showLanding, setShowLanding] = useState(true);
  const [isBroadcasting, setIsBroadcasting] = useState(false);
  const [audioSpectrum, setAudioSpectrum] = useState<number[]>(new Array(10).fill(0));
  const [activeCaseId, setActiveCaseId] = useState<string | null>(null);
  const [videoUrl, setVideoUrl] = useState<string | null>(null);

  // Sync state from Supabase Realtime — subscribes once we have a case_id
  const incidentState = useIncidentState(activeCaseId ?? "");
  const agentLogs = useAgentLogs(activeCaseId ?? "");
  const transcripts = useTranscripts(activeCaseId ?? "");
  const dispatches = useDispatches(activeCaseId ?? "");
  const livePartial = useLivePartials(activeCaseId ?? "");

  useEffect(() => {
    let timer: NodeJS.Timeout;
    if (!incidentState || incidentState.status === 'intake') {
      setElapsedTime(0);
    } else if (incidentState.status !== 'resolved_demo') {
      timer = setInterval(() => setElapsedTime(p => p + 1), 1000);
      setShowLanding(false); // Auto-hide landing if we detect an active session ongoing
    }
    return () => clearInterval(timer);
  }, [incidentState?.status]);

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `T+${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const handleStartDemo = async (scenario: string = 'vehicle_collision') => {
    setIsStarting(true);
    try {
      const response = await fetch(`http://localhost:8000/api/v1/demo/start?scenario=${scenario}`, {
        method: "POST",
      });
      if (!response.ok) throw new Error("Failed to start DEMO");
      const data = await response.json();
      setActiveCaseId(data.case_id);
      setVideoUrl(data.video_url);
      setShowLanding(false);
    } catch (err) {
      console.error(err);
      alert("Backend not running or failed to start demo. Start the server!");
    } finally {
      setIsStarting(false);
    }
  };

  const handleReset = async () => {
    if (confirm("Reset demo and return to scenarios?")) {
      try {
        await fetch("http://localhost:8000/api/v1/demo/reset", { method: "POST" });
      } catch (err) {
        console.error(err);
      }
      setActiveCaseId(null);
      setVideoUrl(null);
      setShowLanding(true);
      window.location.reload(); // Hard reload to clear client state
    }
  };

  const handleApprove = async () => {
    setIsApproving(true);
    try {
      const response = await fetch("http://localhost:8000/api/v1/demo/approve", {
        method: "POST",
      });
      if (!response.ok) throw new Error("Failed to approve DEMO steps");
    } catch (err) {
      console.error(err);
    } finally {
      setIsApproving(false);
    }
  };

  const handleGenerateReport = async () => {
    // End the simulation by approving dispatch, then report opens in new tab
    try {
      await fetch("http://localhost:8000/api/v1/demo/approve", { method: "POST" });
    } catch (err) {
      console.error(err);
    }
  };

  if (showLanding) {
    return (
      <div className="h-screen w-full flex flex-col items-center justify-center p-4 relative z-10 mx-auto dark:bg-zinc-950 bg-zinc-50 overflow-hidden">
        <div className="absolute top-6 right-6">
          <ThemeToggle />
        </div>
        
        <div className="flex flex-col items-center max-w-lg w-full text-center animate-in fade-in zoom-in-95 duration-700">
          <div className="w-4 h-4 rounded-full bg-blue-500 shadow-[0_0_20px_rgba(59,130,246,0.8)] mb-6 animate-pulse"></div>
          <h1 className="text-4xl font-bold tracking-tight uppercase dark:text-white text-black mb-2">Dispatch</h1>
          <p className="font-mono text-xs dark:text-white/40 text-black/50 tracking-widest mb-16">INCIDENT INTELLIGENCE SYSTEM</p>
          
          <div className="w-full flex flex-col gap-4 text-left">
            <h3 className="font-mono text-[10px] uppercase tracking-widest dark:text-white/30 text-black/40 mb-2 px-1">Select Scenario Array</h3>
            
            <button 
             onClick={() => handleStartDemo('vehicle_collision')}
             disabled={isStarting}
             className="w-full p-6 border dark:border-white/10 border-black/10 rounded-sm dark:bg-white/5 bg-black/5 dark:hover:bg-white/10 hover:bg-black/10 transition-all flex flex-col gap-3 group relative overflow-hidden"
            >
              <div className="absolute inset-0 bg-blue-500/0 group-hover:bg-blue-500/5 transition-colors"></div>
              <div className="flex justify-between items-center w-full relative z-10">
                <span className="font-mono text-xs font-bold tracking-widest uppercase dark:text-white text-black group-hover:text-blue-500 transition-colors">Scenario 01</span>
                {isStarting ? <Loader2 className="w-4 h-4 animate-spin text-blue-500" /> : <Play className="w-4 h-4 dark:text-white/30 text-black/30 group-hover:text-blue-500 transition-colors" />}
              </div>
              <div className="flex flex-col gap-1 relative z-10">
                <span className="text-xl font-semibold dark:text-white/90 text-black/90">Multi-Vehicle Collision</span>
                <span className="text-xs font-mono dark:text-white/50 text-black/50">3 Callers • ES/ZH/FR • Vision Integration</span>
              </div>
            </button>
            
            <button 
             disabled
             className="w-full p-6 border dark:border-white/5 border-black/5 rounded-sm dark:bg-black/20 bg-black/5 transition-all flex flex-col gap-3 opacity-50 cursor-not-allowed"
            >
              <div className="flex justify-between items-center w-full">
                <span className="font-mono text-xs font-bold tracking-widest uppercase dark:text-white/40 text-black/40">Scenario 02</span>
                <span className="text-[10px] uppercase font-mono tracking-widest bg-black/10 px-2 py-0.5 rounded">Locked</span>
              </div>
              <div className="flex flex-col gap-1">
                <span className="text-xl font-semibold dark:text-white/50 text-black/50">Industrial Fire</span>
                <span className="text-xs font-mono dark:text-white/30 text-black/30">2 Callers • EN/ES • Sensor Array</span>
              </div>
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen w-full flex flex-col p-4 md:p-6 gap-6 relative z-10 mx-auto max-w-[1920px] animate-in fade-in duration-700">
      {/* Header */}
      <header className="flex justify-between items-center h-12 shrink-0">
        <div className="flex items-center gap-4">
          <a href="/" className="text-xl font-bold tracking-tight uppercase flex items-center gap-2 hover:opacity-80 transition-opacity">
            <span className="w-3 h-3 rounded-full bg-blue-500 shadow-[0_0_10px_rgba(59,130,246,0.8)]"></span>
            Dispatch
          </a>
          <div className="h-4 w-[1px] dark:bg-white/20 bg-black/20 mx-2"></div>
          <div className="font-mono text-sm dark:text-white/40 text-slate-500 tracking-widest hidden md:block">
            INCIDENT INTELLIGENCE SYSTEM // v2.0.4
          </div>
        </div>
        <div className="flex gap-4 items-center">
          
          {elapsedTime > 0 && (
            <div className="font-mono text-xs text-blue-600 dark:text-blue-400 font-bold tracking-widest hidden sm:block animate-in fade-in duration-1000">
              {formatTime(elapsedTime)}
            </div>
          )}
          
          <button 
            onClick={handleReset}
            title="Reset Demo State"
            className="p-2 border dark:border-white/10 border-black/10 rounded-sm dark:bg-white/5 bg-black/5 hover:bg-black/10 dark:hover:bg-white/10 transition-colors"
          >
            <RotateCcw className="w-4 h-4 dark:text-white/70 text-black/70" />
          </button>

          <ThemeToggle />
          <div className="dark:bg-black/50 bg-black/5 border dark:border-white/10 border-black/10 rounded-full px-4 py-1.5 flex items-center gap-3">
            <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-[pulse_3s_ease-in-out_infinite]"></div>
            <span className="text-xs font-mono tracking-widest uppercase dark:text-white/70 text-black/70">Sys Active</span>
          </div>
        </div>
      </header>

      {/* Main Grid Layout */}
      <div className="flex-1 grid grid-cols-1 lg:grid-cols-12 gap-4 md:gap-6 min-h-0">
        
        {/* Left Column: SOURCES (40% - 5 cols) */}
        <div className="lg:col-span-5 flex flex-col gap-4 min-h-0">
          <div className="flex items-center gap-2 px-1 pb-1 mb-[-8px] border-b dark:border-white/10 border-black/10 shrink-0">
            <span className="text-[10px] font-mono font-bold tracking-widest uppercase dark:text-white/40 text-black/40">SCENE MONITORING // CAM-04 + MIC-04</span>
          </div>
          <div className="flex-[3] min-h-0">
            <CCTVPanel state={incidentState} isBroadcasting={isBroadcasting} onAudioSpectrum={setAudioSpectrum} videoUrl={videoUrl} />
          </div>
          <div className="flex-[2] min-h-0">
            <TranscriptPanel transcripts={transcripts} spectrum={audioSpectrum} livePartial={livePartial} />
          </div>
        </div>

        {/* Middle Column: INTELLIGENCE (33% - 4 cols) */}
        <div className="lg:col-span-4 flex flex-col gap-4 min-h-0">
          <div className="shrink-0 min-h-0">
            <CaseFilePanel state={incidentState} />
          </div>
          <div className="flex-1 min-h-0">
            <AgentTerminal logs={agentLogs} />
          </div>
        </div>

        {/* Right Column: ACTIONS (25% - 3 cols) */}
        <div className="lg:col-span-3 flex flex-col gap-4 min-h-0">
          <div className="flex-1 min-h-0">
            {/* Pass transcripts down to ResponseLanes to render outbound broadcasts */}
            <ResponseLanes
               dispatches={dispatches}
               transcripts={transcripts}
               recommendedUnits={incidentState?.recommended_units || []}
               onFirstExecute={handleApprove}
               onBroadcastStateChange={setIsBroadcasting}
               onGenerateReport={handleGenerateReport}
               isResolved={incidentState?.status === 'resolved_demo'}
               caseId={activeCaseId}
            />
          </div>
        </div>

      </div>
    </div>
  );
}

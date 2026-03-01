import { IncidentState } from "@/lib/types";
import { Volume2 } from "lucide-react";
import { useState, useEffect, useRef } from "react";

// Derive detections from real vision API results in incident_state
function deriveScene(state: IncidentState | null) {
  if (!state || !state.vision_detections || state.vision_detections.length === 0) {
    return { desc: "Scanning...", detections: [] };
  }

  // Deduplicate by type, keeping highest confidence per type
  const byType = new Map<string, number>();
  for (const det of state.vision_detections) {
    const t = det.type || det.label || "unknown";
    const c = det.confidence || det.conf || 0;
    byType.set(t, Math.max(byType.get(t) || 0, c));
  }

  const detections = Array.from(byType.entries())
    .map(([label, conf]) => ({ label: label.replace(/_/g, " "), conf }))
    .sort((a, b) => b.conf - a.conf)
    .slice(0, 5);

  // Build description from hazard flags + incident type
  const parts: string[] = [];
  if (state.incident_type) parts.push(state.incident_type);
  if (state.hazard_flags.length > 0) parts.push(state.hazard_flags.join(", "));
  const desc = parts.length > 0 ? parts.join(" — ") : "Scene under analysis";

  return { desc: desc.toUpperCase(), detections };
}

export function CCTVPanel({
  state,
  isBroadcasting = false,
  onAudioSpectrum,
  videoUrl
}: {
  state: IncidentState | null;
  isBroadcasting?: boolean;
  onAudioSpectrum?: (data: number[]) => void;
  videoUrl?: string | null;
}) {
  // Demo states to show some visual activity 
  const isActive = state && ['active', 'escalated', 'critical'].includes(state.status);
  const [videoTime, setVideoTime] = useState(0);
  const videoRef = useRef<HTMLVideoElement>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const animationFrameRef = useRef<number | null>(null);

  // State to track if user has interacted to allow AudioContext
  const [audioInitialized, setAudioInitialized] = useState(false);

  // Initialize Audio Analyser when video starts playing
  useEffect(() => {
    const video = videoRef.current;
    if (!video || !onAudioSpectrum || !audioInitialized) return;

    const handlePlay = () => {
       if (!audioContextRef.current) {
         try {
           const AudioContext = window.AudioContext || (window as any).webkitAudioContext;
           const ctx = new AudioContext();
           const analyser = ctx.createAnalyser();
           
           analyser.fftSize = 64; 
           analyser.smoothingTimeConstant = 0.8; 

           const source = ctx.createMediaElementSource(video);
           source.connect(analyser);
           analyser.connect(ctx.destination); 

           audioContextRef.current = ctx;
           analyserRef.current = analyser;
         } catch (e) {
           console.error("AudioContext initialization failed:", e);
         }
       }

       const updateSpectrum = () => {
         if (analyserRef.current && onAudioSpectrum) {
           const bufferLength = analyserRef.current.frequencyBinCount;
           const dataArray = new Uint8Array(bufferLength);
           analyserRef.current.getByteFrequencyData(dataArray);

           const numBars = 10;
           const step = Math.floor(dataArray.length / numBars);
           const barData: number[] = [];
           
           for (let i = 0; i < numBars; i++) {
             const p = dataArray[i * step] / 255.0;
             barData.push(p);
           }
           
           onAudioSpectrum(barData);
         }
         animationFrameRef.current = requestAnimationFrame(updateSpectrum);
       };

       updateSpectrum();
    };

    video.addEventListener('play', handlePlay);
    
    // If it's already playing when the effect runs, trigger manually
    if (!video.paused) {
      handlePlay();
    }

    return () => {
      video.removeEventListener('play', handlePlay);
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, [audioInitialized, onAudioSpectrum]);

  const currentScene = deriveScene(state);

  return (
    <div className="flex flex-col h-full tech-glass relative overflow-hidden group">
      <div className="absolute top-0 left-0 right-0 z-10 border-b dark:border-white/10 border-black/10 p-3 px-4 flex justify-between items-center dark:bg-black/60 bg-zinc-100/90 backdrop-blur-md">
        <h2 className="text-xs font-mono uppercase tracking-widest dark:text-white/50 text-slate-500 font-semibold flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-red-500 animate-pulse"></div>
          Live Feed // CAM-04
        </h2>
        <div className="text-[10px] font-mono dark:text-white/30 text-slate-400 flex items-center gap-1.5">
          <span className="w-1.5 h-1.5 rounded-full bg-red-500 animate-[pulse_2s_ease-in-out_infinite]"></span>
          REC
        </div>
      </div>

      <div className="flex-1 relative dark:bg-[#0a0a0a] bg-zinc-200 flex items-center justify-center overflow-hidden rounded-b-sm">
        {/* Looping CCTV Video Feed */}
        <video 
          ref={videoRef}
          src={videoUrl || "/video/crash_01.mp4"}
          loop 
          crossOrigin="anonymous"
          playsInline 
          onTimeUpdate={(e) => setVideoTime(e.currentTarget.currentTime)}
          onClick={(e) => {
            if (e.currentTarget.paused) {
              e.currentTarget.play();
            } else {
              e.currentTarget.pause();
            }
          }}
          className={`absolute inset-0 w-full h-full object-cover transition-opacity duration-1000 cursor-pointer ${audioInitialized ? 'opacity-60 dark:opacity-40' : 'opacity-0'}`}
        />
        
        {/* Audio Initialization Overlay (Browser Policy Requirement) */}
        {!audioInitialized && (
          <div className="absolute inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm">
            <button
              onClick={() => {
                setAudioInitialized(true);
                // Manually trigger play since we removed autoPlay to satisfy browser policies
                if (videoRef.current) {
                  videoRef.current.play().catch(e => console.error("Playback failed:", e));
                }
                // Signal backend to start audio streaming + vision
                fetch("http://localhost:8000/api/v1/demo/feed", { method: "POST" })
                  .catch(e => console.error("Feed signal failed:", e));
              }}
              className="flex items-center gap-3 px-6 py-3 border border-blue-500/50 bg-blue-500/10 hover:bg-blue-500/20 text-blue-400 font-mono text-xs uppercase tracking-widest rounded-sm transition-all animate-pulse hover:animate-none"
            >
              <Volume2 className="w-4 h-4" /> INITIATE FEED
            </button>
          </div>
        )}
        
        {/* Subtle CRT Scanline Overlay */}
        <div className="absolute inset-0 opacity-20 dark:opacity-30 pointer-events-none mix-blend-multiply dark:mix-blend-overlay" 
             style={{ 
               backgroundImage: `repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(0,0,0,0.2) 2px, rgba(0,0,0,0.2) 4px)` 
             }} />
        
        {!isActive ? (
          <div className="dark:text-white/20 text-black/20 font-mono text-xs uppercase tracking-widest text-center">
            Signal Lost<br/>or Standby
          </div>
        ) : (
          <>
            {/* Description Box */}
            <div className="absolute bottom-4 left-0 right-0 w-full flex justify-center pointer-events-none z-20">
               <div className="backdrop-blur-md px-3 py-1 rounded-sm border border-white/20 bg-black/60 text-center transition-all duration-500 max-w-lg">
                  <span className="font-mono text-[10px] leading-tight uppercase tracking-widest text-white/90">
                    {currentScene.desc}
                  </span>
               </div>
            </div>

            {/* Detections Stack (Bottom Left) */}
            <div className="absolute bottom-16 left-4 flex flex-col items-start gap-1 pointer-events-none z-20">
               {currentScene.detections.map((det) => {
                 const isHazard = det.label === 'fire' || det.label === 'smoke';
                 const bgClass = isHazard ? 'bg-red-500/20' : 'bg-black/60';
                 const borderClass = isHazard ? 'border-red-500/50 shadow-[0_0_15px_rgba(239,68,68,0.4)]' : 'border-white/20';
                 const textClass = isHazard ? 'text-red-500' : 'text-white/80';
                 
                 return (
                   <div key={det.label} className={`backdrop-blur-md px-2 py-0.5 rounded-sm border ${borderClass} ${bgClass} transition-all duration-300 flex items-center gap-2`}>
                     <span className={`w-1 h-1 rounded-full ${isHazard ? 'bg-red-500 animate-[pulse_1s_ease-in-out_infinite]' : 'bg-white/50'}`}></span>
                     <span className={`font-mono text-[10px] tracking-widest uppercase ${textClass}`}>
                       {det.label} · {Math.round(det.conf * 100)}%
                     </span>
                   </div>
                 );
               })}
            </div>
          </>
        )}

        {/* HUD Elements */}
        {isActive && (
          <>
            <div className="absolute top-11 left-0 right-0 w-full z-30">
              {isBroadcasting && (
                <div className="w-full bg-amber-500 text-black px-4 py-1.5 flex justify-center items-center gap-2 animate-[pulse_1s_ease-in-out_infinite] shadow-[0_4px_20px_rgba(245,158,11,0.5)] border-b border-amber-400">
                  <Volume2 className="w-4 h-4" />
                  <span className="font-mono text-[11px] font-extrabold tracking-[0.2em] uppercase">Evacuation Warning Broadcast In Progress</span>
                  <Volume2 className="w-4 h-4 ml-1" />
                </div>
              )}
            </div>

            <div className="absolute bottom-4 left-4 font-mono text-[9px] dark:text-white/30 text-black/40">
              ZOOM: 2.4X<br/>
              LAT: 37.7749<br/>
              LNG: -122.4194
            </div>
            <div className="absolute bottom-4 right-4 flex flex-col gap-1 items-end font-mono text-[10px] animate-[pulse_8s_ease-in-out_infinite]">
              <div className="text-emerald-500 dark:text-emerald-400">SYS: ONLINE</div>
              <div className="text-blue-500 dark:text-blue-400">AI: ACTIVE</div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

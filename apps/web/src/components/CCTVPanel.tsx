import { IncidentState } from "@/lib/types";
import { Volume2 } from "lucide-react";
import { useState, useEffect, useRef } from "react";

const TIMED_SCENES = [
  { time: 13, desc: "Severe collision, active engine fire", detections: [{label: 'collision', conf: 0.99}, {label: 'fire', conf: 0.95}, {label: 'smoke', conf: 0.90}] },
  { time: 10, desc: "Truck and car engulfed in flames", detections: [{label: 'collision', conf: 0.99}, {label: 'fire', conf: 0.95}, {label: 'smoke', conf: 0.90}] },
  { time: 7, desc: "Severe collision with engine fire and debris", detections: [{label: 'collision', conf: 0.99}, {label: 'fire', conf: 0.99}, {label: 'smoke', conf: 0.95}] },
  { time: 5, desc: "Vehicle collision with smoke and possible fire", detections: [{label: 'collision', conf: 0.95}, {label: 'smoke', conf: 0.90}, {label: 'fire', conf: 0.80}] },
  { time: 3, desc: "Possible collision involving truck and car", detections: [{label: 'collision', conf: 0.80}, {label: 'persons', conf: 0.90}] },
  { time: 0, desc: "Nighttime intersection with light traffic", detections: [{label: 'persons', conf: 0.90}] }
];

export function CCTVPanel({ 
  state, 
  isBroadcasting = false,
  onAudioSpectrum
}: { 
  state: IncidentState | null;
  isBroadcasting?: boolean;
  onAudioSpectrum?: (data: number[]) => void;
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

  // Initialize Audio Analyser
  useEffect(() => {
    const video = videoRef.current;
    if (!video || !onAudioSpectrum || !audioInitialized) return;
       if (!audioContextRef.current) {
         try {
           const AudioContext = window.AudioContext || (window as any).webkitAudioContext;
           const ctx = new AudioContext();
           const analyser = ctx.createAnalyser();
           
           // Fast Fourier Transform size (higher = more resolution, we only need 10 bars so 64 is plenty)
           analyser.fftSize = 64; 
           analyser.smoothingTimeConstant = 0.8; // Smooth out the jumps

           const source = ctx.createMediaElementSource(video);
           source.connect(analyser);
           analyser.connect(ctx.destination); // Ensure audio plays through speakers

           audioContextRef.current = ctx;
           analyserRef.current = analyser;
         } catch (e) {
           console.error("AudioContext initialization failed:", e);
         }
       }

       // Start Analysis Loop
       const updateSpectrum = () => {
         if (analyserRef.current && onAudioSpectrum) {
           const bufferLength = analyserRef.current.frequencyBinCount;
           const dataArray = new Uint8Array(bufferLength);
           analyserRef.current.getByteFrequencyData(dataArray);

           // dataArray length is 32 (fftSize/2). We only want 10 bars for the UI.
           // We'll sample 10 points evenly.
           const numBars = 10;
           const step = Math.floor(dataArray.length / numBars);
           const barData: number[] = [];
           
           for (let i = 0; i < numBars; i++) {
             // Map 0-255 strictly to a 0.0 - 1.0 percentage scale
             const p = dataArray[i * step] / 255.0;
             barData.push(p);
           }
           
           onAudioSpectrum(barData);
         }
         animationFrameRef.current = requestAnimationFrame(updateSpectrum);
       };

       updateSpectrum();

    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, [audioInitialized, onAudioSpectrum]);

  const currentScene = TIMED_SCENES.find(s => videoTime >= s.time) || TIMED_SCENES[TIMED_SCENES.length - 1];

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
          src="/video/crash_01.mp4" 
          autoPlay={audioInitialized}
          loop 
          crossOrigin="anonymous"
          playsInline 
          onTimeUpdate={(e) => setVideoTime(e.currentTarget.currentTime)}
          className={`absolute inset-0 w-full h-full object-cover transition-opacity duration-1000 pointer-events-none ${audioInitialized ? 'opacity-60 dark:opacity-40' : 'opacity-0'}`}
        />
        
        {/* Audio Initialization Overlay (Browser Policy Requirement) */}
        {!audioInitialized && (
          <div className="absolute inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm">
            <button 
              onClick={() => setAudioInitialized(true)}
              className="flex items-center gap-3 px-6 py-3 border border-blue-500/50 bg-blue-500/10 hover:bg-blue-500/20 text-blue-400 font-mono text-xs uppercase tracking-widest rounded-sm transition-all animate-pulse hover:animate-none"
            >
              <Volume2 className="w-4 h-4" /> Initialize Audio Sync
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

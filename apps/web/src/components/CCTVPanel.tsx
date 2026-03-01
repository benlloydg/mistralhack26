import { IncidentState } from "@/lib/types";
import { Volume2 } from "lucide-react";
import { useState } from "react";

const TIMED_SCENES = [
  { time: 13, desc: "Severe collision, active engine fire", detections: [{label: 'collision', conf: 0.99}, {label: 'fire', conf: 0.95}, {label: 'smoke', conf: 0.90}] },
  { time: 10, desc: "Truck and car engulfed in flames", detections: [{label: 'collision', conf: 0.99}, {label: 'fire', conf: 0.95}, {label: 'smoke', conf: 0.90}] },
  { time: 7, desc: "Severe collision with engine fire and debris", detections: [{label: 'collision', conf: 0.99}, {label: 'fire', conf: 0.99}, {label: 'smoke', conf: 0.95}] },
  { time: 5, desc: "Vehicle collision with smoke and possible fire", detections: [{label: 'collision', conf: 0.95}, {label: 'smoke', conf: 0.90}, {label: 'fire', conf: 0.80}] },
  { time: 3, desc: "Possible collision involving truck and car", detections: [{label: 'collision', conf: 0.80}, {label: 'persons', conf: 0.90}] },
  { time: 0, desc: "Nighttime intersection with light traffic", detections: [{label: 'persons', conf: 0.90}] }
];

export function CCTVPanel({ state, isBroadcasting = false }: { state: IncidentState | null, isBroadcasting?: boolean }) {
  // Demo states to show some visual activity 
  const isActive = state && ['active', 'escalated', 'critical'].includes(state.status);
  const [videoTime, setVideoTime] = useState(0);

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
          src="/video/crash_01.mp4" 
          autoPlay 
          loop 
          muted 
          playsInline 
          onTimeUpdate={(e) => setVideoTime(e.currentTarget.currentTime)}
          className="absolute inset-0 w-full h-full object-cover opacity-60 dark:opacity-40 pointer-events-none" 
        />
        
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
          <div className="absolute bottom-4 left-0 right-0 w-full flex flex-col items-center justify-end pointer-events-none z-20">
             {/* General Image Description Overlay */}
             <div className="w-full px-24 flex flex-col items-center gap-1.5">
               
               {/* Detections Row */}
               <div className="flex gap-1.5 flex-wrap justify-center">
                 {currentScene.detections.map((det) => {
                   const isHazard = det.label === 'fire' || det.label === 'smoke';
                   const bgClass = isHazard ? 'bg-red-500/20' : 'bg-black/60';
                   const borderClass = isHazard ? 'border-red-500/50 shadow-[0_0_15px_rgba(239,68,68,0.4)]' : 'border-white/20';
                   const textClass = isHazard ? 'text-red-500' : 'text-white/80';
                   
                   return (
                     <div key={det.label} className={`backdrop-blur-md px-2 py-0.5 rounded-sm border ${borderClass} ${bgClass} transition-all duration-300`}>
                       <span className={`font-mono text-[9px] font-bold tracking-widest uppercase ${textClass}`}>
                         {det.label} · {Math.round(det.conf * 100)}%
                       </span>
                     </div>
                   );
                 })}
               </div>

               {/* Description Box */}
               <div className="backdrop-blur-md px-3 py-1.5 rounded-sm border border-white/20 bg-black/60 w-full text-center transition-all duration-500 max-w-lg">
                  <span className="font-mono text-[10px] uppercase tracking-widest text-white/90">
                    {currentScene.desc}
                  </span>
               </div>
               
             </div>
          </div>
        )}

        {/* HUD Elements */}
        {isActive && (
          <>
            <div className="absolute top-14 left-4 z-30">
              {isBroadcasting && (
                <div className="flex bg-amber-500/90 text-black px-3 py-1.5 rounded-sm items-center gap-2 animate-[pulse_1s_ease-in-out_infinite] shadow-[0_0_20px_rgba(245,158,11,0.6)]">
                  <Volume2 className="w-4 h-4" />
                  <span className="font-mono text-[10px] font-bold tracking-widest uppercase">Evacuation Warning</span>
                </div>
              )}
            </div>

            <div className="absolute bottom-4 left-4 font-mono text-[10px] dark:text-white/40 text-black/50">
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

import { cn } from "@/lib/utils";
import { Loader2, Play, CheckCircle2 } from "lucide-react";

interface ActionButtonProps {
  onStart: () => void;
  onApprove: () => void;
  status: string;
  isStarting: boolean;
  isApproving: boolean;
  recommendedCount?: number;
  confirmedCount?: number;
}

export function ActionButton({ 
  onStart, 
  onApprove, 
  status, 
  isStarting, 
  isApproving,
  recommendedCount = 0,
  confirmedCount = 0
}: ActionButtonProps) {
  
  if (status === 'resolved_demo') {
    return (
      <button 
        disabled
        className="w-full h-14 bg-emerald-500/20 border border-emerald-500/50 text-emerald-600 dark:text-emerald-400 font-mono text-sm tracking-widest uppercase flex items-center justify-center gap-2 rounded-sm cursor-not-allowed transition-all"
      >
        <CheckCircle2 className="w-5 h-5" />
        Incident Resolved
      </button>
    );
  }

  if (status === 'active' || status === 'escalated' || status === 'critical' || status === 'intake') {
    
    // State 3: Confirmed
    if (confirmedCount > 0) {
      return (
        <button 
          disabled
          className="w-full h-14 bg-emerald-500/10 border border-emerald-500/30 text-emerald-600 dark:text-emerald-500 font-mono text-sm font-bold tracking-widest uppercase flex items-center justify-center gap-2 rounded-sm transition-all duration-1000 cursor-not-allowed"
        >
          <CheckCircle2 className="w-5 h-5" />
          Response Approved
        </button>
      );
    }

    // State 2: Pulsing/Glowing - Waiting for approval
    if (recommendedCount > 0 && confirmedCount === 0) {
      return (
        <button 
          onClick={onApprove}
          disabled={isApproving}
          className={cn(
            "w-full h-14 font-mono text-sm font-bold tracking-widest uppercase flex items-center justify-center gap-2 rounded-sm transition-all shadow-[0_0_20px_rgba(59,130,246,0.3)] hover:shadow-[0_0_30px_rgba(59,130,246,0.5)]",
            isApproving 
              ? "bg-blue-600/50 dark:text-white/50 text-white border border-blue-500/30" 
              : "bg-blue-600 text-white border border-blue-400 hover:bg-blue-500 animate-pulse"
          )}
        >
          {isApproving ? <Loader2 className="w-5 h-5 animate-spin" /> : "Approve Initial Response"}
        </button>
      );
    }

    // State 1: Disabled/Grey - Awaiting intelligence (hasn't reached approval gate)
    return (
      <button 
        disabled
        className="w-full h-14 dark:bg-white/5 bg-black/5 dark:text-white/30 text-black/30 border dark:border-white/10 border-black/10 font-mono text-sm font-bold tracking-widest uppercase flex items-center justify-center gap-2 rounded-sm cursor-not-allowed transition-all"
      >
        Awaiting Intelligence
      </button>
    );
  }

  // Not started yet
  return (
    <button 
      onClick={onStart}
      disabled={isStarting}
      className={cn(
        "w-full h-14 font-mono text-sm font-bold tracking-widest uppercase flex items-center justify-center gap-2 rounded-sm transition-all",
        isStarting 
          ? "dark:bg-white/5 bg-black/5 dark:text-white/30 text-black/40 border dark:border-white/10 border-black/10" 
          : "dark:bg-white bg-black dark:text-black text-white hover:opacity-90 border border-transparent dark:shadow-[0_0_20px_rgba(255,255,255,0.2)] shadow-[0_0_20px_rgba(0,0,0,0.2)]"
      )}
    >
      {isStarting ? (
        <>
          <Loader2 className="w-5 h-5 animate-spin" />
          Initializing
        </>
      ) : (
        <>
          <Play className="w-4 h-4" />
          Start Demo
        </>
      )}
    </button>
  );
}

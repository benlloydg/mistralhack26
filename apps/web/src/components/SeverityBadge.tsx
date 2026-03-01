import { cn } from "@/lib/utils";

export function SeverityBadge({ severity }: { severity: string }) {
  const getSeverityStyles = () => {
    switch (severity?.toLowerCase()) {
      case 'critical': 
        return 'border-red-500 text-red-500 bg-red-500/10 shadow-[0_0_15px_rgba(239,68,68,0.5)] animate-pulse';
      case 'high': 
        return 'border-orange-500 text-orange-500 bg-orange-500/10';
      case 'medium': 
        return 'border-amber-500 text-amber-500 bg-amber-500/10';
      case 'low': 
        return 'border-emerald-500 text-emerald-500 bg-emerald-500/10';
      default: 
        return 'border-white/20 text-white/40 bg-white/5';
    }
  };

  return (
    <div key={severity} className={cn(
      "px-3 py-1.5 rounded-sm border uppercase font-mono text-xs font-bold tracking-widest flex items-center gap-2 animate-in fade-in zoom-in-75 duration-500",
      getSeverityStyles()
    )}>
      {severity?.toLowerCase() === 'critical' && (
        <span className="w-2 h-2 rounded-full bg-red-500 animate-ping"></span>
      )}
      {severity ? severity : 'UNKNOWN'}
    </div>
  );
}

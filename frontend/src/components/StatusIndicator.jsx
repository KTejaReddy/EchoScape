export default function StatusIndicator({ tone = "cyan", label, pulse = false, className = "" }) {
  const colors = {
    cyan: "bg-cyan-400 shadow-[0_0_10px_rgba(34,211,238,0.9)]",
    green: "bg-emerald-400 shadow-[0_0_10px_rgba(52,211,153,0.9)]",
    amber: "bg-amber-400 shadow-[0_0_10px_rgba(251,191,36,0.9)]",
    red: "bg-rose-400 shadow-[0_0_10px_rgba(251,113,133,0.9)]",
    slate: "bg-slate-500 shadow-none",
  };
  return (
    <span className={`inline-flex items-center gap-2 ${className}`}>
      <span className={`dot ${colors[tone]} ${pulse ? "animate-pulse" : ""}`} />
      <span className="font-mono text-[11px] uppercase tracking-[0.16em] text-slate-300">{label}</span>
    </span>
  );
}

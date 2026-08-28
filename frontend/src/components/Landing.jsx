import { Radar, ArrowRight, Sparkles } from "lucide-react";

export default function Landing({ onStart, onTryDemo }) {
  return (
    <div className="relative flex h-full flex-col items-center justify-center px-6">
      {/* ambient glow */}
      <div className="pointer-events-none absolute left-1/2 top-1/2 h-[520px] w-[720px] -translate-x-1/2 -translate-y-1/2 rounded-full bg-cyan-500/10 blur-[120px]" />

      <div className="relative z-10 flex max-w-2xl flex-col items-center text-center animate-fade-in">
        <div className="glass hero-ring mb-8 flex h-20 w-20 items-center justify-center">
          <Radar className="h-10 w-10 text-cyan-300 text-glow" />
        </div>

        <div className="font-mono text-[11px] uppercase tracking-[0.4em] text-cyan-400/80">
          The $0-Budget Spatial Radar
        </div>
        <h1 className="mt-3 text-6xl font-bold tracking-tight text-white">
          Echo<span className="text-cyan-300 text-glow">Scape</span>
        </h1>

        <p className="mt-6 max-w-xl text-base leading-relaxed text-slate-400">
          Camera-free spatial presence sensing using only your laptop's built-in
          speakers and microphones. EchoScape plays an inaudible acoustic probe,
          listens to how the room reflects it, and visualises estimated movement
          inside an AI-generated 3D room.
        </p>

        <div className="mt-8 flex flex-col items-center gap-3 sm:flex-row">
          <button className="btn-primary px-6 py-3 text-base" onClick={onStart}>
            <Sparkles className="h-4 w-4" /> Create Spatial Map
          </button>
          <button className="btn-ghost px-6 py-3 text-base" onClick={onTryDemo}>
            Try the Demo Room <ArrowRight className="h-4 w-4" />
          </button>
        </div>

        <div className="mt-12 grid grid-cols-1 gap-3 text-left sm:grid-cols-3">
          {[
            ["01", "Acoustic Sensing", "Inaudible probe tone + room reflections"],
            ["02", "AI Digital Twin", "A photo becomes a 3D room via Groq Vision"],
            ["03", "Live Spatial View", "Estimated position, ripples and trajectory"],
          ].map(([n, title, sub]) => (
            <div key={n} className="glass p-4">
              <div className="font-mono text-[10px] text-cyan-400/70">{n}</div>
              <div className="mt-1 text-sm font-semibold text-slate-200">{title}</div>
              <div className="mt-1 text-xs leading-relaxed text-slate-500">{sub}</div>
            </div>
          ))}
        </div>

        <p className="mt-10 max-w-md font-mono text-[10px] uppercase tracking-[0.2em] text-slate-600">
          Experimental spatial sensing · Camera-free during live monitoring
        </p>
      </div>
    </div>
  );
}

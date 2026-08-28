import RoomCanvas from "./RoomCanvas";
import Dashboard from "./Dashboard";
import StatusIndicator from "./StatusIndicator";

export default function LiveView({ esc }) {
  return (
    <div className="flex h-full flex-col">
      {/* top bar */}
      <header className="flex items-center justify-between border-b border-edge bg-panel/50 px-4 py-2 backdrop-blur-md">
        <div className="flex items-center gap-3">
          <span className="font-mono text-[10px] uppercase tracking-[0.3em] text-slate-500">
            Live Spatial View
          </span>
          <span className="rounded-md border border-edge bg-white/[0.03] px-2 py-0.5 font-mono text-[10px] text-slate-400">
            ROOM {esc.room.room.width.toFixed(1)} × {esc.room.room.depth.toFixed(1)} m
          </span>
          <span
            className={`rounded-md border px-2 py-0.5 font-mono text-[10px] ${
              esc.roomSource === "ai"
                ? "border-cyan-400/30 bg-cyan-400/10 text-cyan-300"
                : "border-amber-400/25 bg-amber-400/5 text-amber-300"
            }`}
          >
            {esc.roomSource === "ai" ? "AI ROOM" : "DEMO ROOM"}
          </span>
        </div>
        <div className="flex items-center gap-4">
          <StatusIndicator
            tone={esc.sensorMode === "demo" ? "amber" : esc.sensorMode === "real" ? "cyan" : "slate"}
            label={esc.sensorMode === "demo" ? "● DEMO MODE — synthetic data" : esc.sensorMode === "real" ? "● LIVE ACOUSTIC" : "STANDBY"}
            pulse={esc.sensorMode !== null}
          />
        </div>
      </header>

      {/* main area */}
      <div className="relative flex min-h-0 flex-1">
        <div className="relative min-w-0 flex-1">
          <RoomCanvas
            room={esc.room}
            spatial={esc.spatial}
            trajectory={esc.trajectory}
            ripples={esc.ripples}
            onRippleExpire={esc.removeRipple}
          />
          {/* corner hint */}
          <div className="pointer-events-none absolute bottom-3 left-3 rounded-md border border-edge bg-black/30 px-2 py-1 font-mono text-[10px] text-slate-500 backdrop-blur-sm">
            drag to orbit · scroll to zoom
          </div>
        </div>
        <Dashboard esc={esc} />
      </div>
    </div>
  );
}

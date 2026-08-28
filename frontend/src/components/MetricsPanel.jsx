import { CameraOff, Cpu, Locate } from "lucide-react";

function Meter({ label, value, pct, color = "bg-cyan-400" }) {
  return (
    <div>
      <div className="flex items-baseline justify-between">
        <span className="label">{label}</span>
        <span className="value">{value}</span>
      </div>
      <div className="mt-1 h-1 overflow-hidden rounded-full bg-white/5">
        <div
          className={`h-full rounded-full ${color} transition-all duration-200`}
          style={{ width: `${Math.min(Math.max(pct, 0), 100)}%`, boxShadow: "0 0 8px rgba(34,211,238,0.6)" }}
        />
      </div>
    </div>
  );
}

export default function MetricsPanel({ spatial, motionDetected }) {
  const s = spatial;
  const conf = s?.confidence ?? 0;
  const signal = s?.signal_strength ?? 0;
  const speed = s?.speed ?? 0;
  const dir = s?.direction_label ?? "—";
  const bearing = s?.direction ?? 0;
  const freq = s?.frequency ? Math.round(s.frequency) : "—";
  const freqShift = s?.frequency_shift ?? 0;

  const rows = [
    ["X", s?.position?.x?.toFixed(2) ?? "0.00", "m"],
    ["Y", s?.position?.y?.toFixed(2) ?? "0.00", "m"],
    ["Z", s?.position?.z?.toFixed(2) ?? "0.00", "m"],
  ];

  return (
    <div className="glass-tight p-3">
      <div className="label mb-3 flex items-center gap-2">
        <Locate className="h-3 w-3" /> Estimated Position
      </div>

      <div className="mb-3 grid grid-cols-3 gap-2">
        {rows.map(([k, v, unit]) => (
          <div key={k} className="rounded-md border border-edge bg-white/[0.02] px-2 py-1.5 text-center">
            <div className="label">{k}</div>
            <div className="value mt-0.5">
              {v} <span className="text-[9px] text-slate-500">{unit}</span>
            </div>
          </div>
        ))}
      </div>

      <div className="space-y-2.5">
        <div className="flex items-baseline justify-between">
          <span className="label">Direction</span>
          <span className="value">
            {dir} <span className="text-slate-500">{bearing.toFixed(0)}°</span>
          </span>
        </div>
        <div className="flex items-baseline justify-between">
          <span className="label">Speed</span>
          <span className="value">{speed.toFixed(2)} m/s</span>
        </div>
        <div className="flex items-baseline justify-between">
          <span className="label">Frequency</span>
          <span className="value">
            {freq} Hz <span className="text-[10px] text-slate-500">(Δ {freqShift >= 0 ? "+" : ""}{freqShift.toFixed(0)})</span>
          </span>
        </div>
      </div>

      <div className="mt-3 space-y-2.5 border-t border-white/5 pt-3">
        <Meter
          label="Confidence"
          value={`${Math.round(conf * 100)}%`}
          pct={conf * 100}
          color={motionDetected ? "bg-cyan-400" : "bg-slate-500"}
        />
        <Meter label="Signal" value={`${Math.round(signal * 100)}%`} pct={signal * 100} color="bg-emerald-400" />
        <div className="flex gap-2 pt-1">
          <div className="flex flex-1 items-center gap-2 rounded-md border border-edge bg-white/[0.02] px-2 py-1.5">
            <CameraOff className="h-3.5 w-3.5 text-slate-400" />
            <div>
              <div className="label">Camera</div>
              <div className="font-mono text-[11px] text-emerald-300">OFF</div>
            </div>
          </div>
          <div className="flex flex-1 items-center gap-2 rounded-md border border-edge bg-white/[0.02] px-2 py-1.5">
            <Cpu className="h-3.5 w-3.5 text-slate-400" />
            <div>
              <div className="label">Ext. hardware</div>
              <div className="font-mono text-[11px] text-slate-300">NONE</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

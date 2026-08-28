import StatusIndicator from "./StatusIndicator";
import MetricsPanel from "./MetricsPanel";
import SignalMonitor from "./SignalMonitor";
import AcousticConcept from "./AcousticConcept";
import ControlPanel from "./ControlPanel";
import { Radar } from "lucide-react";

export default function Dashboard({ esc }) {
  const running = esc.sensorMode !== null;
  const motionDetected = Boolean(esc.spatial?.motion);
  const calibrating = esc.calibration.state === "running";

  return (
    <aside className="flex w-[340px] shrink-0 flex-col gap-3 overflow-y-auto border-l border-edge bg-panel/60 p-3 backdrop-blur-md">
      {/* brand */}
      <div className="flex items-center gap-2.5 px-1 pt-1">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg border border-cyan-400/25 bg-cyan-400/10">
          <Radar className="h-4 w-4 text-cyan-300" />
        </div>
        <div>
          <div className="text-sm font-bold tracking-wide text-white">
            ECHO<span className="text-cyan-300">SCAPE</span>
          </div>
          <div className="font-mono text-[9px] uppercase tracking-[0.25em] text-slate-600">
            $0-Budget Spatial Radar
          </div>
        </div>
      </div>

      {/* system status */}
      <div className="glass-tight p-3">
        <div className="label mb-2">System Status</div>
        <div className="space-y-2">
          <StatusIndicator tone="green" label="SYSTEM — ONLINE" pulse={false} />
          <StatusIndicator
            tone={running ? "green" : "slate"}
            label={running ? "SENSOR — ACTIVE" : "SENSOR — IDLE"}
            pulse={running}
          />
          <StatusIndicator
            tone={esc.sensorMode === "demo" ? "amber" : esc.sensorMode === "real" ? "cyan" : "slate"}
            label={esc.sensorMode === "demo" ? "MODE — DEMO" : esc.sensorMode === "real" ? "MODE — REAL ACOUSTIC" : "MODE — STANDBY"}
            pulse={esc.sensorMode === "demo"}
          />
          <StatusIndicator
            tone={motionDetected ? "cyan" : "slate"}
            label={motionDetected ? "MOTION — DETECTED" : "MOTION — IDLE"}
            pulse={motionDetected}
          />
          <StatusIndicator
            tone={esc.wsStatus === "connected" ? "green" : esc.wsStatus === "connecting" ? "amber" : "red"}
            label={`WEBSOCKET — ${esc.wsStatus.toUpperCase()}`}
            pulse={esc.wsStatus !== "connected"}
          />
        </div>
      </div>

      {/* metrics */}
      <MetricsPanel spatial={esc.spatial} motionDetected={motionDetected} />

      {/* signal monitor */}
      <SignalMonitor spatial={esc.spatial} />

      {/* calibration progress */}
      {calibrating && (
        <div className="glass-tight border-cyan-400/25 p-3">
          <div className="label mb-1">Calibration</div>
          <div className="text-xs text-slate-300">Keep the room still — measuring acoustic baseline…</div>
          <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-white/5">
            <div
              className="h-full bg-cyan-400 transition-all duration-200"
              style={{ width: `${Math.round(esc.calibration.progress * 100)}%` }}
            />
          </div>
        </div>
      )}
      {esc.calibration.state === "done" && esc.calibration.baseline && (
        <div className="glass-tight border-emerald-400/20 p-3">
          <div className="label mb-1 text-emerald-300/80">Calibration Complete</div>
          <div className="font-mono text-[11px] leading-relaxed text-slate-400">
            noise floor {esc.calibration.baseline.noise_floor?.toExponential?.(1) ?? "—"} · signal{" "}
            {Math.round((esc.calibration.baseline.signal_strength ?? 0) * 100)}%
          </div>
        </div>
      )}

      <AcousticConcept active={running} />
      <ControlPanel
        sensorMode={esc.sensorMode}
        onStartReal={esc.startSensor}
        onStartDemo={esc.startSensor}
        onStop={esc.stopSensor}
        onCalibrate={esc.calibrate}
        calibrating={calibrating}
        onClearTrajectory={esc.clearTrajectory}
        onCreateRoom={esc.goToSetup}
        onResetRoom={esc.useDemoRoom}
      />
    </aside>
  );
}

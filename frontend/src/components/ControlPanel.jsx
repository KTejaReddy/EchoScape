import {
  Play, StopCircle, Waves, FlaskConical, Eraser, Plus, RotateCcw, Loader2,
} from "lucide-react";

export default function ControlPanel({
  sensorMode,
  onStartReal,
  onStartDemo,
  onStop,
  onCalibrate,
  calibrating,
  onClearTrajectory,
  onCreateRoom,
  onResetRoom,
}) {
  const running = sensorMode !== null;

  return (
    <div className="glass-tight p-3">
      <div className="label mb-3">Controls</div>
      <div className="grid grid-cols-2 gap-2">
        <button className="btn-primary" disabled={running || calibrating} onClick={() => onStartReal("real")}>
          <Waves className="h-4 w-4" /> Real Mode
        </button>
        <button className="btn-ghost" disabled={running || calibrating} onClick={() => onStartDemo("demo")}>
          <Play className="h-4 w-4" /> Demo Mode
        </button>
        <button className="btn-danger" disabled={!running} onClick={onStop}>
          <StopCircle className="h-4 w-4" /> Stop
        </button>
        <button
          className="btn-ghost"
          disabled={sensorMode !== "real" || calibrating}
          onClick={onCalibrate}
          title={sensorMode !== "real" ? "Start Real Mode first" : "Measure acoustic baseline"}
        >
          {calibrating ? <Loader2 className="h-4 w-4 animate-spin" /> : <FlaskConical className="h-4 w-4" />}
          Calibrate
        </button>
        <button className="btn-ghost" onClick={onClearTrajectory}>
          <Eraser className="h-4 w-4" /> Clear Path
        </button>
        <button className="btn-ghost" onClick={onCreateRoom}>
          <Plus className="h-4 w-4" /> Create Room
        </button>
      </div>
      <button className="btn-ghost mt-2 w-full" onClick={onResetRoom}>
        <RotateCcw className="h-4 w-4" /> Reset to Demo Room
      </button>
    </div>
  );
}

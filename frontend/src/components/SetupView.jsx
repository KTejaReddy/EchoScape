import RoomUploader from "./RoomUploader";

export default function SetupView({ onAnalyze, analyzing, analyzeStage, onUseDemo, onBack }) {
  return (
    <div className="flex h-full flex-col items-center justify-center overflow-y-auto px-6 py-10">
      <div className="mb-8 text-center">
        <div className="font-mono text-[11px] uppercase tracking-[0.35em] text-cyan-400/80">
          Step 1 — AI Digital Twin
        </div>
        <h1 className="mt-2 text-3xl font-bold text-white">Map your space</h1>
      </div>
      <RoomUploader
        onAnalyze={onAnalyze}
        analyzing={analyzing}
        analyzeStage={analyzeStage}
        onUseDemo={onUseDemo}
        onBack={onBack}
      />
    </div>
  );
}

import { useRef, useState } from "react";
import { Upload, ImageIcon, Loader2, Wand2, ArrowLeft } from "lucide-react";

export default function RoomUploader({ onAnalyze, analyzing, analyzeStage, onUseDemo, onBack }) {
  const inputRef = useRef(null);
  const [preview, setPreview] = useState(null);
  const [file, setFile] = useState(null);
  const [dragOver, setDragOver] = useState(false);

  const pick = (f) => {
    if (!f || !f.type.startsWith("image/")) return;
    setFile(f);
    setPreview(URL.createObjectURL(f));
  };

  const analyze = () => {
    if (file) onAnalyze(file);
  };

  return (
    <div className="glass w-full max-w-xl p-6 animate-slide-up">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-slate-100">Create Room</h2>
        <button className="btn-ghost px-2 py-1 text-xs" onClick={onBack}>
          <ArrowLeft className="h-3 w-3" /> Back
        </button>
      </div>
      <p className="mt-1 text-sm text-slate-500">
        Upload a photo of the room. EchoScape's AI will estimate the layout and
        build a stylized 3D digital twin.
      </p>

      {/* upload zone */}
      {!preview ? (
        <button
          onClick={() => inputRef.current?.click()}
          onDragOver={(e) => {
            e.preventDefault();
            setDragOver(true);
          }}
          onDragLeave={() => setDragOver(false)}
          onDrop={(e) => {
            e.preventDefault();
            setDragOver(false);
            pick(e.dataTransfer.files?.[0]);
          }}
          className={`mt-5 flex w-full flex-col items-center justify-center gap-3 rounded-xl border-2 border-dashed px-6 py-12 transition-colors ${
            dragOver
              ? "border-cyan-400/60 bg-cyan-400/5"
              : "border-edge bg-white/[0.02] hover:border-cyan-400/30 hover:bg-cyan-400/5"
          }`}
        >
          <Upload className="h-8 w-8 text-cyan-300/70" />
          <div className="text-sm text-slate-300">Click or drop a room photo</div>
          <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-600">
            JPG · PNG · WEBP
          </div>
        </button>
      ) : (
        <div className="relative mt-5 overflow-hidden rounded-xl border border-edge">
          <img src={preview} alt="Room preview" className="max-h-72 w-full object-cover" />
          <button
            className="absolute right-2 top-2 rounded-md bg-black/60 px-2 py-1 font-mono text-[10px] text-slate-300 hover:text-white"
            onClick={() => {
              setPreview(null);
              setFile(null);
            }}
          >
            ✕ remove
          </button>
        </div>
      )}

      <input
        ref={inputRef}
        type="file"
        accept="image/*"
        className="hidden"
        onChange={(e) => pick(e.target.files?.[0])}
      />

      {/* progress / actions */}
      {analyzing ? (
        <div className="mt-5 space-y-2">
          <div className="flex items-center gap-2 text-sm text-cyan-200">
            <Loader2 className="h-4 w-4 animate-spin" />
            {analyzeStage || "Analyzing spatial environment…"}
          </div>
          <div className="h-1.5 overflow-hidden rounded-full bg-white/5">
            <div className="h-full w-full animate-pulse rounded-full bg-cyan-400/60" />
          </div>
          <div className="flex gap-2 pt-2">
            {["Detecting furniture…", "Building digital twin…"].map((s, i) => (
              <span key={s} className="glass-tight px-2 py-1 font-mono text-[10px] text-slate-500">
                {s}
              </span>
            ))}
          </div>
        </div>
      ) : (
        <div className="mt-5 flex flex-col gap-2 sm:flex-row">
          <button className="btn-primary flex-1 py-2.5" disabled={!file} onClick={analyze}>
            {file ? <Wand2 className="h-4 w-4" /> : <ImageIcon className="h-4 w-4" />}
            {file ? "Analyze Room" : "Upload Room Image"}
          </button>
          <button className="btn-ghost flex-1 py-2.5" onClick={onUseDemo}>
            Use Demo Room
          </button>
        </div>
      )}

      <p className="mt-4 font-mono text-[10px] leading-relaxed text-slate-600">
        No GROQ_API_KEY? The app gracefully falls back to a default demo room —
        the entire pipeline still works.
      </p>
    </div>
  );
}

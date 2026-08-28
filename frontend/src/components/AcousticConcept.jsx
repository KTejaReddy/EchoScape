import { useEffect, useRef, useState } from "react";
import { Volume2, AudioWaveform } from "lucide-react";

/**
 * "How it works" strip: speaker emits the acoustic probe, the stereo mics
 * receive it, and the system estimates position. Helps judges grasp the
 * concept without reading a wall of text.
 */
export default function AcousticConcept({ active }) {
  const [phase, setPhase] = useState(0);
  const rafRef = useRef(0);

  useEffect(() => {
    let t = 0;
    const loop = () => {
      t += 0.03;
      setPhase(t);
      rafRef.current = requestAnimationFrame(loop);
    };
    rafRef.current = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(rafRef.current);
  }, []);

  const waveOpacity = active ? 0.9 : 0.35;

  return (
    <div className="glass-tight p-3">
      <div className="label mb-3">Acoustic Sensing</div>
      <div className="flex items-center justify-between">
        {/* speaker */}
        <div className="flex flex-col items-center gap-1">
          <div className="flex h-9 w-9 items-center justify-center rounded-full border border-cyan-400/30 bg-cyan-400/10">
            <Volume2 className="h-4 w-4 text-cyan-300" />
          </div>
          <span className="font-mono text-[9px] text-slate-500">SPEAKER</span>
        </div>

        {/* wave */}
        <div className="relative h-10 flex-1 overflow-hidden px-2">
          {[0, 1, 2].map((i) => {
            const p = (phase * (0.7 + i * 0.25) + i * 0.4) % 1;
            return (
              <div
                key={i}
                className="absolute top-1/2 h-0.5 -translate-y-1/2 rounded-full bg-cyan-400"
                style={{
                  width: `${10 + p * 70}%`,
                  left: "8%",
                  opacity: waveOpacity * (1 - p),
                  boxShadow: "0 0 8px rgba(34,211,238,0.8)",
                }}
              />
            );
          })}
        </div>

        {/* mics */}
        <div className="flex flex-col items-center gap-1">
          <div className="flex items-center gap-1.5">
            <div className="flex h-9 w-9 items-center justify-center rounded-full border border-emerald-400/30 bg-emerald-400/10">
              <AudioWaveform className="h-4 w-4 text-emerald-300" />
            </div>
            <span className="font-mono text-[9px] text-slate-500">MIC L</span>
          </div>
          <div className="h-1 w-6 rounded bg-slate-600" />
          <div className="flex items-center gap-1.5">
            <div className="flex h-9 w-9 items-center justify-center rounded-full border border-emerald-400/30 bg-emerald-400/10">
              <AudioWaveform className="h-4 w-4 text-emerald-300" />
            </div>
            <span className="font-mono text-[9px] text-slate-500">MIC R</span>
          </div>
        </div>
      </div>
      <p className="mt-3 text-[11px] leading-relaxed text-slate-500">
        Probe tone → room reflection → stereo capture → FFT + TDOA → estimated position.
      </p>
    </div>
  );
}

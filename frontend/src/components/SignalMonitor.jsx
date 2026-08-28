import { useEffect, useRef } from "react";

const HISTORY = 140;

/**
 * Lightweight canvas monitor: a stylised spectrum centred on the carrier and a
 * scrolling line chart of signal strength + motion intensity. No chart library
 * needed — keeps the bundle small and the 3D room dominant.
 */
export default function SignalMonitor({ spatial }) {
  const canvasRef = useRef();
  const bufferRef = useRef({ signal: [], motion: [], freq: [] });

  useEffect(() => {
    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d");
    let raf = 0;
    let mounted = true;

    const resize = () => {
      const rect = canvas.getBoundingClientRect();
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      canvas.width = Math.max(1, Math.floor(rect.width * dpr));
      canvas.height = Math.max(1, Math.floor(rect.height * dpr));
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    };
    resize();
    const observer = new ResizeObserver(resize);
    observer.observe(canvas);

    const draw = () => {
      if (!mounted) return;
      raf = requestAnimationFrame(draw);

      const buf = bufferRef.current;
      if (spatial) {
        buf.signal.push(spatial.signal_strength ?? 0);
        buf.motion.push(spatial.motion_score ?? (spatial.motion ? 0.6 : 0.1));
        buf.freq.push(Math.max(-120, Math.min(120, spatial.frequency_shift ?? 0)));
        if (buf.signal.length > HISTORY) {
          buf.signal.shift();
          buf.motion.shift();
          buf.freq.shift();
        }
      }

      const w = canvas.clientWidth;
      const h = canvas.clientHeight;
      ctx.clearRect(0, 0, w, h);

      // ---- spectrum (stylised) ----
      const specTop = h * 0.34;
      const nBars = 40;
      const barW = w / nBars;
      for (let i = 0; i < nBars; i++) {
        const center = nBars / 2;
        const dist = Math.abs(i - center) / center;
        const lastShift = buf.freq[buf.freq.length - 1] ?? 0;
        const shifted = Math.abs((i - center) - lastShift * 0.25) / center;
        const base = Math.max(0.08, 1 - dist * 1.4);
        const boost = spatial?.motion ? 0.5 : 0.15;
        const v = Math.min(1, base * (0.55 + (spatial?.signal_strength ?? 0) * 0.9) + boost * Math.max(0, 1 - shifted * 2.2));
        const bh = Math.max(1, v * specTop);
        ctx.fillStyle = v > 0.6 ? "rgba(103,232,249,0.9)" : v > 0.3 ? "rgba(34,211,238,0.55)" : "rgba(34,211,238,0.22)";
        ctx.fillRect(i * barW + 1, specTop - bh, barW - 2, bh);
      }

      // ---- scrolling lines ----
      const linesTop = h * 0.42;
      const linesH = h * 0.58 - 8;
      const plot = (data, color, thick) => {
        ctx.beginPath();
        data.forEach((v, i) => {
          const x = (i / (HISTORY - 1)) * w;
          const y = linesTop + linesH - v * linesH;
          if (i === 0) ctx.moveTo(x, y);
          else ctx.lineTo(x, y);
        });
        ctx.strokeStyle = color;
        ctx.lineWidth = thick;
        ctx.stroke();
      };
      ctx.save();
      ctx.shadowBlur = 6;
      ctx.shadowColor = "rgba(34,211,238,0.6)";
      plot(buf.motion, "rgba(251,191,36,0.85)", 1.4);
      plot(buf.signal, "rgba(34,211,238,0.95)", 1.6);
      ctx.restore();

      // grid + labels
      ctx.strokeStyle = "rgba(56,189,248,0.10)";
      ctx.lineWidth = 1;
      for (let i = 1; i < 4; i++) {
        const y = linesTop + (linesH / 4) * i;
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(w, y);
        ctx.stroke();
      }

      // legend
      ctx.font = "10px 'JetBrains Mono', monospace";
      ctx.fillStyle = "rgba(148,163,184,0.9)";
      ctx.fillText("— SIGNAL", 8, linesTop + linesH - 4);
      ctx.fillStyle = "rgba(251,191,36,0.9)";
      ctx.fillText("— MOTION", 74, linesTop + linesH - 4);
      ctx.fillStyle = "rgba(148,163,184,0.7)";
      ctx.fillText("CARRIER " + (spatial?.frequency ? Math.round(spatial.frequency) : "—"), w - 130, linesTop + linesH - 4);
    };
    raf = requestAnimationFrame(draw);

    return () => {
      mounted = false;
      cancelAnimationFrame(raf);
      observer.disconnect();
    };
  }, []);

  return (
    <div className="glass-tight p-3">
      <div className="label mb-2 flex items-center justify-between">
        <span>Signal Monitor</span>
        <span className="normal-case tracking-normal text-slate-600">Hz ± {spatial?.frequency_shift ? `${spatial.frequency_shift.toFixed(0)}` : "0"}</span>
      </div>
      <canvas ref={canvasRef} className="h-28 w-full" />
    </div>
  );
}

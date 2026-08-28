import { AlertTriangle, CheckCircle2, X, Radio } from "lucide-react";

export default function ErrorBanner({ error, notice, audioError, onDismiss, onUseDemo }) {
  if (audioError) {
    return (
      <div className="absolute inset-x-0 bottom-6 z-50 flex justify-center px-6">
        <div className="glass w-full max-w-xl border-rose-400/25 p-5 animate-slide-up">
          <div className="flex items-start gap-3">
            <AlertTriangle className="mt-0.5 h-5 w-5 shrink-0 text-rose-300" />
            <div className="flex-1">
              <div className="font-mono text-sm font-semibold tracking-wide text-rose-200">
                Microphone unavailable
              </div>
              <p className="mt-1.5 text-sm leading-relaxed text-slate-300">
                EchoScape cannot access the selected input device. You can:
              </p>
              <ul className="mt-2 list-inside list-disc space-y-1 text-sm text-slate-400">
                <li>check OS microphone permissions and retry</li>
                <li>select another audio device in backend/.env (AUDIO_DEVICE)</li>
                <li>switch to Demo Mode — the live 3D pipeline stays identical</li>
              </ul>
              <div className="mt-4 flex gap-2">
                <button className="btn-primary" onClick={onUseDemo}>
                  <Radio className="h-4 w-4" /> Switch to Demo Mode
                </button>
                <button className="btn-ghost" onClick={onDismiss}>Dismiss</button>
              </div>
            </div>
            <button className="text-slate-500 hover:text-slate-300" onClick={onDismiss} aria-label="Close">
              <X className="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="absolute inset-x-0 bottom-6 z-50 flex justify-center px-6">
        <div className="glass w-full max-w-xl border-amber-400/25 p-4 animate-slide-up">
          <div className="flex items-start gap-3">
            <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-amber-300" />
            <p className="flex-1 text-sm leading-relaxed text-slate-300">{error}</p>
            <button className="text-slate-500 hover:text-slate-300" onClick={onDismiss} aria-label="Close">
              <X className="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (notice) {
    return (
      <div className="absolute inset-x-0 bottom-6 z-40 flex justify-center px-6">
        <div className="glass w-full max-w-xl border-emerald-400/20 p-4 animate-fade-in">
          <div className="flex items-start gap-3">
            <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-emerald-300" />
            <p className="flex-1 text-sm text-slate-300">{notice}</p>
          </div>
        </div>
      </div>
    );
  }

  return null;
}

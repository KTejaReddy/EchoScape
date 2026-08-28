import { useEchoScape } from "./hooks/useEchoScape";
import Landing from "./components/Landing";
import SetupView from "./components/SetupView";
import LiveView from "./components/LiveView";
import ErrorBanner from "./components/ErrorBanner";

export default function App() {
  const esc = useEchoScape();

  if (!esc.room) {
    return (
      <div className="flex h-full items-center justify-center bg-void">
        <div className="font-mono text-sm text-cyan-300/70 animate-pulse">INITIALIZING ECHOSCAPE…</div>
      </div>
    );
  }

  return (
    <div className="relative h-full overflow-hidden bg-void bg-grid-pattern">
      {esc.view === "landing" && <Landing onStart={() => esc.goToSetup()} onTryDemo={() => esc.goToLive()} />}
      {esc.view === "setup" && (
        <SetupView
          onBack={() => esc.goToLive()}
          onAnalyze={esc.analyzeRoom}
          onUseDemo={esc.useDemoRoom}
          analyzing={esc.analyzing}
          analyzeStage={esc.analyzeStage}
        />
      )}
      {esc.view === "live" && <LiveView esc={esc} />}
      <ErrorBanner
        error={esc.error}
        notice={esc.notice}
        audioError={esc.audioError}
        onDismiss={() => esc.setError(null)}
        onUseDemo={() => {
          esc.setError(null);
          esc.setAudioError(false);
          esc.startSensor("demo");
        }}
      />
    </div>
  );
}

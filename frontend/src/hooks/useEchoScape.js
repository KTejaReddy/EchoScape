import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import * as api from "../services/api";
import { useWebSocket } from "./useWebSocket";

const TRAJECTORY_MAX = 220;
const RIPPLE_MAX = 8;

let rippleId = 0;

/**
 * Single source of truth for the EchoScape app: room layout, sensor state,
 * live spatial data, trajectory, ripples and friendly error handling.
 */
export function useEchoScape() {
  const [view, setView] = useState("landing"); // landing | setup | live
  const [room, setRoom] = useState(null);
  const [roomSource, setRoomSource] = useState("demo"); // ai | demo
  const [analyzing, setAnalyzing] = useState(false);
  const [analyzeStage, setAnalyzeStage] = useState("");

  const [sensorMode, setSensorMode] = useState(null); // real | demo | null
  const [spatial, setSpatial] = useState(null);
  const [trajectory, setTrajectory] = useState([]);
  const [ripples, setRipples] = useState([]);
  const [calibration, setCalibration] = useState({ state: "idle", progress: 0, baseline: null });
  const [error, setError] = useState(null);
  const [notice, setNotice] = useState(null);
  const [audioError, setAudioError] = useState(null);

  const spatialRef = useRef(null);
  const trajectoryRef = useRef([]);
  const lastTrajectoryPoint = useRef(null);

  const applyRoom = useCallback((layout) => {
    const normalized = normalizeRoom(layout);
    setRoom(normalized.layout);
    setRoomSource(normalized.source);
    setView((v) => (v === "landing" ? v : "live"));
  }, []);

  const flashNotice = useCallback((message) => {
    setNotice(message);
    window.setTimeout(() => setNotice(null), 3500);
  }, []);

  // -- websocket ------------------------------------------------------------

  const wsHandlers = useMemo(
    () => ({
      onConnect: () => {
        api.getStatus().then((s) => {
          if (s.room) applyRoom(s.room);
          setSensorMode(s.mode);
        }).catch(() => {});
      },
      spatial_update: (payload) => {
        spatialRef.current = payload;
        setSpatial(payload);

        const p = payload.position;
        const prev = lastTrajectoryPoint.current;
        if (!prev || Math.hypot(p.x - prev.x, p.z - prev.z) > 0.02) {
          lastTrajectoryPoint.current = p;
          trajectoryRef.current = [...trajectoryRef.current.slice(-(TRAJECTORY_MAX - 1)), p];
          setTrajectory(trajectoryRef.current);
        }

        // Spawn a ripple on strong motion events.
        if (payload.motion && payload.confidence > 0.3) {
          setRipples((existing) => {
            const now = existing
              .map((r) => ({ ...r, age: (Date.now() - r.born) / 1000 }))
              .filter((r) => r.age < 3.2);
            const next = [...now, { id: rippleId++, x: p.x, z: p.z, born: Date.now() }];
            return next.slice(-RIPPLE_MAX);
          });
        }
      },
      sensor_started: (data) => {
        setSensorMode(data.mode);
        flashNotice(data.mode === "demo" ? "Demo Mode active — synthetic data" : "Live acoustic sensing active");
      },
      sensor_stopped: () => {
        setSensorMode(null);
      },
      room_updated: (data) => applyRoom(data.layout),
      calibration_started: () => setCalibration({ state: "running", progress: 0, baseline: null }),
      calibration_progress: (data) =>
        setCalibration((c) => ({ ...c, state: "running", progress: data.progress })),
      calibration_complete: (data) =>
        setCalibration({ state: "done", progress: 1, baseline: data.baseline }),
      error: (data) => {
        setError(data.message || "An unknown error occurred.");
        if (data.suggestion === "demo") setAudioError(true);
      },
    }),
    [applyRoom, flashNotice]
  );

  const { status: wsStatus } = useWebSocket(wsHandlers);

  // -- initial load ---------------------------------------------------------

  useEffect(() => {
    let cancelled = false;
    api
      .getRoom()
      .then((layout) => {
        if (!cancelled) {
          const normalized = normalizeRoom(layout);
          setRoom(normalized.layout);
          setRoomSource(normalized.source);
        }
      })
      .catch(() => {});
    return () => {
      cancelled = true;
    };
  }, []);

  // -- actions --------------------------------------------------------------

  const analyzeRoom = useCallback(
    async (file) => {
      setError(null);
      setAnalyzing(true);
      setAnalyzeStage("Uploading room photo…");
      try {
        setAnalyzeStage("Contacting Groq Vision…");
        const layout = await api.analyzeRoomImage(file);
        setAnalyzeStage("Building digital twin…");
        await new Promise((r) => setTimeout(r, 350)); // let the UI breathe
        applyRoom(layout);
        flashNotice(layout.source === "ai" ? "AI room analysis complete" : "Using demo room (Groq unavailable)");
      } catch (err) {
        setError(err.message || "Room analysis failed.");
      } finally {
        setAnalyzing(false);
        setAnalyzeStage("");
      }
    },
    [applyRoom, flashNotice]
  );

  const useDemoRoom = useCallback(async () => {
    setError(null);
    try {
      const layout = await api.resetRoom();
      applyRoom(layout);
      flashNotice("Demo room loaded");
    } catch (err) {
      setError(err.message);
    }
  }, [applyRoom, flashNotice]);

  const startSensor = useCallback(
    async (mode) => {
      setError(null);
      setAudioError(null);
      try {
        const status = await api.startSensor(mode);
        setSensorMode(status.mode);
      } catch (err) {
        const msg = err.message || "Could not start the sensor.";
        setError(msg);
        if (mode === "real" && /microphone|audio|device|input/i.test(msg)) {
          setAudioError(true);
        }
      }
    },
    []
  );

  const stopSensor = useCallback(async () => {
    setError(null);
    try {
      await api.stopSensor();
      setSensorMode(null);
    } catch (err) {
      setError(err.message);
    }
  }, []);

  const calibrate = useCallback(async () => {
    setError(null);
    try {
      await api.calibrateSensor(3);
    } catch (err) {
      setError(err.message);
    }
  }, []);

  const clearTrajectory = useCallback(() => {
    trajectoryRef.current = [];
    lastTrajectoryPoint.current = null;
    setTrajectory([]);
  }, []);

  const removeRipple = useCallback((id) => {
    setRipples((existing) => existing.filter((r) => r.id !== id));
  }, []);

  const goToLive = useCallback(() => {
    setView("live");
    setError(null);
  }, []);

  const goToSetup = useCallback(() => {
    setView("setup");
    setError(null);
  }, []);

  return {
    view,
    goToLive,
    goToSetup,
    room,
    roomSource,
    analyzing,
    analyzeStage,
    analyzeRoom,
    useDemoRoom,
    sensorMode,
    startSensor,
    stopSensor,
    calibrate,
    calibration,
    spatial,
    trajectory,
    ripples,
    removeRipple,
    clearTrajectory,
    wsStatus,
    error,
    setError,
    notice,
    audioError,
    setAudioError,
  };
}

// ---------------------------------------------------------------------------
// Room layout normalisation (client side; mirrors backend validation)
// ---------------------------------------------------------------------------
const VALID_TYPES = new Set([
  "bed", "sofa", "table", "desk", "chair", "wardrobe", "cabinet", "door",
  "window", "television", "shelf", "plant", "lamp", "rug",
]);
const TYPE_ALIASES = { tv: "television" };

export function normalizeRoom(layout) {
  const room = layout?.room && typeof layout.room.width === "number"
    ? layout.room
    : { width: 6, depth: 5, height: 3 };
  const width = Math.min(Math.max(room.width, 2), 20);
  const depth = Math.min(Math.max(room.depth, 2), 20);
  const height = Math.min(Math.max(room.height, 2), 6);
  const dims = { width, depth, height };

  const objects = Array.isArray(layout?.objects) ? layout.objects : [];
  const cleaned = objects
    .map((o) => {
      const type = TYPE_ALIASES[o?.type] || o?.type;
      if (!type || !VALID_TYPES.has(type)) return null;
      return {
        name: o.name || type,
        type,
        x: clampNum(o.x, -width / 2, width / 2),
        y: clampNum(o.y, 0, height),
        z: clampNum(o.z, -depth / 2, depth / 2),
        width: clampNum(o.width, 0.1, Math.min(width * 0.6, 4)),
        depth: clampNum(o.depth, 0.1, Math.min(depth * 0.6, 4)),
        height: clampNum(o.height, 0.02, Math.min(height * 0.9, 3)),
        rotation: Number(o.rotation) || 0,
      };
    })
    .filter(Boolean)
    .slice(0, 24);

  return {
    layout: { room: dims, objects: cleaned, source: layout?.source || "demo" },
    source: layout?.source === "ai" ? "ai" : "demo",
  };
}

function clampNum(v, lo, hi) {
  const n = Number(v);
  if (!Number.isFinite(n)) return lo;
  return Math.min(Math.max(n, lo), hi);
}

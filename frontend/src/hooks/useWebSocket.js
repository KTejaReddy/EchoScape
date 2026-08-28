import { useEffect, useRef, useState } from "react";
import { io } from "socket.io-client";

/**
 * Connects to the EchoScape backend WebSocket with automatic reconnection.
 * Events are routed to the provided handlers. Returns connection status.
 */
export function useWebSocket(handlers = {}) {
  const [status, setStatus] = useState("connecting");
  const socketRef = useRef(null);
  const handlersRef = useRef(handlers);

  useEffect(() => {
    handlersRef.current = handlers;
  }, [handlers]);

  useEffect(() => {
    // Same-origin so the Vite proxy forwards /socket.io to the backend.
    const socket = io({
      path: "/socket.io",
      transports: ["websocket", "polling"],
      reconnection: true,
      reconnectionAttempts: Infinity,
      reconnectionDelay: 800,
      reconnectionDelayMax: 4000,
      timeout: 10000,
    });
    socketRef.current = socket;

    socket.on("connect", () => {
      setStatus("connected");
      handlersRef.current?.onConnect?.();
    });
    socket.on("disconnect", (reason) => {
      setStatus("disconnected");
      handlersRef.current?.onDisconnect?.(reason);
    });
    socket.on("connect_error", () => {
      setStatus("connecting");
    });

    const route = (name) =>
      socket.on(name, (data) => handlersRef.current?.[name]?.(data));

    route("spatial_update");
    route("sensor_started");
    route("sensor_stopped");
    route("room_updated");
    route("error");
    route("calibration_started");
    route("calibration_progress");
    route("calibration_complete");
    route("status");

    return () => {
      socket.disconnect();
      socketRef.current = null;
    };
  }, []);

  return { status, socket: socketRef.current };
}

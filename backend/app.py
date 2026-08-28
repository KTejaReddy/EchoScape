"""EchoScape backend - Flask + SocketIO application.

Owns the sensor lifecycle (real DSP pipeline OR demo simulator), streams
spatial updates to the React frontend over WebSocket, and exposes the REST API
for room analysis and sensor control.

Run:  python app.py   (from the backend/ directory)
"""
from __future__ import annotations

import base64
import os
import threading
import time
import uuid
from typing import Optional

from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_socketio import SocketIO

import config
from audio.generator import AudioDeviceError
from audio.processor import SensorPipeline
from audio.recorder import list_devices
from spatial.coordinate_mapper import fallback_layout
from streaming.demo import DemoSimulator
from streaming.producer import Producer
from utils.logging_config import configure_logging
from vision.groq_layout import VisionError, analyze_image

log = configure_logging(config.LOG_LEVEL)

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("ECHOSCAPE_SECRET", "echoscape-hackathon")
socketio = SocketIO(
    app,
    cors_allowed_origins=config.CORS_ORIGIN_LIST,
    async_mode="threading",
    ping_interval=20,
    ping_timeout=30,
    max_http_buffer_size=512 * 1024,
)
CORS(app, origins=config.CORS_ORIGIN_LIST)


# ---------------------------------------------------------------------------
# Sensor manager
# ---------------------------------------------------------------------------
class SensorManager:
    """Owns the producer queue, DSP pipeline, demo simulator and emitter thread."""

    def __init__(self) -> None:
        self.producer = Producer()
        self.room = fallback_layout()
        self.pipeline = SensorPipeline(self.producer, self.room)
        self.demo = DemoSimulator(self.producer, self.room, frame_rate=config.DEMO_FRAME_RATE, noise=config.DEMO_NOISE)

        self.mode: Optional[str] = None  # None | "real" | "demo"
        self._stop = threading.Event()
        self._emitter_thread: Optional[threading.Thread] = None
        self._demo_thread: Optional[threading.Thread] = None
        self._last_error: Optional[str] = None

    # -- lifecycle ----------------------------------------------------------

    def start_emitter(self) -> None:
        """Persistent thread: producer queue -> WebSocket emit."""
        if self._emitter_thread is not None and self._emitter_thread.is_alive():
            return
        self._stop.clear()
        self._emitter_thread = threading.Thread(target=self._emit_loop, name="echoscape-emitter", daemon=True)
        self._emitter_thread.start()

    def stop_emitter(self) -> None:
        self._stop.set()

    def _emit_loop(self) -> None:
        while not self._stop.is_set():
            payload = self.producer.get(timeout=0.1)
            if payload is not None:
                try:
                    socketio.emit("spatial_update", payload)
                except Exception as exc:  # noqa: BLE001
                    log.debug("Emit failed: %s", exc)

    # -- sensor control -----------------------------------------------------

    def start_sensor(self, mode: str) -> dict:
        """Start sensing in 'real' or 'demo' mode. Returns a status dict."""
        mode = (mode or "").lower()
        if mode not in ("real", "demo"):
            raise ValueError("mode must be 'real' or 'demo'")

        self.stop_sensor()
        self._last_error = None
        self.mode = mode

        if mode == "real":
            try:
                self.pipeline.start()
            except AudioDeviceError as exc:
                self.mode = None
                self._last_error = str(exc)
                socketio.emit("error", {"message": str(exc), "suggestion": "demo"})
                raise
            socketio.emit("sensor_started", {"mode": "real"})
        else:
            self.demo.reset()
            self._stop.clear()
            self._demo_thread = threading.Thread(target=self._demo_loop, name="echoscape-demo", daemon=True)
            self._demo_thread.start()
            socketio.emit("sensor_started", {"mode": "demo"})

        log.info("Sensor started in %s mode", mode)
        return self.status()

    def _demo_loop(self) -> None:
        interval = 1.0 / max(self.demo.frame_rate, 1.0)
        while not self._stop.is_set():
            try:
                self.demo.step()
            except Exception as exc:  # noqa: BLE001
                log.error("Demo loop error: %s", exc)
                self._last_error = str(exc)
            self._stop.wait(interval)

    def stop_sensor(self) -> dict:
        was = self.mode
        self._stop.set()
        self.pipeline.stop()
        if self._demo_thread is not None and self._demo_thread.is_alive():
            self._demo_thread.join(timeout=2.0)
        self._demo_thread = None
        if was is not None:
            socketio.emit("sensor_stopped", {"mode": was})
        self.mode = None
        return self.status()

    # -- calibration --------------------------------------------------------

    def calibrate(self, seconds: float = 3.0) -> None:
        """Run calibration on a background thread, streaming progress events."""
        if self.mode != "real":
            raise ValueError("Calibration requires Real Mode (Start Sensor first).")

        def _run() -> None:
            socketio.emit("calibration_started", {"seconds": seconds})
            try:
                baseline = self.pipeline.calibrate(
                    seconds=seconds,
                    on_progress=lambda p: socketio.emit(
                        "calibration_progress", {"progress": round(min(max(p, 0.0), 1.0), 3)}
                    ),
                )
                socketio.emit("calibration_complete", {"baseline": baseline})
            except Exception as exc:  # noqa: BLE001
                socketio.emit("error", {"message": f"Calibration failed: {exc}"})
                log.error("Calibration failed: %s", exc)

        threading.Thread(target=_run, name="echoscape-calibration", daemon=True).start()

    # -- room ---------------------------------------------------------------

    def set_room(self, layout: dict) -> None:
        self.room = layout
        self.pipeline.set_room(layout)
        self.demo.room = layout
        self.pipeline.estimator.reset(room=layout)

    # -- status -------------------------------------------------------------

    def status(self) -> dict:
        latest = self.producer.latest()
        return {
            "mode": self.mode,
            "running": self.mode is not None,
            "room": self.room,
            "room_source": self.room.get("source", "demo"),
            "latest": latest,
            "error": self._last_error,
            "devices": list_devices(),
            "audio": {
                "sample_rate": config.AUDIO_SAMPLE_RATE,
                "block_size": config.AUDIO_BLOCK_SIZE,
                "carrier_frequency": config.CARRIER_FREQUENCY,
                "amplitude": config.AUDIO_AMPLITUDE,
                "mic_distance": config.MIC_DISTANCE,
                "speed_of_sound": config.SPEED_OF_SOUND,
                "motion_threshold": config.MOTION_THRESHOLD,
            },
            "generator": self.pipeline.generator.describe(),
            "recorder": self.pipeline.recorder.describe(),
            "calibration": self.pipeline._calibration,  # noqa: SLF001 - prototype
        }


manager = SensorManager()


# ---------------------------------------------------------------------------
# Error helpers
# ---------------------------------------------------------------------------
def _friendly_error(message: str, status: int = 400) -> tuple:
    return jsonify({"error": message}), status


# ---------------------------------------------------------------------------
# REST API
# ---------------------------------------------------------------------------
@app.get("/api/health")
def api_health():
    return jsonify(
        {
            "status": "ok",
            "service": "echoscape-backend",
            "groq_configured": bool(config.GROQ_API_KEY.strip()),
            "vision_model": config.GROQ_VISION_MODEL,
            "time": time.time(),
        }
    )


@app.post("/api/analyze-room")
def api_analyze_room():
    """Analyse a room photo via Groq Vision. Accepts multipart 'image' or JSON."""
    image_bytes: Optional[bytes] = None
    mime = "image/jpeg"

    if request.files and "image" in request.files:
        f = request.files["image"]
        image_bytes = f.read()
        mime = f.mimetype or mime
    elif request.is_json:
        data = request.get_json(silent=True) or {}
        b64 = data.get("image_base64") or data.get("image")
        if b64:
            try:
                image_bytes = base64.b64decode(b64)
            except (ValueError, TypeError):
                return _friendly_error("The uploaded image data was not valid base64.")
            mime = data.get("mime", mime)

    if not image_bytes:
        return _friendly_error("No image provided. Upload a room photo first.")
    if len(image_bytes) > config.MAX_IMAGE_BYTES:
        return _friendly_error("Image is too large (max 10 MB).")
    if len(image_bytes) < 60:
        return _friendly_error("That image looks empty or corrupt.")

    # Persist only while analysing, then clean up immediately.
    os.makedirs(config.UPLOAD_DIR, exist_ok=True)
    tmp_path = os.path.join(config.UPLOAD_DIR, f"room_{uuid.uuid4().hex}.img")
    try:
        with open(tmp_path, "wb") as fh:
            fh.write(image_bytes)

        try:
            layout = analyze_image(image_bytes, mime)
        except VisionError as exc:
            log.warning("Vision analysis failed, falling back to demo room: %s", exc)
            layout = fallback_layout()
            layout["note"] = str(exc)
    finally:
        try:
            os.remove(tmp_path)
        except OSError:
            pass

    manager.set_room(layout)
    socketio.emit("room_updated", {"layout": layout, "source": layout.get("source", "demo")})
    return jsonify(layout)


@app.post("/api/room/reset")
def api_room_reset():
    layout = fallback_layout()
    manager.set_room(layout)
    socketio.emit("room_updated", {"layout": layout, "source": "demo"})
    return jsonify(layout)


@app.post("/api/sensor/start")
def api_sensor_start():
    body = request.get_json(silent=True) or {}
    mode = body.get("mode", "real")
    try:
        return jsonify(manager.start_sensor(mode))
    except ValueError as exc:
        return _friendly_error(str(exc))
    except AudioDeviceError as exc:
        return _friendly_error(
            f"{exc}\n\nYou can: select another device, enable Demo Mode, "
            "or check OS microphone permissions.",
            status=400,
        )


@app.post("/api/sensor/stop")
def api_sensor_stop():
    return jsonify(manager.stop_sensor())


@app.post("/api/sensor/calibrate")
def api_sensor_calibrate():
    body = request.get_json(silent=True) or {}
    try:
        seconds = min(max(float(body.get("seconds", 3.0)), 1.0), 10.0)
        manager.calibrate(seconds)
        return jsonify({"status": "calibrating", "seconds": seconds})
    except ValueError as exc:
        return _friendly_error(str(exc))


@app.get("/api/sensor/status")
def api_sensor_status():
    return jsonify(manager.status())


@app.get("/api/devices")
def api_devices():
    return jsonify({"devices": list_devices()})


@app.get("/api/room")
def api_room():
    return jsonify(manager.room)


# ---------------------------------------------------------------------------
# SocketIO event handlers
# ---------------------------------------------------------------------------
@socketio.on("connect")
def on_connect():
    log.info("Client connected: %s", request.sid)
    socketio.emit("status", manager.status(), to=request.sid)


@socketio.on("disconnect")
def on_disconnect():
    log.info("Client disconnected: %s", request.sid)


@socketio.on("ping")
def on_ping(_data=None):
    socketio.emit("pong", {"time": time.time()}, to=request.sid)


@socketio.on("sensor:start")
def on_sensor_start(data=None):
    try:
        mode = (data or {}).get("mode", "real")
        manager.start_sensor(mode)
    except (ValueError, AudioDeviceError) as exc:
        socketio.emit("error", {"message": str(exc)}, to=request.sid)


@socketio.on("sensor:stop")
def on_sensor_stop(_data=None):
    manager.stop_sensor()


@socketio.on("sensor:calibrate")
def on_sensor_calibrate(_data=None):
    try:
        manager.calibrate()
    except ValueError as exc:
        socketio.emit("error", {"message": str(exc)}, to=request.sid)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def main() -> None:
    manager.start_emitter()
    log.info("EchoScape backend listening on http://%s:%s", config.HOST, config.PORT)
    try:
        socketio.run(app, host=config.HOST, port=config.PORT, debug=config.DEBUG, allow_unsafe_werkzeug=True)
    except KeyboardInterrupt:
        pass
    finally:
        manager.stop_emitter()
        manager.stop_sensor()
        log.info("EchoScape backend shut down")


if __name__ == "__main__":
    main()

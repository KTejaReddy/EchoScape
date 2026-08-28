"""Thread-safe producer queue + payload builder.

Audio capture and DSP run on worker threads; the resulting estimates are
published into a `Producer`. A single consumer thread in the Flask app drains
the queue and emits each payload over WebSocket. This keeps heavy DSP work out
of the request/emit path.
"""
from __future__ import annotations

import queue
import time
from typing import Any, Optional


class Producer:
    def __init__(self, maxsize: int = 100) -> None:
        self._queue: "queue.Queue[dict]" = queue.Queue(maxsize=maxsize)
        self._latest: Optional[dict] = None

    def publish(self, payload: dict) -> None:
        """Add a payload to the queue (drop-oldest if full)."""
        self._latest = payload
        if self._queue.full():
            try:
                self._queue.get_nowait()
            except queue.Empty:
                pass
        try:
            self._queue.put_nowait(payload)
        except queue.Full:
            pass

    def get(self, timeout: float = 0.1) -> Optional[dict]:
        """Return the next payload or None on timeout."""
        try:
            return self._queue.get(timeout=timeout)
        except queue.Empty:
            return None

    def latest(self) -> Optional[dict]:
        return self._latest

    def clear(self) -> None:
        while True:
            try:
                self._queue.get_nowait()
            except queue.Empty:
                return
        self._latest = None

    @property
    def qsize(self) -> int:
        return self._queue.qsize()


def build_payload(
    *,
    position: dict,
    motion: bool,
    confidence: float,
    speed: float,
    bearing: float,
    bearing_label: str,
    frequency: float,
    frequency_shift: float,
    signal_strength: float,
    mode: str,
    motion_score: float = 0.0,
    spectral_energy: float = 0.0,
    azimuth: float = 0.0,
    tdoa_confidence: float = 0.0,
) -> dict:
    """Build the wire payload streamed to the frontend."""
    return {
        "type": "spatial_update",
        "timestamp": round(time.time(), 3),
        "position": {
            "x": round(float(position.get("x", 0.0)), 3),
            "y": round(float(position.get("y", 0.0)), 3),
            "z": round(float(position.get("z", 0.0)), 3),
        },
        "motion": bool(motion),
        "confidence": round(float(confidence), 4),
        "speed": round(float(speed), 4),
        "direction": round(float(bearing), 1),
        "direction_label": bearing_label,
        "frequency": round(float(frequency), 2),
        "frequency_shift": round(float(frequency_shift), 2),
        "signal_strength": round(float(signal_strength), 4),
        "motion_score": round(float(motion_score), 4),
        "spectral_energy": round(float(spectral_energy), 2),
        "azimuth": round(float(azimuth), 1),
        "tdoa_confidence": round(float(tdoa_confidence), 4),
        "mode": mode,
    }

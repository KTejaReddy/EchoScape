"""Acoustic signal generation.

Plays a quiet high-frequency probe tone (or chirp) through the laptop speaker so
the microphones can observe room reflections. Everything is configurable and
defaults are deliberately conservative (low amplitude, high frequency).
"""
from __future__ import annotations

import logging
import math
import threading
import time
from typing import Optional

import numpy as np
import sounddevice as sd

log = logging.getLogger("echoscape.audio.generator")


class AudioDeviceError(Exception):
    """Raised when a requested audio device is unavailable or misconfigured."""


class SignalGenerator:
    """Generates a continuous sine / chirp tone on a background thread-safe stream."""

    def __init__(
        self,
        sample_rate: int,
        frequency: float,
        amplitude: float,
        use_chirp: bool = False,
        chirp_rate: float = 400.0,
        device: Optional[str] = None,
    ) -> None:
        self.sample_rate = int(sample_rate)
        self.frequency = float(frequency)
        self.amplitude = max(0.0, min(float(amplitude), 0.5))
        self.use_chirp = bool(use_chirp)
        self.chirp_rate = float(chirp_rate)
        self.device = device or None

        self._stream: Optional[sd.OutputStream] = None
        self._phase = 0.0
        self._lock = threading.Lock()

    # -- lifecycle ----------------------------------------------------------

    def start(self) -> None:
        """Open the output stream and begin generating the tone."""
        if self._stream is not None:
            return

        # Fail early with a friendly error instead of crashing the app.
        try:
            sd.query_devices(self.device, "output")
        except (ValueError, sd.PortAudioError) as exc:  # type: ignore[attr-defined]
            raise AudioDeviceError(
                f"Speaker unavailable: {exc}"
            ) from exc

        try:
            self._stream = sd.OutputStream(
                samplerate=self.sample_rate,
                blocksize=1024,
                device=self.device,
                channels=1,
                dtype="float32",
                callback=self._callback,
            )
            self._stream.start()
        except (sd.PortAudioError, ValueError) as exc:  # type: ignore[attr-defined]
            self._stream = None
            raise AudioDeviceError(
                f"Could not open speaker output: {exc}"
            ) from exc
        log.info("Signal generator started (%.0f Hz, amp %.2f)", self.frequency, self.amplitude)

    def stop(self) -> None:
        """Close the output stream."""
        with self._lock:
            stream, self._stream = self._stream, None
        if stream is not None:
            try:
                stream.stop()
            except Exception:  # noqa: BLE001 - cleanup must never raise
                pass
            try:
                stream.close()
            except Exception:  # noqa: BLE001
                pass
        log.info("Signal generator stopped")

    @property
    def running(self) -> bool:
        return self._stream is not None

    # -- internals ----------------------------------------------------------

    def _callback(self, outdata: np.ndarray, frames: int, time_info, status) -> None:  # type: ignore[no-untyped-def]
        """Fill the output buffer with the probe waveform."""
        if status:
            log.debug("Output stream status: %s", status)

        t = np.arange(frames, dtype=np.float32) / self.sample_rate
        if self.use_chirp:
            # Linear chirp around the carrier: f(t) = f0 + chirp_rate * t
            phase = self._phase + 2.0 * math.pi * (
                self.frequency * t + 0.5 * self.chirp_rate * t * t
            )
            wave = np.sin(phase).astype(np.float32)
            self._phase = phase[-1]
        else:
            phase = self._phase + 2.0 * math.pi * self.frequency * t
            wave = np.sin(phase).astype(np.float32)
            self._phase = phase[-1]

        outdata[:, 0] = wave * self.amplitude

    def describe(self) -> dict:
        return {
            "sample_rate": self.sample_rate,
            "frequency": self.frequency,
            "amplitude": self.amplitude,
            "use_chirp": self.use_chirp,
            "chirp_rate": self.chirp_rate,
            "device": self.device,
            "running": self.running,
        }

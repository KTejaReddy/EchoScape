"""Microphone capture.

Captures stereo blocks with `sounddevice` and pushes them into a bounded queue.
Mono devices are handled by duplicating the single channel. All device errors
are converted into friendly `AudioDeviceError`s so the rest of the app can
fall back to Demo Mode instead of crashing.
"""
from __future__ import annotations

import logging
import queue
import threading
from typing import Optional

import numpy as np
import sounddevice as sd

from audio.generator import AudioDeviceError

log = logging.getLogger("echoscape.audio.recorder")


def list_devices() -> list[dict]:
    """Return a safe summary of available audio devices for the UI."""
    devices = []
    try:
        for idx, info in enumerate(sd.query_devices()):
            devices.append(
                {
                    "index": idx,
                    "name": str(info.get("name", "Unknown")),
                    "max_input_channels": int(info.get("max_input_channels", 0)),
                    "max_output_channels": int(info.get("max_output_channels", 0)),
                    "default_samplerate": float(info.get("default_samplerate", 0) or 0),
                }
            )
    except Exception as exc:  # noqa: BLE001 - never crash on enumeration
        log.warning("Could not enumerate audio devices: %s", exc)
    return devices


class AudioRecorder:
    """Captures stereo (or mono) microphone blocks into a bounded queue."""

    def __init__(
        self,
        sample_rate: int,
        block_size: int,
        channels: int = 2,
        device: Optional[str] = None,
        max_queue: int = 12,
    ) -> None:
        self.sample_rate = int(sample_rate)
        self.block_size = int(block_size)
        self.channels = max(1, int(channels))
        self.device = device or None
        self._queue: "queue.Queue[np.ndarray]" = queue.Queue(maxsize=max_queue)
        self._stream: Optional[sd.InputStream] = None
        self._lock = threading.Lock()

    # -- lifecycle ----------------------------------------------------------

    def start(self) -> None:
        """Open the input stream. Raises AudioDeviceError on any problem."""
        if self._stream is not None:
            return

        # Resolve the actual device so we can detect mono mics up front.
        try:
            info = sd.query_devices(self.device, "input")
        except (ValueError, sd.PortAudioError) as exc:  # type: ignore[attr-defined]
            raise AudioDeviceError(f"Microphone unavailable: {exc}") from exc

        max_ch = int(info.get("max_input_channels", 0) or 0)
        effective_channels = min(self.channels, max_ch) if max_ch > 0 else self.channels
        if effective_channels < 1:
            raise AudioDeviceError("Selected microphone has no input channels.")

        try:
            self._stream = sd.InputStream(
                samplerate=self.sample_rate,
                blocksize=self.block_size,
                device=self.device,
                channels=effective_channels,
                dtype="float32",
                callback=self._callback,
            )
            self._stream.start()
        except (sd.PortAudioError, ValueError) as exc:  # type: ignore[attr-defined]
            self._stream = None
            raise AudioDeviceError(f"Could not open microphone input: {exc}") from exc

        self._actual_channels = effective_channels
        log.info(
            "Recorder started: %d Hz, block %d, channels %d (device: %s)",
            self.sample_rate,
            self.block_size,
            effective_channels,
            info.get("name", "default"),
        )

    def stop(self) -> None:
        """Close the input stream."""
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
        log.info("Recorder stopped")

    @property
    def running(self) -> bool:
        return self._stream is not None

    # -- data access --------------------------------------------------------

    def next_block(self, timeout: float = 0.2) -> Optional[np.ndarray]:
        """Return the next audio block or None on timeout."""
        try:
            return self._queue.get(timeout=timeout)
        except queue.Empty:
            return None

    def drain(self) -> None:
        """Drop any queued audio (used before calibration / start)."""
        while True:
            try:
                self._queue.get_nowait()
            except queue.Empty:
                return

    # -- internals ----------------------------------------------------------

    def _callback(self, indata: np.ndarray, frames: int, time_info, status) -> None:  # type: ignore[no-untyped-def]
        if status:
            log.debug("Input stream status: %s", status)
        block = np.array(indata, dtype=np.float32, copy=True)

        # Normalise to a fixed 2-channel layout: mono -> duplicate, >2 -> take L/R.
        if block.ndim == 1 or block.shape[1] == 1:
            block = np.repeat(block, 2, axis=1)
        elif block.shape[1] > 2:
            block = block[:, :2]

        if self._queue.full():
            try:
                self._queue.get_nowait()  # drop oldest, keep it real-time
            except queue.Empty:
                pass
        try:
            self._queue.put_nowait(block)
        except queue.Full:
            pass  # extremely unlikely after the drop above

    def describe(self) -> dict:
        return {
            "sample_rate": self.sample_rate,
            "block_size": self.block_size,
            "channels": getattr(self, "_actual_channels", self.channels),
            "device": self.device,
            "running": self.running,
        }

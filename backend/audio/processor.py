"""Real-sensor processing pipeline.

Runs on a background worker thread:

    audio block (recorder queue)
        -> FFT features (left+right)
        -> TDOA azimuth
        -> motion detection
        -> spatial estimator
        -> producer queue -> WebSocket

The pipeline owns the SignalGenerator (probe tone) and AudioRecorder and is
started/stopped cleanly with a threading.Event.
"""
from __future__ import annotations

import logging
import threading
import time
from typing import Optional

import numpy as np

from audio.fft_detector import FFTDetector
from audio.generator import AudioDeviceError, SignalGenerator
from audio.motion_detector import MotionDetector
from audio.recorder import AudioRecorder
from audio.tdoa import estimate_angle
from config import (
    AUDIO_AMPLITUDE,
    AUDIO_BLOCK_SIZE,
    AUDIO_CHANNELS,
    AUDIO_DEVICE,
    AUDIO_GENERATE,
    AUDIO_SAMPLE_RATE,
    AUDIO_STREAM_RATE,
    AUDIO_USE_CHIRP,
    AUDIO_CHIRP_RATE,
    CARRIER_FREQUENCY,
    MIC_DISTANCE,
    MOTION_SMOOTHING,
    MOTION_THRESHOLD,
    POSITION_SMOOTHING,
    SPEED_OF_SOUND,
    TDOA_SMOOTHING,
)
from spatial.estimator import SpatialEstimator
from streaming.producer import Producer, build_payload

log = logging.getLogger("echoscape.audio.processor")


class SensorPipeline:
    """Owns the audio devices and runs the DSP loop on a worker thread."""

    def __init__(self, producer: Producer, room: dict) -> None:
        self.producer = producer
        self.room = room

        self.generator = SignalGenerator(
            sample_rate=AUDIO_SAMPLE_RATE,
            frequency=CARRIER_FREQUENCY,
            amplitude=AUDIO_AMPLITUDE,
            use_chirp=AUDIO_USE_CHIRP,
            chirp_rate=AUDIO_CHIRP_RATE,
            device=AUDIO_DEVICE or None,
        )
        self.recorder = AudioRecorder(
            sample_rate=AUDIO_SAMPLE_RATE,
            block_size=AUDIO_BLOCK_SIZE,
            channels=AUDIO_CHANNELS,
            device=AUDIO_DEVICE or None,
        )
        self.fft = FFTDetector(target_frequency=CARRIER_FREQUENCY)
        self.motion = MotionDetector(threshold=MOTION_THRESHOLD, smoothing=MOTION_SMOOTHING)
        self.estimator = SpatialEstimator(room=room, smoothing=TDOA_SMOOTHING, position_smoothing=POSITION_SMOOTHING)

        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        self._error: Optional[str] = None
        self._calibration: Optional[dict] = None

    # -- lifecycle ----------------------------------------------------------

    def start(self) -> None:
        """Open audio devices and start the worker loop. Raises AudioDeviceError."""
        with self._lock:
            if self._thread is not None and self._thread.is_alive():
                return

            # Start devices first; any failure aborts cleanly.
            self.recorder.start()
            try:
                if AUDIO_GENERATE:
                    self.generator.start()
            except AudioDeviceError:
                # Microphone is the critical path; a missing speaker is tolerable.
                log.warning("Speaker unavailable - running receive-only (no probe tone).")

            self._stop_event.clear()
            self._error = None
            self.estimator.reset(room=self.room)
            self.fft.reset()
            self.motion.reset()
            self.recorder.drain()

            self._thread = threading.Thread(
                target=self._run, name="echoscape-dsp", daemon=True
            )
            self._thread.start()
            log.info("Sensor pipeline started (real mode)")

    def stop(self) -> None:
        """Stop the worker thread and close audio devices."""
        with self._lock:
            self._stop_event.set()
            thread, self._thread = self._thread, None
        if thread is not None and thread.is_alive():
            thread.join(timeout=2.0)
        self.generator.stop()
        self.recorder.stop()
        log.info("Sensor pipeline stopped")

    @property
    def running(self) -> bool:
        thread = self._thread
        return thread is not None and thread.is_alive()

    def get_error(self) -> Optional[str]:
        return self._error

    def set_room(self, room: dict) -> None:
        self.room = room
        self.estimator.reset(room=room)

    # -- calibration --------------------------------------------------------

    def calibrate(self, seconds: float = 3.0, on_progress=None) -> dict:
        """Measure the acoustic baseline: noise floor and target-band magnitude."""
        log.info("Calibration started (%.1f s)", seconds)
        # Make sure the devices are alive (started by start()).
        samples: list[np.ndarray] = []
        step = 0.2
        waited = 0.0
        start = time.monotonic()
        deadline = start + seconds
        while time.monotonic() < deadline and not self._stop_event.is_set():
            block = self.recorder.next_block(timeout=step)
            if block is not None:
                samples.append(block[:, 0])
            waited += step
            if on_progress is not None:
                on_progress(min(waited / seconds, 1.0))
            if not self.recorder.running:
                break

        if not samples:
            raise AudioDeviceError("No microphone data received during calibration.")

        audio = np.concatenate(samples)
        fft = FFTDetector(target_frequency=CARRIER_FREQUENCY)
        features = fft.analyze(audio, AUDIO_SAMPLE_RATE)

        baseline = {
            "noise_floor": round(features["noise_floor"], 6),
            "signal_strength": round(features["signal_strength"], 4),
            "spectral_energy": round(features["spectral_energy"], 2),
            "dominant_frequency": round(features["dominant_frequency"], 2),
            "seconds": round(time.monotonic() - start, 1),
        }
        self._calibration = baseline
        log.info("Calibration complete: %s", baseline)
        return baseline

    # -- worker loop --------------------------------------------------------

    def _run(self) -> None:
        interval = 1.0 / max(AUDIO_STREAM_RATE, 1)
        while not self._stop_event.is_set():
            t0 = time.monotonic()
            try:
                self._process_one_block()
            except Exception as exc:  # noqa: BLE001 - keep the loop alive
                log.error("DSP worker error: %s", exc)
                self._error = str(exc)

            elapsed = time.monotonic() - t0
            sleep = interval - elapsed
            if sleep > 0:
                self._stop_event.wait(sleep)

    def _process_one_block(self) -> None:
        block = self.recorder.next_block(timeout=0.05)
        if block is None:
            return

        left = block[:, 0]
        right = block[:, 1] if block.shape[1] > 1 else left

        # FFT features for both channels, averaged where it makes sense.
        fl = self.fft.analyze(left, AUDIO_SAMPLE_RATE)
        fr = self.fft.analyze(right, AUDIO_SAMPLE_RATE)
        freq = (fl["dominant_frequency"] + fr["dominant_frequency"]) / 2.0
        deviation = (fl["frequency_deviation"] + fr["frequency_deviation"]) / 2.0
        signal_strength = max(fl["signal_strength"], fr["signal_strength"])
        energy = max(fl["spectral_energy"], fr["spectral_energy"])
        fft_motion = max(fl["motion_score"], fr["motion_score"])

        # TDOA azimuth from the stereo pair.
        tdoa = estimate_angle(
            left, right,
            sample_rate=AUDIO_SAMPLE_RATE,
            mic_distance=MIC_DISTANCE,
            speed_of_sound=SPEED_OF_SOUND,
        )

        noise_floor = self._calibration["noise_floor"] if self._calibration else None
        motion = self.motion.update(
            fft_motion=fft_motion,
            frequency_deviation=deviation,
            signal_strength=signal_strength,
            tdoa_confidence=tdoa["confidence"],
            calibration_noise_floor=noise_floor,
        )

        state = self.estimator.update(
            motion_detected=motion["motion_detected"],
            confidence=motion["confidence"],
            azimuth_deg=tdoa["angle_deg"],
            dt=1.0 / AUDIO_STREAM_RATE,
        )

        payload = build_payload(
            position={"x": state["x"], "y": state["y"], "z": state["z"]},
            motion=motion["motion_detected"],
            confidence=motion["confidence"],
            speed=state["speed"],
            bearing=state["bearing"],
            bearing_label=state["bearing_label"],
            frequency=freq,
            frequency_shift=deviation,
            signal_strength=motion["signal_strength"],
            mode="real",
            motion_score=motion["motion_score"],
            spectral_energy=energy,
            azimuth=state["azimuth"],
            tdoa_confidence=tdoa["confidence"],
        )
        self.producer.publish(payload)

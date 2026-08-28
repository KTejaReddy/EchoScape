"""Practical motion detection.

Combines the FFT motion score, frequency deviation and TDOA confidence into a
single smoothed 0..1 confidence value, then applies a threshold to decide
IDLE vs MOTION. No human recognition is attempted - the goal is simply:

    no significant acoustic change  -> IDLE
    significant acoustic change     -> MOTION
"""
from __future__ import annotations

import logging
from typing import Optional

log = logging.getLogger("echoscape.audio.motion")


class MotionDetector:
    def __init__(
        self,
        threshold: float = 0.35,
        smoothing: float = 0.4,
        signal_alpha: float = 0.3,
    ) -> None:
        self.threshold = float(threshold)
        self.smoothing = float(smoothing)
        self._smoothed: Optional[float] = None
        self._signal_alpha = float(signal_alpha)
        self._signal_strength: Optional[float] = None

    def update(
        self,
        fft_motion: float,
        frequency_deviation: float,
        signal_strength: float,
        tdoa_confidence: float = 0.0,
        calibration_noise_floor: Optional[float] = None,
    ) -> dict:
        """Update smoothed state and return motion info.

        `calibration_noise_floor` is an optional per-block noise floor measured
        during calibration; when the current noise floor is far above it the
        environment is probably too loud for reliable sensing.
        """
        # A strong, moving reflection usually correlates across mics too.
        directional = tdoa_confidence

        raw = 0.6 * fft_motion + 0.25 * abs(frequency_deviation) / 150.0 + 0.15 * directional
        raw = min(max(raw, 0.0), 1.0)

        if self._smoothed is None:
            self._smoothed = raw
        else:
            self._smoothed = self.smoothing * raw + (1.0 - self.smoothing) * self._smoothed

        if self._signal_strength is None:
            self._signal_strength = signal_strength
        else:
            self._signal_strength = (
                self._signal_alpha * signal_strength
                + (1.0 - self._signal_alpha) * self._signal_strength
            )

        confidence = float(self._smoothed)
        motion_detected = confidence >= self.threshold
        return {
            "motion_detected": bool(motion_detected),
            "confidence": round(confidence, 4),
            "motion_score": round(raw, 4),
            "signal_strength": round(float(self._signal_strength), 4),
        }

    def reset(self) -> None:
        self._smoothed = None
        self._signal_strength = None

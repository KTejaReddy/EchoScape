"""Simplified stereo TDOA (Time Difference of Arrival) estimation.

Cross-correlates the left and right microphone channels to estimate the
inter-channel delay, then converts that delay into an azimuth angle using the
microphone spacing and the speed of sound:

    delay = argmax( L(t) * R(t - tau) )
    angle = asin( delay * speed_of_sound / mic_distance )

This is a prototype-grade estimator: it gives a *direction*, not
centimetre-level accuracy. Values are clamped to physically plausible ranges so
a noisy block can never produce a wild angle.
"""
from __future__ import annotations

import logging

import numpy as np
from scipy import signal as scipy_signal

log = logging.getLogger("echoscape.audio.tdoa")

MAX_ANGLE_DEG = 55.0  # clamp to avoid asin singularities / false wide angles


def estimate_angle(
    left: np.ndarray,
    right: np.ndarray,
    sample_rate: int,
    mic_distance: float = 0.15,
    speed_of_sound: float = 343.0,
) -> dict:
    """Return {'angle_deg', 'delay_seconds', 'correlation_peak', 'confidence'}.

    angle_deg: azimuth in degrees, 0 = straight ahead, positive = right.
    """
    n = int(min(left.size, right.size))
    if n < 16:
        return _neutral_angle()

    l = np.asarray(left[:n], dtype=np.float32)
    r = np.asarray(right[:n], dtype=np.float32)

    # Physically plausible max delay (seconds) given the geometry.
    max_delay_s = mic_distance / max(speed_of_sound, 1.0)
    max_lag = max(1, int(round(max_delay_s * sample_rate)))
    if max_lag >= n:
        max_lag = max(1, n // 4)

    # Cross-correlation (full, so negative lags are included).
    corr = scipy_signal.correlate(l, r, mode="full", method="fft")
    center = n - 1  # index of lag 0

    lo = max(0, center - max_lag)
    hi = min(corr.size, center + max_lag + 1)
    window = corr[lo:hi]
    if window.size == 0:
        return _neutral_angle()

    peak_idx = int(np.argmax(np.abs(window)))
    peak_value = float(window[peak_idx])
    lag_samples = (lo + peak_idx) - center

    # Normalise the peak so it is comparable across blocks (scale-free).
    energy = float(np.sqrt(np.dot(l, l) * np.dot(r, r)) + 1e-12)
    corr_peak_norm = abs(peak_value) / energy

    # Effectively no signal -> no direction information at all.
    if corr_peak_norm < 0.05:
        return _neutral_angle()

    delay_s = lag_samples / float(sample_rate)

    # Convert delay to angle, clamped to a physically plausible range.
    ratio = np.clip(delay_s * speed_of_sound / max(mic_distance, 1e-6), -1.0, 1.0)
    angle_deg = float(np.degrees(np.arcsin(ratio)))
    angle_deg = float(np.clip(angle_deg, -MAX_ANGLE_DEG, MAX_ANGLE_DEG))

    # Direction confidence: strong, well-defined correlation peak wins.
    confidence = float(np.clip((corr_peak_norm - 0.25) / 0.55, 0.0, 1.0))

    return {
        "angle_deg": angle_deg,
        "delay_seconds": delay_s,
        "correlation_peak": corr_peak_norm,
        "confidence": confidence,
    }


def _neutral_angle() -> dict:
    return {
        "angle_deg": 0.0,
        "delay_seconds": 0.0,
        "correlation_peak": 0.0,
        "confidence": 0.0,
    }

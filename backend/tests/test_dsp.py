"""DSP unit tests: FFT detection, TDOA, motion detection, spatial estimation."""
from __future__ import annotations

import math

import numpy as np
import pytest

from audio.fft_detector import FFTDetector
from audio.motion_detector import MotionDetector
from audio.tdoa import estimate_angle
from spatial.estimator import SpatialEstimator

SR = 48000


def _tone(freq: float, seconds: float = 0.1, amplitude: float = 0.5) -> np.ndarray:
    n = int(SR * seconds)
    t = np.arange(n) / SR
    return (amplitude * np.sin(2 * np.pi * freq * t)).astype(np.float32)


# ---------------------------------------------------------------------------
# FFT detection
# ---------------------------------------------------------------------------
def test_fft_finds_dominant_frequency():
    det = FFTDetector(target_frequency=19000.0)
    block = _tone(19000.0)
    feats = det.analyze(block, SR)
    assert feats["dominant_frequency"] == pytest.approx(19000.0, abs=30.0)
    assert feats["signal_strength"] > 0.5


def test_fft_detects_frequency_shift():
    det = FFTDetector(target_frequency=19000.0)
    block = _tone(19100.0)
    feats = det.analyze(block, SR)
    assert feats["frequency_deviation"] == pytest.approx(100.0, abs=30.0)


def test_fft_silence_gives_low_motion():
    det = FFTDetector(target_frequency=19000.0)
    block = np.zeros(SR // 10, dtype=np.float32)
    feats = det.analyze(block, SR)
    assert feats["motion_score"] < 0.05
    assert feats["signal_strength"] < 0.2


def test_fft_reset_clears_baselines():
    det = FFTDetector(target_frequency=19000.0)
    det.analyze(_tone(19000.0), SR)
    det.reset()
    assert det._mag_baseline is None  # noqa: SLF001


# ---------------------------------------------------------------------------
# TDOA
# ---------------------------------------------------------------------------
def test_tdoa_detects_delay_direction():
    # A signal arriving at the right mic ~0.1 ms later (left leads) means the
    # source is to the right -> positive angle.
    tone = _tone(19000.0, seconds=0.05)
    delay_samples = int(0.0001 * SR)  # 0.1 ms
    left = tone
    right = np.concatenate([np.zeros(delay_samples), tone[: len(tone) - delay_samples]])

    result = estimate_angle(left, right, SR, mic_distance=0.15, speed_of_sound=343.0)
    # delay = t_left - t_right < 0 => source on the left => angle negative
    assert result["angle_deg"] < -1.0
    assert result["confidence"] > 0.5


def test_tdoa_angles_are_clamped():
    # An absurd delay must not produce an impossible angle.
    tone = _tone(19000.0, seconds=0.05)
    big = int(0.02 * SR)
    left = tone
    right = np.concatenate([np.zeros(big), tone[: len(tone) - big]])
    result = estimate_angle(left, right, SR, mic_distance=0.15, speed_of_sound=343.0)
    assert abs(result["angle_deg"]) <= 55.0


def test_tdoa_silence_is_neutral():
    result = estimate_angle(np.zeros(2048, dtype=np.float32), np.zeros(2048, dtype=np.float32), SR)
    assert result["angle_deg"] == 0.0
    assert result["confidence"] == 0.0


# ---------------------------------------------------------------------------
# Motion detection
# ---------------------------------------------------------------------------
def test_motion_detector_threshold():
    det = MotionDetector(threshold=0.5, smoothing=1.0)  # no smoothing for direct test
    out = det.update(fft_motion=0.9, frequency_deviation=50.0, signal_strength=0.8)
    assert out["motion_detected"] is True
    assert 0.5 < out["confidence"] <= 1.0

    det2 = MotionDetector(threshold=0.5, smoothing=1.0)
    out2 = det2.update(fft_motion=0.0, frequency_deviation=0.0, signal_strength=0.1)
    assert out2["motion_detected"] is False


def test_motion_detector_smoothing():
    det = MotionDetector(threshold=0.5, smoothing=0.4)
    det.update(fft_motion=0.0, frequency_deviation=0.0, signal_strength=0.1)
    spike = det.update(fft_motion=1.0, frequency_deviation=100.0, signal_strength=0.9)
    # Smoothed value must be strictly between 0 and the raw 1.0.
    assert 0.0 < spike["confidence"] < 1.0


# ---------------------------------------------------------------------------
# Spatial estimation
# ---------------------------------------------------------------------------
def test_estimator_moves_along_azimuth():
    room = {"width": 6.0, "depth": 5.0, "height": 3.0}
    est = SpatialEstimator(room, smoothing=1.0, position_smoothing=1.0)
    # azimuth 90 deg = to the right (+x)
    for _ in range(20):
        state = est.update(motion_detected=True, confidence=0.9, azimuth_deg=90.0, dt=0.05)
    # 20 frames @ 0.05 s = 1 s of walking at ~0.99 m/s.
    assert state["x"] > 0.8
    assert abs(state["z"]) < 0.3


def test_estimator_does_not_teleport():
    room = {"width": 6.0, "depth": 5.0, "height": 3.0}
    est = SpatialEstimator(room, smoothing=1.0, position_smoothing=0.2)
    est.update(motion_detected=True, confidence=1.0, azimuth_deg=90.0, dt=0.05)
    state = est.update(motion_detected=True, confidence=1.0, azimuth_deg=90.0, dt=0.05)
    assert state["x"] < 0.3  # heavily smoothed, moves slowly


def test_estimator_idle_decays_confidence():
    room = {"width": 6.0, "depth": 5.0, "height": 3.0}
    est = SpatialEstimator(room, smoothing=1.0, position_smoothing=1.0, idle_hold=0.05, idle_decay=0.5)
    est.update(motion_detected=True, confidence=0.9, azimuth_deg=0.0, dt=0.05)
    for _ in range(10):
        state = est.update(motion_detected=False, confidence=0.0, azimuth_deg=0.0, dt=0.05)
    assert state["confidence"] < 0.1


def test_estimator_stays_inside_room():
    room = {"width": 4.0, "depth": 4.0, "height": 3.0}
    est = SpatialEstimator(room, smoothing=1.0, position_smoothing=1.0)
    for _ in range(500):
        state = est.update(motion_detected=True, confidence=1.0, azimuth_deg=45.0, dt=0.05)
    assert -1.6 <= state["x"] <= 1.6
    assert -1.6 <= state["z"] <= 1.6


def test_bearing_labels():
    from spatial.estimator import bearing_from_azimuth
    assert bearing_from_azimuth(0.0) == (0.0, "N")
    assert bearing_from_azimuth(90.0) == (90.0, "E")
    assert bearing_from_azimuth(24.0)[1] == "NE"

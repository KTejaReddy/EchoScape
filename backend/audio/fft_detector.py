"""Real-time FFT signal processing.

Pipeline for one stereo audio block:

    block -> window -> FFT -> magnitude spectrum
          -> peak search near the carrier frequency
          -> dominant frequency / deviation
          -> spectral energy / noise baseline
          -> signal strength
          -> motion score (via exponential smoothing)

Everything is kept deliberately simple and numerically stable so it can run
comfortably at 20-30 Hz on a normal laptop.
"""
from __future__ import annotations

import logging
from typing import Optional

import numpy as np

log = logging.getLogger("echoscape.audio.fft")

# How wide (Hz) the peak-search band around the carrier frequency is.
DEFAULT_BAND_HZ = 800.0


class FFTDetector:
    """Computes motion-relevant features from a single mono channel block."""

    def __init__(self, target_frequency: float, band_hz: float = DEFAULT_BAND_HZ) -> None:
        self.target_frequency = float(target_frequency)
        self.band_hz = float(band_hz)

        # Smoothed baselines (EMA). Initialised to None until first block.
        self._mag_baseline: Optional[float] = None
        self._energy_baseline: Optional[float] = None
        self._signal_alpha = 0.25

    def analyze(self, block: np.ndarray, sample_rate: int) -> dict:
        """Analyse one mono float32 block; returns a dict of features."""
        n = int(block.size)
        if n < 16:
            return self._empty_features()

        # 1. Window (Hann) to reduce spectral leakage.
        windowed = block * np.hanning(n)

        # 2. Magnitude spectrum.
        spectrum = np.fft.rfft(windowed)
        mag = np.abs(spectrum)
        freqs = np.fft.rfftfreq(n, d=1.0 / sample_rate)

        # 3. Search band around the carrier.
        lower = self.target_frequency - self.band_hz
        upper = self.target_frequency + self.band_hz
        in_band = (freqs >= lower) & (freqs <= upper)

        if not np.any(in_band):
            return self._empty_features()

        band_mag = np.where(in_band, mag, 0.0)
        peak_idx = int(np.argmax(band_mag))
        peak_freq = float(freqs[peak_idx])
        peak_mag = float(mag[peak_idx])

        # 4. Noise baseline: median magnitude outside the search band.
        outside = mag[~in_band]
        noise_floor = float(np.median(outside)) if outside.size else 1e-12
        noise_floor = max(noise_floor, 1e-12)

        # 5. Signal strength: how much the peak stands above the noise floor,
        #    mapped into 0..1 (1 - exp(-snr/scale) saturates smoothly).
        snr = peak_mag / noise_floor
        signal_strength = float(1.0 - np.exp(-snr / 6.0))

        # 6. Spectral energy of the whole block.
        energy = float(np.sum(mag * mag))

        # 7. Smoothed baselines for magnitude and energy.
        if self._mag_baseline is None:
            self._mag_baseline = peak_mag
            self._energy_baseline = energy
        else:
            a = self._signal_alpha
            self._mag_baseline = a * peak_mag + (1.0 - a) * self._mag_baseline
            self._energy_baseline = a * energy + (1.0 - a) * self._energy_baseline

        # 8. Deviation of the dominant peak from the carrier.
        deviation = peak_freq - self.target_frequency

        # 9. Motion score (0..1): combination of frequency deviation and the
        #    relative change in reflected energy. A moving body Doppler-shifts
        #    and modulates the reflected signal, so either effect raises it.
        #    The deviation term is gated by signal strength: when there is no
        #    real signal (silence), a stray "peak" must not count as motion.
        dev_norm = min(abs(deviation) / 150.0, 1.0)
        signal_gate = min(signal_strength / 0.4, 1.0)
        energy_change = 0.0
        if self._energy_baseline > 1e-12:
            energy_change = min(abs(energy - self._energy_baseline) / self._energy_baseline, 2.0) / 2.0
        motion_score = float(min(0.65 * dev_norm * signal_gate + 0.45 * energy_change, 1.0))

        return {
            "dominant_frequency": peak_freq,
            "frequency_deviation": deviation,
            "peak_magnitude": peak_mag,
            "noise_floor": noise_floor,
            "signal_strength": signal_strength,
            "spectral_energy": energy,
            "motion_score": motion_score,
            "peak_index": peak_idx,
            "band_low": lower,
            "band_high": upper,
        }

    def _empty_features(self) -> dict:
        return {
            "dominant_frequency": self.target_frequency,
            "frequency_deviation": 0.0,
            "peak_magnitude": 0.0,
            "noise_floor": 0.0,
            "signal_strength": 0.0,
            "spectral_energy": 0.0,
            "motion_score": 0.0,
            "peak_index": 0,
            "band_low": self.target_frequency - self.band_hz,
            "band_high": self.target_frequency + self.band_hz,
        }

    def reset(self) -> None:
        """Forget the smoothed baselines (used before calibration)."""
        self._mag_baseline = None
        self._energy_baseline = None

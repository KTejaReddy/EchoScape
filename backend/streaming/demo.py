"""Demo Mode simulator.

Produces realistic synthetic movement data (a person entering, walking around,
and leaving) that flows through the exact same producer/WebSocket pipeline as
the real DSP path. The payloads are clearly flagged with mode="demo" so the UI
never pretends synthetic data is real.
"""
from __future__ import annotations

import logging
import math
import random
import time
from typing import Optional

from spatial.coordinate_mapper import clamp_position, room_dims
from streaming.producer import Producer, build_payload

log = logging.getLogger("echoscape.streaming.demo")

# Scripted waypoints: (x, z, dwell_seconds). The demo "person" walks the room.
SCRIPT = [
    (-2.2, 1.6, 1.2),   # enters near the door / corner
    (-1.4, 1.3, 0.8),   # moves toward the desk
    (-0.4, 0.6, 0.6),   # crosses toward centre
    (0.5, 0.2, 1.0),    # centre
    (1.4, 0.8, 0.8),    # toward the wardrobe side
    (1.8, -0.6, 1.0),   # back across
    (0.6, -1.4, 0.7),   # toward the door
    (-0.8, -1.6, 1.2),  # pause near door
    (-1.6, -0.8, 0.6),  # returns toward desk
    (-2.2, 1.6, 2.0),   # back to start, dwell
]


class DemoSimulator:
    """Steps through the scripted path and publishes spatial_update payloads."""

    def __init__(
        self,
        producer: Producer,
        room: dict,
        frame_rate: float = 15.0,
        noise: float = 0.04,
        seed: Optional[int] = None,
    ) -> None:
        self.producer = producer
        self.room = room_dims(room)
        self.frame_rate = float(frame_rate)
        self.noise = float(noise)
        self._rng = random.Random(seed)

        self._waypoints = list(SCRIPT)
        self._wp_index = 0
        self._t_in_segment = 0.0
        self._pos = list(self._waypoints[0][:2])
        self._started_at = 0.0
        self._smoothed = {"x": self._pos[0], "z": self._pos[1], "speed": 0.0}

    def reset(self) -> None:
        self._wp_index = 0
        self._t_in_segment = 0.0
        self._pos = list(self._waypoints[0][:2])
        self._smoothed = {"x": self._pos[0], "z": self._pos[1], "speed": 0.0}

    def step(self) -> None:
        """Advance one frame and publish a payload."""
        dt = 1.0 / self.frame_rate
        self._t_in_segment += dt
        target, dwell = self._current_waypoint()
        seg_time = self._segment_time()

        if self._t_in_segment >= dwell + seg_time:
            self._wp_index = (self._wp_index + 1) % len(self._waypoints)
            self._t_in_segment = 0.0
            target, dwell = self._current_waypoint()
            seg_time = self._segment_time()

        # Ease-in/out through the segment so movement looks natural.
        t = min(max(self._t_in_segment - dwell, 0.0) / max(seg_time, 1e-6), 1.0)
        ease = 0.5 - 0.5 * math.cos(math.pi * t)
        # Integrate toward the target with an ease factor per frame.
        move = ease * dt / max(seg_time, 1e-6) * 1.4
        nx = self._pos[0] + (target[0] - self._pos[0]) * min(move, 1.0)
        nz = self._pos[1] + (target[1] - self._pos[1]) * min(move, 1.0)
        self._pos = [nx, nz]

        # Jitter + smoothing so the path is never perfectly straight.
        self._pos[0] += self._rng.uniform(-self.noise, self.noise)
        self._pos[1] += self._rng.uniform(-self.noise, self.noise)
        a = 0.35
        self._smoothed["x"] = a * self._pos[0] + (1 - a) * self._smoothed["x"]
        self._smoothed["z"] = a * self._pos[1] + (1 - a) * self._smoothed["z"]

        x, z = clamp_position(self._smoothed["x"], self._smoothed["z"], self.room)

        # Motion / confidence: dwell => pause with decaying confidence.
        moving = t > 0.03 and t < 0.97
        confidence = (0.55 + 0.4 * math.sin(t * math.pi)) if moving else 0.15
        confidence = min(max(confidence + self._rng.uniform(-0.05, 0.05), 0.0), 1.0)
        motion = confidence >= 0.35

        # Direction from the actual movement vector (compass bearing).
        dx = x - self._smoothed_x_prev()
        dz = z - self._smoothed_z_prev()
        bearing = (math.degrees(math.atan2(dx, dz)) + 360.0) % 360.0
        bearing_label = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"][int(round(bearing / 45.0)) % 8]

        inst_speed = math.hypot(dx, dz) / dt if motion else 0.0
        speed = min(inst_speed, 1.4)

        freq_shift = self._rng.uniform(-45, 45) if motion else self._rng.uniform(-8, 8)

        payload = build_payload(
            position={"x": x, "y": 0.0, "z": z},
            motion=motion,
            confidence=confidence,
            speed=round(speed, 3),
            bearing=round(bearing, 1),
            bearing_label=bearing_label,
            frequency=19000.0 + freq_shift,
            frequency_shift=freq_shift,
            signal_strength=round(min(max(0.5 + 0.3 * abs(math.sin(t * math.pi)) + self._rng.uniform(-0.06, 0.06), 0.0), 1.0), 3),
            mode="demo",
            motion_score=round(confidence, 3),
            spectral_energy=round(4.0 + self._rng.uniform(-0.4, 0.4), 2),
            azimuth=round(self._rng.uniform(-40, 40) if motion else 0.0, 1),
            tdoa_confidence=round(0.4 + 0.5 * confidence, 3),
        )
        self._prev_x, self._prev_z = x, z
        self.producer.publish(payload)

    # -- helpers ------------------------------------------------------------

    def _current_waypoint(self) -> tuple[tuple[float, float], float]:
        """Return ((x, z), dwell) for the current waypoint."""
        x, z, dwell = self._waypoints[self._wp_index]
        return (float(x), float(z)), float(dwell)

    def _segment_time(self) -> float:
        """Time (s) to traverse the current segment."""
        cur = self._waypoints[self._wp_index]
        prev = self._waypoints[(self._wp_index - 1) % len(self._waypoints)]
        dist = math.hypot(cur[0] - prev[0], cur[1] - prev[1])
        return max(dist / 0.9, 0.6)  # ~0.9 m/s walking speed

    def _smoothed_x_prev(self) -> float:
        return getattr(self, "_prev_x", self._smoothed["x"])

    def _smoothed_z_prev(self) -> float:
        return getattr(self, "_prev_z", self._smoothed["z"])

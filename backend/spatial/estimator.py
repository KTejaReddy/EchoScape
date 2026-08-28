"""Spatial position estimation.

Combines motion intensity, TDOA azimuth, and the previous position into a
smoothed estimated position inside the room.

Coordinate convention: the room is centred on the origin, +x is to the right
and +z is "ahead" (toward the camera). A TDOA azimuth of 0 degrees means
"straight ahead", positive azimuth means "to the right".

Behaviour:
  * while motion is detected, the estimate drifts along the (smoothed) TDOA
    azimuth with a speed proportional to confidence;
  * when idle, the position is held briefly while confidence decays;
  * positions are exponentially smoothed so the marker never teleports.
"""
from __future__ import annotations

import logging
import math
from typing import Optional

from spatial.coordinate_mapper import clamp_position, room_dims

log = logging.getLogger("echoscape.spatial.estimator")

# Eight-point compass labels for the dashboard.
COMPASS = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]


def _wrap_degrees(angle: float) -> float:
    """Wrap an angle into (-180, 180]."""
    return (angle + 180.0) % 360.0 - 180.0


def bearing_from_azimuth(azimuth_deg: float) -> tuple[float, str]:
    """Convert a TDOA azimuth into a compass bearing + label.

    Facing north (ahead = +z), a positive azimuth points east, so the compass
    bearing equals the azimuth directly. Returns (bearing_deg, label).
    """
    bearing = azimuth_deg % 360.0
    label = COMPASS[int(round(bearing / 45.0)) % 8]
    return round(bearing, 1), label


class SpatialEstimator:
    def __init__(
        self,
        room: dict,
        smoothing: float = 0.35,
        position_smoothing: float = 0.35,
        idle_hold: float = 2.5,
        idle_decay: float = 0.5,
        max_speed: float = 1.1,
    ) -> None:
        self.room = room_dims(room)
        self.max_speed = float(max_speed)

        # Position (metres), origin at room centre.
        self.x = 0.0
        self.z = 0.0
        self.y = 0.0
        self._true_x = 0.0  # unsmoothed integrator position
        self._true_z = 0.0

        self.confidence = 0.0
        self.speed = 0.0

        self._azimuth = 0.0  # smoothed azimuth (degrees)
        self._heading_alpha = float(smoothing)
        self._pos_alpha = float(position_smoothing)
        self._idle_hold = float(idle_hold)
        self._idle_decay = float(idle_decay)

        self._idle_accum = 0.0  # virtual seconds spent idle (deterministic)
        self._last_dt = 1.0 / 20.0

    def reset(self, room: Optional[dict] = None) -> None:
        if room is not None:
            self.room = room_dims(room)
        self.x = 0.0
        self.z = 0.0
        self.y = 0.0
        self._true_x = 0.0
        self._true_z = 0.0
        self.confidence = 0.0
        self.speed = 0.0
        self._azimuth = 0.0
        self._idle_accum = 0.0

    def update(self, motion_detected: bool, confidence: float, azimuth_deg: float, dt: Optional[float] = None) -> dict:
        """Advance the estimate one step and return the new state dict."""
        if dt is None or dt <= 0:
            dt = self._last_dt
        self._last_dt = min(max(dt, 0.01), 1.0)

        target_conf = self.confidence

        if motion_detected:
            self._idle_accum = 0.0

            # Circular EMA on the azimuth so it never wraps weirdly at +/-180.
            delta = _wrap_degrees(azimuth_deg - self._azimuth)
            self._azimuth = _wrap_degrees(self._azimuth + self._heading_alpha * delta)

            # Integrate the "true" position along the azimuth at full speed.
            # (dx = sin(az), dz = cos(az)). The display position below chases
            # this integrator, so tracking stays responsive while the path
            # stays smooth and can never teleport.
            speed = self.max_speed * min(confidence, 1.0)
            step = speed * dt
            self._true_x += math.sin(math.radians(self._azimuth)) * step
            self._true_z += math.cos(math.radians(self._azimuth)) * step
            self._true_x, self._true_z = clamp_position(self._true_x, self._true_z, self.room)
            target_conf = min(max(confidence, 0.0), 1.0)
        else:
            # Idle: hold the position briefly (virtual time), then decay.
            self._idle_accum += dt
            if self._idle_accum > self._idle_hold:
                target_conf = self.confidence * self._idle_decay
            else:
                target_conf = self.confidence

        # Smoothed display position chases the true integrator (EMA). This is
        # what the frontend sees; it never jumps because the inputs (azimuth,
        # confidence, speed) are already smoothed upstream.
        new_x = self._pos_alpha * self._true_x + (1.0 - self._pos_alpha) * self.x
        new_z = self._pos_alpha * self._true_z + (1.0 - self._pos_alpha) * self.z
        new_x, new_z = clamp_position(new_x, new_z, self.room)

        # Speed = actual distance travelled this tick, smoothed.
        dist = math.hypot(new_x - self.x, new_z - self.z)
        inst_speed = dist / dt if dt > 0 else 0.0
        self.speed = 0.6 * inst_speed + 0.4 * self.speed

        self.x, self.z = new_x, new_z
        self.confidence = min(max(target_conf, 0.0), 1.0)

        bearing, label = bearing_from_azimuth(self._azimuth)

        return {
            "x": round(self.x, 3),
            "y": 0.0,
            "z": round(self.z, 3),
            "confidence": round(self.confidence, 4),
            "speed": round(self.speed, 4),
            "azimuth": round(self._azimuth, 1),
            "bearing": bearing,
            "bearing_label": label,
        }

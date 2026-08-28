"""Room layout validation + coordinate mapping.

AI-generated furniture coordinates are never trusted directly. Every object is
validated (type, position, dimensions, rotation) and clamped inside the room
bounds. Anything invalid is dropped or replaced with a fallback object.
"""
from __future__ import annotations

import logging
from typing import Any

log = logging.getLogger("echoscape.spatial.mapper")

VALID_OBJECT_TYPES = {
    "bed", "sofa", "table", "desk", "chair", "wardrobe", "cabinet",
    "door", "window", "television", "tv", "shelf", "plant", "lamp",
    "nightstand", "rug", "bookcase", "bookshelf",
}

TYPE_ALIASES = {
    "tv": "television",
    "nightstand": "cabinet",
    "bookcase": "shelf",
    "bookshelf": "shelf",
}

# Sensible default size (metres) per object type when the model omits them.
DEFAULT_SIZES = {
    "bed": (2.0, 1.8, 0.5),
    "sofa": (2.2, 1.0, 0.9),
    "table": (1.4, 0.9, 0.75),
    "desk": (1.4, 0.7, 0.75),
    "chair": (0.5, 0.5, 0.9),
    "wardrobe": (1.2, 0.6, 2.0),
    "cabinet": (0.8, 0.5, 0.9),
    "door": (0.9, 0.15, 2.1),
    "window": (1.2, 0.1, 1.4),
    "television": (1.2, 0.1, 0.7),
    "shelf": (1.0, 0.3, 1.8),
    "plant": (0.4, 0.4, 1.2),
    "lamp": (0.3, 0.3, 1.4),
    "rug": (1.6, 2.4, 0.02),
}

ROOM_LIMITS = {"width": (2.0, 20.0), "depth": (2.0, 20.0), "height": (2.0, 6.0)}


class LayoutError(ValueError):
    """Raised when a layout cannot be salvaged at all."""


def _num(value: Any, default: float = 0.0) -> float:
    try:
        f = float(value)
    except (TypeError, ValueError):
        return default
    if f != f or f in (float("inf"), float("-inf")):  # NaN / inf
        return default
    return f


def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def validate_room_layout(layout: Any) -> dict:
    """Normalise an arbitrary parsed layout into a safe room description.

    Raises LayoutError when there is no usable room at all. Surviving objects
    are validated and clamped; unusable objects are skipped.
    """
    if not isinstance(layout, dict):
        raise LayoutError("Layout is not an object.")

    room_raw = layout.get("room") if isinstance(layout.get("room"), dict) else {}
    width = _clamp(_num(room_raw.get("width"), 6.0), *ROOM_LIMITS["width"])
    depth = _clamp(_num(room_raw.get("depth"), 5.0), *ROOM_LIMITS["depth"])
    height = _clamp(_num(room_raw.get("height"), 3.0), *ROOM_LIMITS["height"])

    room = {"width": width, "depth": depth, "height": height}

    objects_raw = layout.get("objects")
    if not isinstance(objects_raw, list):
        objects_raw = []

    objects: list[dict] = []
    for raw in objects_raw:
        if not isinstance(raw, dict):
            continue
        obj = _normalise_object(raw, room)
        if obj is not None:
            objects.append(obj)

    # Cap the object count to keep the scene cheap to render.
    objects = objects[:24]

    source = layout.get("source", "ai")
    return {"room": room, "objects": objects, "source": source}


def _normalise_object(raw: dict, room: dict) -> dict | None:
    """Validate + clamp a single object; returns None if it is unusable."""
    name = str(raw.get("name", "")).strip() or "object"
    raw_type = str(raw.get("type", "")).strip().lower()
    obj_type = TYPE_ALIASES.get(raw_type, raw_type)
    if obj_type not in VALID_OBJECT_TYPES:
        # Unknown types are dropped silently - the AI sometimes invents them.
        return None

    x = _num(raw.get("x"), 0.0)
    y = _num(raw.get("y"), 0.0)
    z = _num(raw.get("z"), 0.0)
    rotation = _num(raw.get("rotation"), 0.0)

    # Dimension defaults + sanity clamp (never let the AI fill the room).
    dw, dd, dh = DEFAULT_SIZES.get(obj_type, (0.6, 0.6, 0.8))
    width = _clamp(_num(raw.get("width"), dw), 0.1, min(room["width"] * 0.6, 4.0))
    depth = _clamp(_num(raw.get("depth"), dd), 0.1, min(room["depth"] * 0.6, 4.0))
    height = _clamp(_num(raw.get("height"), dh), 0.02, min(room["height"] * 0.9, 3.0))

    # Clamp the object's centre inside the room with a small margin.
    margin = 0.25
    x = _clamp(x, -room["width"] / 2 + margin, room["width"] / 2 - margin)
    z = _clamp(z, -room["depth"] / 2 + margin, room["depth"] / 2 - margin)
    y = max(0.0, min(_num(raw.get("y"), 0.0), room["height"]))

    return {
        "name": name,
        "type": obj_type,
        "x": round(x, 3),
        "y": round(y, 3),
        "z": round(z, 3),
        "width": round(width, 3),
        "depth": round(depth, 3),
        "height": round(height, 3),
        "rotation": round(rotation, 2),
    }


def fallback_layout() -> dict:
    """Default demo room used when Groq is unavailable or the analysis fails."""
    room = {"width": 6.0, "depth": 5.0, "height": 3.0}
    objects = [
        {"name": "Bed", "type": "bed", "x": -2.0, "y": 0.0, "z": 1.6, "width": 2.0, "depth": 1.8, "height": 0.5, "rotation": 0},
        {"name": "Desk", "type": "desk", "x": 1.8, "y": 0.0, "z": 1.8, "width": 1.4, "depth": 0.7, "height": 0.75, "rotation": 0},
        {"name": "Chair", "type": "chair", "x": 2.1, "y": 0.0, "z": 1.0, "width": 0.5, "depth": 0.5, "height": 0.9, "rotation": 0.4},
        {"name": "Wardrobe", "type": "wardrobe", "x": 2.3, "y": 0.0, "z": -1.6, "width": 1.2, "depth": 0.6, "height": 2.0, "rotation": -1.2},
        {"name": "Door", "type": "door", "x": 0.0, "y": 0.0, "z": -2.45, "width": 0.9, "depth": 0.12, "height": 2.1, "rotation": 0},
    ]
    return {"room": room, "objects": objects, "source": "demo"}


def clamp_position(x: float, z: float, room: dict, margin: float = 0.4) -> tuple[float, float]:
    """Clamp a person position inside the room bounds."""
    dims = room_dims(room)
    w, d = dims["width"], dims["depth"]
    cx = _clamp(x, -w / 2 + margin, w / 2 - margin)
    cz = _clamp(z, -d / 2 + margin, d / 2 - margin)
    return round(float(cx), 3), round(float(cz), 3)


def room_dims(layout_or_dims: dict) -> dict:
    """Normalise either a bare dims dict or a full layout dict to dims."""
    if isinstance(layout_or_dims, dict) and isinstance(layout_or_dims.get("room"), dict):
        return layout_or_dims["room"]
    if isinstance(layout_or_dims, dict) and "width" in layout_or_dims:
        return layout_or_dims
    return {"width": 6.0, "depth": 5.0, "height": 3.0}

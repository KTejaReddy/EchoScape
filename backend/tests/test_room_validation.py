"""Room layout validation and clamping tests."""
from __future__ import annotations

import pytest

from spatial.coordinate_mapper import (
    LayoutError,
    fallback_layout,
    validate_room_layout,
)


def test_valid_layout_passes():
    layout = {
        "room": {"width": 6, "depth": 5, "height": 3},
        "objects": [
            {"name": "bed", "type": "bed", "x": -1.5, "z": 1.2, "width": 2.0, "depth": 1.8, "height": 0.5, "rotation": 0}
        ],
    }
    out = validate_room_layout(layout)
    assert out["room"]["width"] == 6.0
    assert out["objects"][0]["type"] == "bed"
    assert out["source"] == "ai"


def test_unknown_type_dropped():
    layout = {
        "room": {"width": 6, "depth": 5, "height": 3},
        "objects": [{"name": "warp-drive", "type": "warp-drive", "x": 0, "z": 0}],
    }
    out = validate_room_layout(layout)
    assert out["objects"] == []


def test_type_alias_normalised():
    layout = {
        "room": {"width": 6, "depth": 5, "height": 3},
        "objects": [{"name": "tv", "type": "tv", "x": 0, "z": 0}],
    }
    out = validate_room_layout(layout)
    assert out["objects"][0]["type"] == "television"


def test_coordinates_clamped_into_room():
    layout = {
        "room": {"width": 4, "depth": 4, "height": 3},
        "objects": [{"name": "bed", "type": "bed", "x": 999, "z": -999, "width": 50, "depth": 50, "height": 50}],
    }
    out = validate_room_layout(layout)
    obj = out["objects"][0]
    assert obj["x"] <= 4.0 / 2 - 0.25 + 1e-6
    assert obj["z"] >= -(4.0 / 2 - 0.25) - 1e-6
    assert obj["width"] <= 4.0 * 0.6 + 1e-6


def test_invalid_layout_raises():
    with pytest.raises(LayoutError):
        validate_room_layout("not a dict")
    with pytest.raises(LayoutError):
        validate_room_layout(None)


def test_nan_values_replaced():
    layout = {
        "room": {"width": float("nan"), "depth": 5, "height": 3},
        "objects": [{"name": "chair", "type": "chair", "x": float("inf"), "z": 0}],
    }
    out = validate_room_layout(layout)
    assert out["room"]["width"] == 6.0  # default
    assert out["objects"][0]["x"] == 0.0


def test_fallback_layout_is_demo():
    layout = fallback_layout()
    assert layout["source"] == "demo"
    assert len(layout["objects"]) >= 5
    assert all(o["type"] in {"bed", "desk", "chair", "wardrobe", "door"} for o in layout["objects"])


def test_objects_capped():
    many = {
        "room": {"width": 6, "depth": 5, "height": 3},
        "objects": [{"name": f"o{i}", "type": "chair", "x": 0, "z": 0} for i in range(50)],
    }
    out = validate_room_layout(many)
    assert len(out["objects"]) <= 24

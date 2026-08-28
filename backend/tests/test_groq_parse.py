"""Defensive parsing of Groq vision output."""
from __future__ import annotations

import pytest

from vision.groq_layout import VisionError, parse_layout


def test_parse_clean_json():
    text = '{"room": {"width": 6, "depth": 5, "height": 3}, "objects": [{"name": "bed", "type": "bed", "x": -1.5, "z": 1.2, "width": 2.2, "depth": 2.0, "height": 0.6, "rotation": 0}]}'
    layout = parse_layout(text)
    assert layout["source"] == "ai"
    assert layout["objects"][0]["type"] == "bed"


def test_parse_json_inside_markdown_fence():
    text = '```json\n{"room": {"width": 6, "depth": 5, "height": 3}, "objects": []}\n```'
    layout = parse_layout(text)
    assert layout["room"]["width"] == 6.0


def test_parse_json_surrounded_by_prose():
    text = 'Here is the layout I detected:\n{"room": {"width": 6, "depth": 5, "height": 3}, "objects": []}\nHope this helps!'
    layout = parse_layout(text)
    assert layout["room"]["depth"] == 5.0


def test_parse_garbage_raises_friendly_error():
    with pytest.raises(VisionError, match="unreadable"):
        parse_layout("I am sorry but I cannot help with that request.")


def test_parse_none_raises():
    with pytest.raises(VisionError):
        parse_layout(None)


def test_parse_invalid_room_falls_back_to_defaults():
    # Valid JSON but unusable room -> still returns a safe layout (no crash).
    layout = parse_layout('{"room": {"width": null}, "objects": "nope"}')
    assert layout["room"]["width"] == 6.0
    assert layout["objects"] == []


def test_parse_unknown_types_dropped():
    text = '{"room": {"width": 6, "depth": 5, "height": 3}, "objects": [{"name": "mystery", "type": "warp-drive", "x": 0, "z": 0}, {"name": "sofa", "type": "sofa", "x": 0, "z": 0}]}'
    layout = parse_layout(text)
    assert [o["type"] for o in layout["objects"]] == ["sofa"]

"""Groq Vision room analysis.

Sends a room photo to a Groq vision-capable model and parses the resulting
furniture layout JSON defensively. Never trusts the AI output: malformed JSON
falls back gracefully and the whole call degrades to the demo room when Groq
is unavailable.
"""
from __future__ import annotations

import base64
import json
import logging
import re
from typing import Any, Optional

import requests

from config import (
    GROQ_API_KEY,
    GROQ_BASE_URL,
    GROQ_TIMEOUT,
    GROQ_VISION_MODEL,
)
from spatial.coordinate_mapper import LayoutError, validate_room_layout

log = logging.getLogger("echoscape.vision.groq")

SYSTEM_PROMPT = """You are EchoScape, an interior layout analyser for an experimental \
acoustic spatial-sensing prototype.

Look at the room photo and produce a STRICT JSON layout estimate. The JSON must be \
parseable with json.loads() and contain EXACTLY these fields, no markdown, no commentary:

{
  "room": {"width": <metres, number>, "depth": <metres, number>, "height": <metres, number>},
  "objects": [
    {
      "name": "<short label>",
      "type": "<one of: bed, sofa, table, desk, chair, wardrobe, cabinet, door, window, television, shelf, plant>",
      "x": <metres from room centre, + is right>,
      "z": <metres from room centre, + is toward the camera>,
      "y": 0,
      "width": <metres>,
      "depth": <metres>,
      "height": <metres>,
      "rotation": <radians, 0 = facing camera>
    }
  ]
}

Rules:
- Estimate room size in metres (typical rooms are 3-7 m wide).
- List the 5 largest/most visible furniture or structural objects.
- Coordinates are relative to the CENTRE of the room. Negative x = left, negative z = away.
- Keep every object inside the room bounds.
- Return ONLY the JSON object."""


class VisionError(Exception):
    """Friendly wrapper for Groq failures (no key, network, API error...)."""


def analyze_image(image_bytes: bytes, mime_type: str = "image/jpeg") -> dict:
    """Analyse a room photo and return a validated layout dict.

    Raises VisionError with a human-readable message when Groq cannot be used.
    """
    if not GROQ_API_KEY.strip():
        raise VisionError(
            "No GROQ_API_KEY configured. Add it to backend/.env to enable AI room analysis."
        )

    data_url = f"data:{mime_type};base64,{base64.b64encode(image_bytes).decode('ascii')}"

    payload = {
        "model": GROQ_VISION_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Analyse this room photo and return the layout JSON."},
                    {"type": "image_url", "image_url": {"url": data_url}},
                ],
            },
        ],
        "temperature": 0.2,
        "response_format": {"type": "json_object"},
        "max_tokens": 1200,
    }

    try:
        resp = requests.post(
            f"{GROQ_BASE_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=GROQ_TIMEOUT,
        )
    except requests.RequestException as exc:
        raise VisionError(f"Could not reach the Groq API: {exc}") from exc

    if resp.status_code == 401:
        raise VisionError("Groq rejected the API key. Check GROQ_API_KEY in backend/.env.")
    if resp.status_code == 429:
        raise VisionError("Groq rate limit reached. Wait a moment and try again.")
    if resp.status_code >= 400:
        raise VisionError(
            f"Groq API error {resp.status_code}: {resp.text[:300]}"
        )

    try:
        data = resp.json()
        content = data["choices"][0]["message"]["content"]
    except (ValueError, KeyError, IndexError, TypeError) as exc:
        raise VisionError("Groq returned an unexpected response shape.") from exc

    return parse_layout(content)


def parse_layout(content: str) -> dict:
    """Safely parse the model's text into a validated room layout."""
    text = str(content or "")
    parsed: Any = None

    # Try direct JSON parse first.
    try:
        parsed = json.loads(text)
    except ValueError:
        pass

    # Fallback: extract the first {...} block.
    if parsed is None:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                parsed = json.loads(match.group(0))
            except ValueError:
                parsed = None

    if parsed is None:
        raise VisionError(
            "The vision model returned unreadable output. Showing the demo room instead."
        )

    try:
        layout = validate_room_layout(parsed)
    except LayoutError:
        raise VisionError(
            "The vision model returned an invalid layout. Showing the demo room instead."
        ) from None

    layout["source"] = "ai"
    layout["model"] = GROQ_VISION_MODEL
    return layout

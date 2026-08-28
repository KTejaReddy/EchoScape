"""EchoScape configuration.

All tunables live in environment variables (see .env.example).
Every setting has a sensible default so the app runs out of the box.
"""
from __future__ import annotations

import os

from dotenv import load_dotenv

# Load .env if present (does nothing when the file is missing).
load_dotenv()


def _env_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on")


# ---------------------------------------------------------------------------
# Server
# ---------------------------------------------------------------------------
HOST = os.getenv("ECHOSCAPE_HOST", "127.0.0.1")
PORT = _env_int("ECHOSCAPE_PORT", 5001)
DEBUG = _env_bool("ECHOSCAPE_DEBUG", False)
LOG_LEVEL = os.getenv("ECHOSCAPE_LOG_LEVEL", "INFO").upper()

# CORS origin for the Vite dev server (and anything else that needs it).
CORS_ORIGINS = os.getenv("ECHOSCAPE_CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
CORS_ORIGIN_LIST = [o.strip() for o in CORS_ORIGINS.split(",") if o.strip()]

# ---------------------------------------------------------------------------
# Groq vision (room analysis)
# ---------------------------------------------------------------------------
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_VISION_MODEL = os.getenv("GROQ_VISION_MODEL", "llama-3.2-90b-vision-preview")
GROQ_BASE_URL = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")
GROQ_TIMEOUT = _env_float("GROQ_TIMEOUT", 45.0)

# ---------------------------------------------------------------------------
# Audio
# ---------------------------------------------------------------------------
AUDIO_SAMPLE_RATE = _env_int("AUDIO_SAMPLE_RATE", 48000)
AUDIO_BLOCK_SIZE = _env_int("AUDIO_BLOCK_SIZE", 2048)
AUDIO_CHANNELS = _env_int("AUDIO_CHANNELS", 2)
CARRIER_FREQUENCY = _env_float("CARRIER_FREQUENCY", 19000.0)
AUDIO_AMPLITUDE = _env_float("AUDIO_AMPLITUDE", 0.08)  # conservative, never loud
AUDIO_DEVICE = os.getenv("AUDIO_DEVICE", "")  # empty => system default
AUDIO_USE_CHIRP = _env_bool("AUDIO_USE_CHIRP", False)
AUDIO_CHIRP_RATE = _env_float("AUDIO_CHIRP_RATE", 400.0)  # Hz per second of sweep
AUDIO_GENERATE = _env_bool("AUDIO_GENERATE", True)  # play the probe tone at all
AUDIO_STREAM_RATE = _env_int("AUDIO_STREAM_RATE", 20)  # target WS updates / second

# ---------------------------------------------------------------------------
# TDOA / spatial geometry
# ---------------------------------------------------------------------------
MIC_DISTANCE = _env_float("MIC_DISTANCE", 0.15)  # meters between microphones
SPEED_OF_SOUND = _env_float("SPEED_OF_SOUND", 343.0)  # m/s

# ---------------------------------------------------------------------------
# Motion detection
# ---------------------------------------------------------------------------
MOTION_THRESHOLD = _env_float("MOTION_THRESHOLD", 0.35)  # 0..1 score to call "motion"
TDOA_SMOOTHING = _env_float("TDOA_SMOOTHING", 0.35)  # EMA alpha for angle
MOTION_SMOOTHING = _env_float("MOTION_SMOOTHING", 0.4)  # EMA alpha for motion score
POSITION_SMOOTHING = _env_float("POSITION_SMOOTHING", 0.35)  # EMA alpha for x/z
SIGNAL_ALPHA = _env_float("SIGNAL_ALPHA", 0.25)  # EMA for signal-strength baseline

# Idle behaviour: how long (seconds) to hold the last position with fading
# confidence before declaring idle.
IDLE_HOLD_SECONDS = _env_float("IDLE_HOLD_SECONDS", 2.5)
IDLE_CONFIDENCE_DECAY = _env_float("IDLE_CONFIDENCE_DECAY", 0.5)

# ---------------------------------------------------------------------------
# Demo mode
# ---------------------------------------------------------------------------
DEMO_FRAME_RATE = _env_int("DEMO_FRAME_RATE", 15)  # simulated updates / second
DEMO_NOISE = _env_float("DEMO_NOISE", 0.04)  # metres of jitter on the path

# ---------------------------------------------------------------------------
# Uploads
# ---------------------------------------------------------------------------
UPLOAD_DIR = os.getenv("ECHOSCAPE_UPLOAD_DIR", os.path.join(os.path.dirname(__file__), ".uploads"))
MAX_IMAGE_BYTES = _env_int("ECHOSCAPE_MAX_IMAGE_BYTES", 10 * 1024 * 1024)

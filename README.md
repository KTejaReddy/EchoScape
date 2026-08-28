# EchoScape — The $0-Budget Spatial Radar

> Privacy-first, camera-free-during-live-monitoring spatial presence detection using a laptop's **built-in speakers and microphones**, visualised inside an **AI-generated 3D room**.

EchoScape is a hackathon prototype that turns commodity laptop audio hardware into an *experimental* acoustic sensing system. It plays a quiet, high-frequency probe tone, listens to how the room reflects it, and estimates movement — then visualises that movement live in a stylised 3D digital twin created from a single room photo.

**External hardware: NONE. Camera: OFF during live monitoring.**

---

## 1. Project Overview

```
ROOM PHOTO
    ↓
Groq Vision API
    ↓
Furniture/Layout JSON
    ↓
3D Digital Room (React Three Fiber)
    ↓
Laptop Speaker → Acoustic Probe Tone
    ↓
Room Reflection
    ↓
Laptop Stereo Microphones
    ↓
Python DSP (FFT / TDOA / motion)
    ↓
Producer Queue → Flask → WebSocket
    ↓
React Frontend → Live 3D Spatial Visualization
```

Two sensing modes flow through the *exact same* WebSocket pipeline:

| Mode | Data source | Badge in UI |
|---|---|---|
| **Real Mode** | Actual laptop mic capture + FFT/TDOA DSP | `● LIVE ACOUSTIC` |
| **Demo Mode** | Scripted synthetic trajectory + realistic noise | `● DEMO MODE — synthetic data` |

Demo Mode exists so a hackathon demo never dies to bad audio hardware, a noisy venue, or missing mic permissions.

## 2. Problem

- Cameras are invasive and often unwelcome in private spaces.
- Dedicated presence sensors / radar modules cost money and hardware.
- Every laptop already ships with a speaker and (usually) stereo microphones — commodity hardware that is almost never repurposed for sensing.

## 3. Solution

EchoScape repurposes that built-in audio hardware:

1. **Probe** — plays a quiet 19 kHz tone (configurable, inaudible to most humans).
2. **Listen** — captures the reflected signal on both mics.
3. **Estimate** — FFT finds the reflected peak; frequency shift + energy modulation indicate motion; stereo cross-correlation (TDOA) hints at direction.
4. **Visualise** — the estimate drives a glowing marker, ripples, a trajectory trail, and a responsive grid inside an AI-generated 3D room.

It is **experimental** by design: it estimates *presence and coarse direction*, not centimetre-perfect tracking.

## 4. Architecture

```
┌─────────────────────────────── BACKEND (Python 3.10+) ───────────────────────────────┐
│                                                                                      │
│  audio/generator.py      speaker probe tone (sine / chirp)                           │
│  audio/recorder.py       stereo mic capture (mono fallback) ──┐                      │
│  audio/fft_detector.py   Hann window → FFT → peak/energy       │                      │
│  audio/tdoa.py           cross-correlation L/R → azimuth      ▼                      │
│  audio/motion_detector.py  smoothing → IDLE / MOTION      ┌───────────┐             │
│  spatial/estimator.py    position integration + smoothing  │ producer │  queue.Queue │
│  streaming/demo.py       scripted demo trajectory ───────▶ │  queue   │             │
│                                                           └───────────┘             │
│                                                                   │                  │
│                                        Flask-SocketIO emitter thread (consumer)      │
│                                                   │                                  │
│   REST: /api/health · /api/analyze-room · /api/sensor/* · /api/devices               │
│   WS:   /socket.io  →  spatial_update · sensor_started/stopped · calibration_*      │
└──────────────────────────────────────────────────────────────────────────────────────┘
                                    │  WebSocket  │
┌────────────────────────────────────▼─────────────┴───────────────────────────────────┐
│                         FRONTEND (React + Vite + Three.js)                           │
│  useWebSocket → useEchoScape (state) → RoomCanvas                                     │
│  Furniture (procedural low-poly) · GridFloor (shader ripples) · PersonTracker        │
│  AcousticRipples · Trajectory · Dashboard (metrics, signal monitor, controls)        │
└──────────────────────────────────────────────────────────────────────────────────────┘
```

Key design decision: **producer/consumer with a thread-safe `queue.Queue`**. Audio capture and DSP run on a background worker thread; a single emitter thread drains the queue and pushes payloads over WebSocket. No heavy FFT work ever happens inside a Flask request thread.

## 5. Tech Stack

**Backend** — Python 3.10+, Flask, Flask-SocketIO, NumPy, SciPy, sounddevice, python-dotenv, requests, queue + threading.

**Frontend** — React 18, Vite 5, Three.js, React Three Fiber, @react-three/drei, Tailwind CSS, socket.io-client, lucide-react, Vitest + Testing Library.

**AI** — Groq Vision API (configurable model) for room photo → furniture layout.

## 6. Installation

### Requirements

| Thing | Minimum |
|---|---|
| OS | Windows / macOS / Linux |
| Python | 3.10+ |
| Node.js | 18+ |
| Laptop | built-in microphone + speaker |
| Groq API key | *optional* — needed only for AI room analysis (a demo room is built in) |

External hardware: **NONE**.

### One-command start (Windows)

```bat
start.bat
```

This checks Python/Node, creates `backend/.venv`, installs backend + frontend dependencies, starts the backend, and launches the frontend dev server.

PowerShell users: `.\start.ps1` (same behaviour, stops both processes with Ctrl+C).

### Manual start

```bash
# 1. Backend
cd backend
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt     # Windows
# .venv/bin/python on macOS/Linux
cp .env.example .env                                        # optional: add GROQ_API_KEY
.venv/Scripts/python app.py                                  # → http://127.0.0.1:5001

# 2. Frontend (new terminal)
cd frontend
npm install
npm run dev                                                 # → http://localhost:5173
```

Open **http://localhost:5173** in a browser.

## 7. Environment Variables

Copy `backend/.env.example` → `backend/.env` and adjust if needed. **Never commit `.env`.** Keys are never sent to the frontend.

| Variable | Default | Purpose |
|---|---|---|
| `GROQ_API_KEY` | *(empty)* | Groq API key for AI room analysis |
| `GROQ_VISION_MODEL` | `llama-3.2-90b-vision-preview` | Vision model (make sure it supports vision + JSON output) |
| `AUDIO_SAMPLE_RATE` | `48000` | Capture/generation sample rate |
| `AUDIO_BLOCK_SIZE` | `2048` | FFT block size |
| `CARRIER_FREQUENCY` | `19000` | Probe tone frequency (Hz). Lower to ~18k if your laptop can't do 19k |
| `AUDIO_AMPLITUDE` | `0.08` | Probe volume (conservative; keep it low) |
| `AUDIO_DEVICE` | *(empty)* | Pin a specific audio device by name (substring) |
| `AUDIO_GENERATE` | `1` | Set `0` to sense without playing the probe tone |
| `AUDIO_USE_CHIRP` | `0` | Experimental: sweep the carrier instead of a fixed tone |
| `MIC_DISTANCE` | `0.15` | Estimated spacing between microphones (metres) |
| `SPEED_OF_SOUND` | `343` | Speed of sound (m/s) |
| `MOTION_THRESHOLD` | `0.35` | Smoothed score above which motion is declared |
| `TDOA_SMOOTHING` | `0.35` | EMA alpha for the TDOA azimuth |
| `MOTION_SMOOTHING` | `0.4` | EMA alpha for the motion score |
| `POSITION_SMOOTHING` | `0.35` | EMA alpha for the displayed position |
| `IDLE_HOLD_SECONDS` | `2.5` | How long to hold position after motion stops |
| `IDLE_CONFIDENCE_DECAY` | `0.5` | Confidence multiplier when idle |
| `DEMO_FRAME_RATE` | `15` | Demo mode update rate |
| `DEMO_NOISE` | `0.04` | Demo path jitter (metres) |
| `ECHOSCAPE_HOST/PORT` | `127.0.0.1 / 5001` | Backend bind address |

## 8. Running the Application

1. **Landing** → click **Create Spatial Map** (or **Try the Demo Room** to skip analysis).
2. **Setup** → upload a room photo → **Analyze Room**. Groq Vision returns a layout JSON, the backend validates/clamps it, and the 3D room appears. Without a Groq key the app uses a clearly-labelled **DEMO ROOM**.
3. **Live view** → **Start Sensor**.
   - **Real Mode** opens your microphone, plays the probe tone, and streams DSP estimates.
   - **Demo Mode** streams a scripted synthetic trajectory through the identical pipeline.
4. Watch the dashboard: position, confidence, direction, speed, frequency shift, signal monitor. The grid ripples on motion; the marker glows and trails a fading path.
5. **Calibrate** (Real Mode) measures a 3-second acoustic baseline used to improve motion detection.

## 9. Real Mode

1. Click **Real Mode**.
2. If the browser asks for microphone permission — the mic is used by the **Python backend**, so grant permission to the OS/terminal, not the browser.
3. The backend plays the probe tone and processes ~20 blocks/second.
4. Walk around. The marker moves with *estimated* position and confidence.

Real Mode is receive-only (`AUDIO_GENERATE=0`) if you prefer, and the carrier frequency is configurable for laptops that cannot reproduce/record 20 kHz.

## 10. Demo Mode

Click **Demo Mode**. A scripted "person" enters near the door, walks the room (desk → centre → wardrobe → door → back), with eased motion, jitter, pauses, and matching speed/confidence/direction/signal values. The header badge reads **`● DEMO MODE — synthetic data`** so the demo is never mistaken for real sensing.

## 11. DSP Explanation

For each stereo block (`AUDIO_BLOCK_SIZE` samples at `AUDIO_SAMPLE_RATE`):

```
block → Hann window → rfft → magnitude spectrum
     → peak search in band [carrier ± 800 Hz]
     → dominant frequency / deviation
     → spectral energy + noise-floor baseline (median outside band)
     → signal strength = 1 - exp(-SNR/scale)  (0..1)
     → motion score = f(deviation, energy change)  (gated by signal strength)
     → exponential smoothing → IDLE / MOTION
```

- **Frequency deviation** captures Doppler-ish shifts of the reflected peak as a body moves.
- **Energy modulation** captures the body breaking/rebuilding the reflection path.
- The deviation term is **gated by signal strength** so silence or a stray peak never registers as motion.
- All noisy quantities are exponentially smoothed (EMA) before use.

## 12. TDOA Explanation

A simplified stereo Time-Difference-of-Arrival estimator:

```
delay = argmax( cross-correlation( L, R ) )        # scipy.signal.correlate
angle = asin( delay · speed_of_sound / mic_distance )
```

- Delay is clamped to the physically plausible range (±`MIC_DISTANCE / SPEED_OF_SOUND`).
- Angles are clamped to ±55° and a weak correlation peak yields a **neutral** estimate.
- The azimuth feeds the spatial estimator, which integrates a smoothed position:

```
x += sin(azimuth) · speed · dt
z += cos(azimuth) · speed · dt        (position clamped inside the room)
```

**Honest expectation:** TDOA on two laptop mics gives a *coarse direction*, not metre-level accuracy. The prototype favours stable, smooth output over fake precision.

## 13. Groq Vision Explanation

1. The photo is base64-encoded and posted to Groq's chat-completions endpoint with `response_format: json_object`.
2. The model is asked for **strict JSON**: room width/depth/height plus ~5 objects with type, position, size, rotation.
3. The backend **never trusts the output**: it parses defensively (direct JSON → `{...}` extraction fallback), validates every object type, clamps coordinates/dimensions into the room, drops unknown types, and caps object count.
4. Any failure (no key, bad key, rate limit, malformed JSON) falls back to the built-in demo room with a friendly note — the app never crashes on AI output.

## 14. WebSocket Architecture

- Client connects to `/socket.io` (proxied by Vite in dev).
- A persistent **emitter thread** drains the `queue.Queue` producer and emits `spatial_update` (~10–30 Hz) plus lifecycle events: `sensor_started`, `sensor_stopped`, `room_updated`, `calibration_started/progress/complete`, `error`, `status`.
- REST endpoints (`/api/sensor/start|stop|calibrate`, `/api/analyze-room`) control the backend; WebSocket is the one-way live stream plus a `ping`/`pong` keepalive.
- The client reconnects automatically and re-syncs room + sensor status on connect.

Example payload:

```json
{
  "type": "spatial_update",
  "timestamp": 1720000000,
  "position": {"x": 1.25, "y": 0, "z": -0.72},
  "motion": true,
  "confidence": 0.82,
  "speed": 0.41,
  "direction": 24,
  "direction_label": "NE",
  "frequency": 19007,
  "frequency_shift": 7.0,
  "signal_strength": 0.73,
  "mode": "real"
}
```

## 15. Troubleshooting

| Symptom | Fix |
|---|---|
| "Microphone unavailable" | Grant OS mic permission to your terminal/IDE; set `AUDIO_DEVICE` to another device; or switch to Demo Mode |
| No tone heard / nothing detected | Lower `CARRIER_FREQUENCY` to 18000–18500; raise `AUDIO_AMPLITUDE` a little; check `AUDIO_DEVICE` |
| Weird/none audio devices | Use **Demo Mode** for the presentation — the pipeline is identical |
| Groq analysis fails | Check `GROQ_API_KEY` in `backend/.env`; the app falls back to the demo room automatically |
| WebSocket disconnects | The client reconnects automatically; confirm the backend is running and the Vite proxy (`/socket.io`) is up |
| Everything works but marker barely moves | Real-mode sensing is environment-dependent; run **Calibrate** while the room is still, and walk *between* the speaker and mic |

## 16. Limitations

- **Experimental acoustic localization.** A laptop's microphones are close together and non-calibrated; TDOA gives a *coarse direction*, never centimetre-perfect tracking. Positions are smoothed estimates, not ground truth.
- **Environment sensitive.** Loud venues, fan noise, other 19 kHz-ish sources, and reverberation degrade reliability.
- **Hardware variance.** Some laptops cannot reproduce or capture ~20 kHz well — the frequency is configurable for this reason.
- **Demo ≠ real.** Synthetic demo data is clearly labelled in the UI.
- **No persistence.** Rooms and sessions live in memory; a server restart resets to the demo room.
- **Prototype robustness.** Best-effort graceful degradation everywhere, but this is a hackathon prototype, not production sensing.

## 17. Future Improvements

- Full-spectrum analysis (phase across frames) and a proper chirp-sequence TDOA.
- Online per-device calibration that learns the direct-path baseline.
- Multi-tone spread-spectrum probes for resilience to noise and other sources.
- Web Audio / browser-based capture as a fallback when PortAudio is unavailable.
- Room persistence, multiple rooms, and shared multi-client viewing.
- Recording/playback of raw audio blocks for reproducible testing.
- Confidence-weighted Kalman filtering instead of EMA.

---

## Testing

```bash
# Backend (46 tests: DSP, TDOA, motion, estimator, room validation, Groq parse, API)
cd backend && .venv/Scripts/python -m pytest

# Frontend (10 tests: layout normalisation, app shell, WebSocket handling)
cd frontend && npm test

# Frontend production build
cd frontend && npm run build
```

---

*EchoScape — turning ordinary laptop audio hardware into an experimental, privacy-first spatial sensing system.*

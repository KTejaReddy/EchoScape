"""API endpoint tests (Flask test client, no real audio devices touched)."""
from __future__ import annotations

import base64
import io

import pytest

import app as app_module

client = app_module.app.test_client()


@pytest.fixture(autouse=True)
def _stop_sensor():
    """Ensure no sensor is left running between tests."""
    yield
    app_module.manager.stop_sensor()


def test_health():
    resp = client.get("/api/health")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["status"] == "ok"
    assert "groq_configured" in body


def test_room_endpoint_returns_fallback():
    resp = client.get("/api/room")
    assert resp.status_code == 200
    assert resp.get_json()["source"] == "demo"


def test_analyze_room_without_image():
    resp = client.post("/api/analyze-room", json={})
    assert resp.status_code == 400
    assert "image" in resp.get_json()["error"].lower()


def test_analyze_room_falls_back_without_api_key(monkeypatch):
    # Force "no API key" regardless of the local .env, then confirm the app
    # degrades to the demo room instead of crashing.
    monkeypatch.setattr("vision.groq_layout.GROQ_API_KEY", "")
    tiny = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
    )
    resp = client.post(
        "/api/analyze-room",
        data={"image": (io.BytesIO(tiny), "room.png")},
        content_type="multipart/form-data",
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["source"] == "demo"
    assert "note" in body


def test_analyze_room_invalid_base64():
    resp = client.post("/api/analyze-room", json={"image_base64": "%%%not-base64%%%"})
    assert resp.status_code == 400


def test_sensor_start_demo():
    resp = client.post("/api/sensor/start", json={"mode": "demo"})
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["mode"] == "demo"
    assert body["running"] is True


def test_sensor_start_invalid_mode():
    resp = client.post("/api/sensor/start", json={"mode": "banana"})
    assert resp.status_code == 400


def test_sensor_stop():
    client.post("/api/sensor/start", json={"mode": "demo"})
    resp = client.post("/api/sensor/stop")
    assert resp.status_code == 200
    assert resp.get_json()["running"] is False


def test_sensor_status():
    resp = client.get("/api/sensor/status")
    assert resp.status_code == 200
    body = resp.get_json()
    assert "mode" in body
    assert "room" in body
    assert "audio" in body


def test_calibration_requires_real_mode():
    resp = client.post("/api/sensor/calibrate")
    assert resp.status_code == 400


def test_devices_endpoint():
    resp = client.get("/api/devices")
    assert resp.status_code == 200
    assert "devices" in resp.get_json()


def test_room_reset():
    resp = client.post("/api/room/reset")
    assert resp.status_code == 200
    assert resp.get_json()["source"] == "demo"


def test_demo_stream_produces_spatial_payload():
    from streaming.producer import Producer
    from streaming.demo import DemoSimulator
    producer = Producer()
    demo = DemoSimulator(producer, app_module.manager.room, frame_rate=15.0, noise=0.0, seed=7)
    for _ in range(30):
        demo.step()
    payload = producer.get(timeout=0.1)
    assert payload is not None
    assert payload["type"] == "spatial_update"
    assert payload["mode"] == "demo"

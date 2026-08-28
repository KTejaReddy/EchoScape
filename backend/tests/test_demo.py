"""Demo simulator + payload builder tests."""
from __future__ import annotations

from streaming.demo import DemoSimulator
from streaming.producer import Producer, build_payload


def _run_frames(demo: DemoSimulator, frames: int):
    for _ in range(frames):
        demo.step()


def test_demo_produces_payloads():
    producer = Producer()
    demo = DemoSimulator(producer, {"width": 6.0, "depth": 5.0, "height": 3.0}, frame_rate=15.0, noise=0.0, seed=42)
    _run_frames(demo, 60)
    payload = producer.latest()
    assert payload is not None
    assert payload["type"] == "spatial_update"
    assert payload["mode"] == "demo"
    assert -3.0 <= payload["position"]["x"] <= 3.0
    assert -2.5 <= payload["position"]["z"] <= 2.5
    assert 0.0 <= payload["confidence"] <= 1.0
    assert isinstance(payload["motion"], bool)


def test_demo_moves_around():
    producer = Producer()
    demo = DemoSimulator(producer, {"width": 6.0, "depth": 5.0, "height": 3.0}, frame_rate=15.0, noise=0.0, seed=1)
    _run_frames(demo, 10)
    first = producer.latest()["position"]
    _run_frames(demo, 60)
    later = producer.latest()["position"]
    # The demo person must actually move.
    assert abs(first["x"] - later["x"]) + abs(first["z"] - later["z"]) > 0.3


def test_demo_reset():
    producer = Producer()
    demo = DemoSimulator(producer, {"width": 6.0, "depth": 5.0, "height": 3.0})
    _run_frames(demo, 90)
    demo.reset()
    assert demo._pos == list(demo._waypoints[0][:2])  # noqa: SLF001


def test_build_payload_fields():
    payload = build_payload(
        position={"x": 1.2, "y": 0.0, "z": -0.8},
        motion=True,
        confidence=0.82,
        speed=0.41,
        bearing=24.0,
        bearing_label="NE",
        frequency=19007.0,
        frequency_shift=7.0,
        signal_strength=0.73,
        mode="real",
    )
    assert payload["position"] == {"x": 1.2, "y": 0.0, "z": -0.8}
    assert payload["direction"] == 24.0
    assert payload["direction_label"] == "NE"
    assert payload["mode"] == "real"

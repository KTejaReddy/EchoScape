import { describe, expect, it } from "vitest";
import { normalizeRoom } from "../hooks/useEchoScape";

const demoLayout = {
  room: { width: 6, depth: 5, height: 3 },
  objects: [
    { name: "Bed", type: "bed", x: -2, z: 1.6, width: 2, depth: 1.8, height: 0.5, rotation: 0 },
    { name: "Desk", type: "desk", x: 1.8, z: 1.8, width: 1.4, depth: 0.7, height: 0.75 },
  ],
  source: "demo",
};

describe("normalizeRoom", () => {
  it("keeps valid objects and dims", () => {
    const { layout, source } = normalizeRoom(demoLayout);
    expect(source).toBe("demo");
    expect(layout.room).toEqual({ width: 6, depth: 5, height: 3 });
    expect(layout.objects).toHaveLength(2);
    expect(layout.objects[0].type).toBe("bed");
  });

  it("drops unknown types", () => {
    const { layout } = normalizeRoom({
      ...demoLayout,
      objects: [...demoLayout.objects, { name: "warp", type: "warp-drive", x: 0, z: 0 }],
    });
    expect(layout.objects).toHaveLength(2);
  });

  it("aliases tv to television", () => {
    const { layout } = normalizeRoom({
      ...demoLayout,
      objects: [{ name: "TV", type: "tv", x: 0, z: 0 }],
    });
    expect(layout.objects[0].type).toBe("television");
  });

  it("clamps out-of-room coordinates and sizes", () => {
    const { layout } = normalizeRoom({
      room: { width: 4, depth: 4, height: 3 },
      objects: [{ name: "bed", type: "bed", x: 999, z: -999, width: 50, depth: 50, height: 50 }],
    });
    const o = layout.objects[0];
    expect(o.x).toBeLessThanOrEqual(2);
    expect(o.z).toBeGreaterThanOrEqual(-2);
    expect(o.width).toBeLessThanOrEqual(2.4);
  });

  it("falls back to a default room when missing", () => {
    const { layout, source } = normalizeRoom(null);
    expect(source).toBe("demo");
    expect(layout.room.width).toBe(6);
    expect(layout.objects).toEqual([]);
  });

  it("marks ai source rooms", () => {
    const { source } = normalizeRoom({ ...demoLayout, source: "ai" });
    expect(source).toBe("ai");
  });
});

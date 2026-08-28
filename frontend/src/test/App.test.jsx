import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";

const demoLayout = {
  room: { width: 6, depth: 5, height: 3 },
  objects: [
    { name: "Bed", type: "bed", x: -2, z: 1.6, width: 2, depth: 1.8, height: 0.5, rotation: 0 },
    { name: "Desk", type: "desk", x: 1.8, z: 1.8, width: 1.4, depth: 0.7, height: 0.75 },
  ],
  source: "demo",
};

const handlers = {};
const stubSocket = {
  on: vi.fn((name, fn) => {
    handlers[name] = fn;
    return stubSocket;
  }),
  emit: vi.fn(),
  disconnect: vi.fn(),
};

vi.mock("socket.io-client", () => ({
  io: vi.fn(() => stubSocket),
}));

vi.mock("../services/api", () => ({
  getRoom: vi.fn(() => Promise.resolve(demoLayout)),
  getStatus: vi.fn(() =>
    Promise.resolve({ mode: null, room: demoLayout, running: false })
  ),
  getHealth: vi.fn(() => Promise.resolve({ status: "ok" })),
  analyzeRoomImage: vi.fn(),
  resetRoom: vi.fn(() => Promise.resolve(demoLayout)),
  startSensor: vi.fn(() => Promise.resolve({ mode: "demo", running: true })),
  stopSensor: vi.fn(() => Promise.resolve({ running: false })),
  calibrateSensor: vi.fn(() => Promise.resolve({})),
}));

import App from "../App";

describe("EchoScape app shell", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders the landing screen", async () => {
    render(<App />);
    expect(await screen.findByText("The $0-Budget Spatial Radar")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /echo\s*scape/i })).toBeInTheDocument();
  });

  it("moves from landing to setup", async () => {
    render(<App />);
    fireEvent.click(await screen.findByText("Create Spatial Map"));
    expect(await screen.findByText("Create Room")).toBeInTheDocument();
    expect(screen.getByText(/Upload a photo of the room/i)).toBeInTheDocument();
  });

  it("shows the upload area and demo room escape hatch", async () => {
    render(<App />);
    fireEvent.click(await screen.findByText("Create Spatial Map"));
    expect(await screen.findByText("Upload Room Image")).toBeInTheDocument();
    expect(screen.getByText("Use Demo Room")).toBeInTheDocument();
  });

  it("handles spatial updates arriving over the socket without crashing", async () => {
    render(<App />);
    await screen.findByText("The $0-Budget Spatial Radar");

    const update = {
      type: "spatial_update",
      timestamp: Date.now() / 1000,
      position: { x: 1.2, y: 0, z: -0.8 },
      motion: true,
      confidence: 0.82,
      speed: 0.4,
      direction: 24,
      direction_label: "NE",
      frequency: 19007,
      signal_strength: 0.73,
      mode: "demo",
    };
    handlers["spatial_update"](update);

    expect(screen.getByText("The $0-Budget Spatial Radar")).toBeInTheDocument();
  });
});

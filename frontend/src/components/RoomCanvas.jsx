import { useMemo } from "react";
import { Canvas } from "@react-three/fiber";
import { OrbitControls, Edges } from "@react-three/drei";
import * as THREE from "three";

import Furniture from "./Furniture";
import GridFloor from "./GridFloor";
import Trajectory from "./Trajectory";
import PersonTracker from "./PersonTracker";
import AcousticRipples from "./AcousticRipples";

function RoomShell({ room }) {
  const { width, depth, height } = room;
  const t = 0.12; // wall thickness

  const walls = useMemo(
    () => [
      { args: [width + t * 2, height, t], pos: [0, height / 2, depth / 2] },
      { args: [width + t * 2, height, t], pos: [0, height / 2, -depth / 2] },
      { args: [t, height, depth], pos: [width / 2, height / 2, 0] },
      { args: [t, height, depth], pos: [-width / 2, height / 2, 0] },
    ],
    [width, depth, height]
  );

  return (
    <group>
      {/* floor base */}
      <mesh position={[0, -0.06, 0]}>
        <boxGeometry args={[width + 0.4, 0.08, depth + 0.4]} />
        <meshStandardMaterial color="#070c16" roughness={0.95} />
      </mesh>

      {/* walls */}
      {walls.map((w, i) => (
        <mesh key={i} position={w.pos}>
          <boxGeometry args={w.args} />
          <meshStandardMaterial color="#0d1a2c" roughness={0.9} transparent opacity={0.6} side={THREE.DoubleSide} />
          <Edges scale={1.002} color="#155e75" />
        </mesh>
      ))}

      {/* subtle ceiling glow ring instead of a solid ceiling */}
      <mesh position={[0, height + 0.02, 0]} rotation-x={Math.PI / 2}>
        <ringGeometry args={[Math.min(width, depth) * 0.32, Math.min(width, depth) * 0.38, 64]} />
        <meshBasicMaterial color="#0e7490" transparent opacity={0.18} side={THREE.DoubleSide} depthWrite={false} blending={THREE.AdditiveBlending} />
      </mesh>
    </group>
  );
}

export default function RoomCanvas({ room, spatial, trajectory, ripples, onRippleExpire }) {
  const dims = room.room;
  const { width, depth, height } = dims;

  const cameraPos = useMemo(
    () => [width * 0.75 + 2.2, height * 0.9 + 1.6, depth * 0.85 + 2.6],
    [width, depth, height]
  );

  const pos = spatial?.position ?? { x: 0, y: 0, z: 0 };
  const confidence = spatial?.confidence ?? 0;
  const motion = Boolean(spatial?.motion);

  return (
    <Canvas
      dpr={[1, 1.75]}
      camera={{ position: cameraPos, fov: 42, near: 0.1, far: 120 }}
      gl={{ antialias: true, powerPreference: "high-performance" }}
    >
      <color attach="background" args={["#05070d"]} />
      <fog attach="fog" args={["#05070d", 14, 34]} />

      <ambientLight intensity={0.45} color="#bcd8ff" />
      <directionalLight position={[6, 9, 4]} intensity={0.75} color="#cfe8ff" />
      <pointLight position={[0, 2.4, 0]} intensity={0.5} distance={12} color="#22d3ee" />

      <RoomShell room={dims} />
      <Furniture objects={room.objects} />
      <GridFloor room={room} person={pos} motion={motion} ripples={ripples} />
      <Trajectory points={trajectory} />
      <PersonTracker position={pos} confidence={confidence} motion={motion} />
      <AcousticRipples ripples={ripples} onExpire={onRippleExpire} />

      <OrbitControls
        makeDefault
        enablePan={false}
        minDistance={2}
        maxDistance={34}
        maxPolarAngle={Math.PI / 2.12}
        target={[0, 0.5, 0]}
        enableDamping
        dampingFactor={0.08}
      />
    </Canvas>
  );
}

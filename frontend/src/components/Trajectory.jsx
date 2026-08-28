import { useEffect, useRef } from "react";
import * as THREE from "three";

/**
 * Renders the recent estimated positions as a glowing line whose colour fades
 * toward the older end (bright cyan = current, dark = history).
 */
export default function Trajectory({ points }) {
  const lineRef = useRef();

  useEffect(() => {
    const line = lineRef.current;
    if (!line) return;
    const n = points.length;
    const positions = new Float32Array(Math.max(n, 2) * 3);
    const colors = new Float32Array(Math.max(n, 2) * 3);

    for (let i = 0; i < n; i++) {
      const p = points[i];
      positions[i * 3] = p.x;
      positions[i * 3 + 1] = 0.03;
      positions[i * 3 + 2] = p.z;
      const t = i / Math.max(n - 1, 1);
      // older (t=0) -> dark slate, newer (t=1) -> bright cyan
      const c = new THREE.Color();
      c.setHSL(0.52, 0.95, 0.12 + 0.5 * t);
      colors[i * 3] = c.r;
      colors[i * 3 + 1] = c.g;
      colors[i * 3 + 2] = c.b;
    }

    const geom = line.geometry;
    geom.setAttribute("position", new THREE.BufferAttribute(positions, 3));
    geom.setAttribute("color", new THREE.BufferAttribute(colors, 3));
    geom.setDrawRange(0, Math.max(n, 2));
    geom.computeBoundingSphere();
    line.visible = n > 1;
  }, [points]);

  return (
    <line ref={lineRef} visible={false}>
      <bufferGeometry />
      <lineBasicMaterial
        vertexColors
        transparent
        opacity={0.85}
        blending={THREE.AdditiveBlending}
        depthWrite={false}
      />
    </line>
  );
}

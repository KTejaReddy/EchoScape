import { useMemo, useRef } from "react";
import * as THREE from "three";
import { useFrame } from "@react-three/fiber";

/**
 * Stylised spatial marker for the estimated person position: a glowing core,
 * a vertical light beam and a confidence ring. Interpolates smoothly so the
 * marker never teleports between updates.
 */
export default function PersonTracker({ position, confidence, motion }) {
  const groupRef = useRef();
  const coreRef = useRef();
  const haloRef = useRef();
  const beamRef = useRef();
  const ringRef = useRef();

  const target = useMemo(() => new THREE.Vector3(position.x, 0, position.z), []);

  // Keep the target fresh when the estimate changes.
  target.set(position.x, 0, position.z);

  useFrame((state, dt) => {
    const g = groupRef.current;
    if (!g) return;
    const alpha = 1 - Math.exp(-dt * 7);
    g.position.lerp(target, alpha);

    const t = state.clock.elapsedTime;
    const pulse = 1 + 0.14 * Math.sin(t * 5.5) * (motion ? 1 : 0.35);
    const coreScale = pulse * (0.28 + confidence * 0.45);

    if (coreRef.current) coreRef.current.scale.setScalar(coreScale);
    if (haloRef.current) {
      haloRef.current.scale.setScalar(coreScale * 2.4);
      haloRef.current.material.opacity = 0.10 + confidence * 0.22;
    }
    if (beamRef.current) {
      beamRef.current.scale.y = 0.35 + confidence * 2.0;
      beamRef.current.material.opacity = 0.08 + confidence * 0.3;
    }
    if (ringRef.current) {
      ringRef.current.scale.setScalar(0.5 + confidence * 2.4 + 0.15 * Math.sin(t * 2.2));
      ringRef.current.rotation.z = t * 0.5;
      ringRef.current.material.opacity = 0.12 + confidence * 0.3;
    }
  });

  const visible = confidence > 0.01;

  return (
    <group ref={groupRef} visible={visible}>
      {/* confidence ring on the floor */}
      <mesh ref={ringRef} rotation-x={-Math.PI / 2} position={[0, 0.03, 0]}>
        <ringGeometry args={[0.9, 1, 48]} />
        <meshBasicMaterial
          color="#67e8f9"
          transparent
          opacity={0}
          depthWrite={false}
          blending={THREE.AdditiveBlending}
          side={THREE.DoubleSide}
        />
      </mesh>

      {/* vertical light beam */}
      <mesh ref={beamRef} position={[0, 0.9, 0]}>
        <cylinderGeometry args={[0.035, 0.05, 1.8, 10, 1, true]} />
        <meshBasicMaterial
          color="#22d3ee"
          transparent
          opacity={0}
          depthWrite={false}
          blending={THREE.AdditiveBlending}
          side={THREE.DoubleSide}
        />
      </mesh>

      {/* glow halo */}
      <mesh ref={haloRef} position={[0, 1.45, 0]}>
        <sphereGeometry args={[0.5, 20, 20]} />
        <meshBasicMaterial
          color="#22d3ee"
          transparent
          opacity={0}
          depthWrite={false}
          blending={THREE.AdditiveBlending}
        />
      </mesh>

      {/* bright core */}
      <mesh ref={coreRef} position={[0, 1.45, 0]}>
        <sphereGeometry args={[0.16, 20, 20]} />
        <meshBasicMaterial
          color="#aef3ff"
          emissive="#22d3ee"
          emissiveIntensity={2}
          toneMapped={false}
        />
      </mesh>
    </group>
  );
}

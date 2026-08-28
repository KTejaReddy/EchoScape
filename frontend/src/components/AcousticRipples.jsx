import { useRef } from "react";
import { useFrame } from "@react-three/fiber";
import * as THREE from "three";

const LIFETIME_MS = 2600;

function Ring({ ripple, onExpire }) {
  const ringRef = useRef();
  const ring2Ref = useRef();
  const verticalRef = useRef();

  useFrame(() => {
    const t = (performance.now() - ripple.born) / LIFETIME_MS;
    if (t >= 1) {
      onExpire?.(ripple.id);
      return;
    }
    const ease = 1 - Math.pow(1 - t, 3);
    const scale = 0.2 + ease * 5.2;
    const opacity = Math.pow(1 - t, 1.5);

    if (ringRef.current) {
      ringRef.current.scale.setScalar(scale);
      ringRef.current.material.opacity = opacity * 0.8;
    }
    if (ring2Ref.current) {
      ring2Ref.current.scale.setScalar(scale * 0.6);
      ring2Ref.current.material.opacity = opacity * 0.45;
    }
    if (verticalRef.current) {
      verticalRef.current.scale.set(scale * 0.5, 1 + t * 2.2, scale * 0.5);
      verticalRef.current.material.opacity = opacity * 0.22;
    }
  });

  return (
    <group position={[ripple.x, 0, ripple.z]}>
      <mesh ref={ringRef} rotation-x={-Math.PI / 2} position={[0, 0.045, 0]}>
        <ringGeometry args={[0.86, 1, 48]} />
        <meshBasicMaterial
          color="#3ee8ff"
          transparent
          opacity={0}
          depthWrite={false}
          blending={THREE.AdditiveBlending}
          side={THREE.DoubleSide}
        />
      </mesh>
      <mesh ref={ring2Ref} rotation-x={-Math.PI / 2} position={[0, 0.05, 0]}>
        <ringGeometry args={[0.93, 1, 40]} />
        <meshBasicMaterial
          color="#7dd3fc"
          transparent
          opacity={0}
          depthWrite={false}
          blending={THREE.AdditiveBlending}
          side={THREE.DoubleSide}
        />
      </mesh>
      <mesh ref={verticalRef} position={[0, 0.9, 0]}>
        <cylinderGeometry args={[1, 1, 1.8, 24, 1, true]} />
        <meshBasicMaterial
          color="#22d3ee"
          transparent
          opacity={0}
          depthWrite={false}
          blending={THREE.AdditiveBlending}
          side={THREE.DoubleSide}
        />
      </mesh>
    </group>
  );
}

export default function AcousticRipples({ ripples = [], onExpire }) {
  return (
    <group>
      {ripples.map((r) => (
        <Ring key={r.id} ripple={r} onExpire={onExpire} />
      ))}
    </group>
  );
}

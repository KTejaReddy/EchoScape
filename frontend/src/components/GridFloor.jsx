import { useEffect, useMemo, useRef } from "react";
import * as THREE from "three";
import { useFrame } from "@react-three/fiber";

const VERT = /* glsl */ `
  uniform float uTime;
  uniform vec4 uRipples[6];
  uniform float uRippleCount;
  varying vec3 vWorld;

  void main() {
    vec3 pos = position;
    float disp = 0.0;
    for (int i = 0; i < 6; i++) {
      if (float(i) >= uRippleCount) break;
      vec2 delta = pos.xz - uRipples[i].xy;
      float d = length(delta);
      float age = uRipples[i].z;   // 0..1
      float amp = uRipples[i].w;   // 0..1
      float wave = sin(d * 6.0 - age * 14.0) * exp(-d * 1.7) * (1.0 - age) * amp * 0.5;
      disp += wave;
    }
    pos.y += disp;
    vWorld = pos;
    gl_Position = projectionMatrix * modelViewMatrix * vec4(pos, 1.0);
  }
`;

const FRAG = /* glsl */ `
  uniform float uTime;
  uniform vec3 uPerson;
  uniform float uMotion;
  varying vec3 vWorld;

  void main() {
    vec3 p = vWorld;

    // Minor grid lines every 0.5 m, major every 2.5 m.
    vec2 g = abs(fract(p.xz / 0.5) - 0.5);
    float minor = 1.0 - smoothstep(0.46, 0.5, max(g.x, g.y));
    vec2 gm = abs(fract(p.xz / 2.5) - 0.5);
    float major = 1.0 - smoothstep(0.49, 0.5, max(gm.x, gm.y));

    // Grid brightens and "wakes up" near the estimated person position.
    float focus = 0.3 + 0.7 * smoothstep(5.0, 0.0, length(p.xz - uPerson.xz));

    // Breathing pulse so the grid feels alive even when idle.
    float breath = 0.75 + 0.25 * sin(uTime * 0.8);

    float intensity = (0.10 * minor + 0.28 * major + 0.22 * uMotion * minor) * focus * breath;
    vec3 col = vec3(0.10, 0.82, 0.95) * intensity;
    gl_FragColor = vec4(col, 1.0);
  }
`;

const MAX_RIPPLES = 6;

/**
 * Floor grid that distorts with ripple waves. `ripples` are
 * {id, x, z, born(ms)} — the shader receives them as vec4(x, z, age, amp).
 */
export default function GridFloor({ room, person, motion, ripples }) {
  const meshRef = useRef();
  const materialRef = useRef();

  const { width, depth } = room.room;

  const geometryArgs = useMemo(() => {
    const w = width + 2;
    const d = depth + 2;
    return [w, d, Math.max(24, Math.round(w / 0.25)), Math.max(24, Math.round(d / 0.25))];
  }, [width, depth]);

  useEffect(() => {
    const mat = materialRef.current;
    if (!mat) return;
    mat.uniforms.uPerson.value = new THREE.Vector3(person.x, 0, person.z);
    mat.uniforms.uMotion.value = motion ? 1 : 0;
  }, [person, motion]);

  useFrame((state, dt) => {
    const mat = materialRef.current;
    if (!mat) return;
    mat.uniforms.uTime.value += dt;

    const arr = mat.uniforms.uRipples.value;
    const now = performance.now();
    let count = 0;
    for (let i = 0; i < Math.min(ripples.length, MAX_RIPPLES); i++) {
      const r = ripples[ripples.length - 1 - i];
      const age = Math.min((now - r.born) / 2600, 1);
      arr[i].set(r.x, r.z, age, Math.min(Math.max(1 - age, 0), 1));
      count++;
    }
    for (let i = count; i < MAX_RIPPLES; i++) arr[i].set(0, 0, 1, 0);
    mat.uniforms.uRippleCount.value = count;
  });

  return (
    <mesh ref={meshRef} rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.02, 0]}>
      <planeGeometry args={geometryArgs} />
      <shaderMaterial
        ref={materialRef}
        vertexShader={VERT}
        fragmentShader={FRAG}
        transparent
        depthWrite={false}
        blending={THREE.AdditiveBlending}
        uniforms={{
          // 'opacity' is read unconditionally by three's refreshUniformsCommon.
          opacity: { value: 1.0 },
          uTime: { value: 0 },
          uRipples: {
            value: Array.from({ length: MAX_RIPPLES }, () => new THREE.Vector4(0, 0, 1, 0)),
          },
          uRippleCount: { value: 0 },
          uPerson: { value: new THREE.Vector3(0, 0, 0) },
          uMotion: { value: 0 },
        }}
      />
    </mesh>
  );
}

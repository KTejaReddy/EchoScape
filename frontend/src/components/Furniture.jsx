import { useMemo } from "react";
import { Text } from "@react-three/drei";

/* Shared stylised palette: dark bodies + cyan accents. */
const M = {
  body: { color: "#1b2436", roughness: 0.85, metalness: 0.05 },
  dark: { color: "#121a28", roughness: 0.9, metalness: 0.05 },
  wood: { color: "#3a3f4d", roughness: 0.8, metalness: 0.05 },
  accent: { color: "#22d3ee", emissive: "#0891b2", emissiveIntensity: 0.35, roughness: 0.5 },
  glow: { color: "#0e7490", emissive: "#22d3ee", emissiveIntensity: 0.9, roughness: 0.4 },
  glass: { color: "#67e8f9", transparent: true, opacity: 0.22, roughness: 0.1, metalness: 0.2 },
  soft: { color: "#243349", roughness: 0.95 },
};

function Box({ args, position, rotation = [0, 0, 0], mat = M.body, name }) {
  return (
    <mesh position={position} rotation={rotation} name={name}>
      <boxGeometry args={args} />
      <meshStandardMaterial {...mat} />
    </mesh>
  );
}

function Cyl({ args, position, rotation = [0, 0, 0], mat = M.body }) {
  return (
    <mesh position={position} rotation={rotation}>
      <cylinderGeometry args={args} />
      <meshStandardMaterial {...mat} />
    </mesh>
  );
}

/* ------------------------------------------------------------------ */
/* Individual furniture types                                           */
/* ------------------------------------------------------------------ */

function Bed({ o }) {
  const w = o.width, d = o.depth;
  return (
    <group>
      <Box args={[w, 0.35, d]} position={[0, 0.175, 0]} mat={M.wood} />
      <Box args={[w * 0.94, 0.18, d * 0.94]} position={[0, 0.44, 0]} mat={M.soft} />
      <Box args={[w * 0.98, 0.65, 0.12]} position={[0, 0.68, -d / 2 + 0.06]} mat={M.dark} />
      <Box args={[w * 0.32, 0.16, d * 0.3]} position={[-w * 0.22, 0.61, d * 0.22]} mat={M.soft} />
      <Box args={[w * 0.32, 0.16, d * 0.3]} position={[w * 0.22, 0.61, d * 0.22]} mat={M.soft} />
      <Box args={[w * 0.05, 0.35, d * 0.9]} position={[-w / 2 + 0.03, 0.35, 0]} mat={M.body} />
      <Box args={[w * 0.05, 0.35, d * 0.9]} position={[w / 2 - 0.03, 0.35, 0]} mat={M.body} />
    </group>
  );
}

function Sofa({ o }) {
  const w = o.width, d = o.depth;
  return (
    <group>
      <Box args={[w, 0.38, d]} position={[0, 0.19, 0]} mat={M.soft} />
      <Box args={[w, 0.55, 0.22]} position={[0, 0.55, -d / 2 + 0.11]} mat={M.soft} />
      <Box args={[0.22, 0.6, d * 0.92]} position={[-w / 2 + 0.11, 0.42, 0]} mat={M.soft} />
      <Box args={[0.22, 0.6, d * 0.92]} position={[w / 2 - 0.11, 0.42, 0]} mat={M.soft} />
      <Box args={[w * 0.42, 0.16, d * 0.7]} position={[-w * 0.24, 0.46, 0.1]} mat={M.soft} />
      <Box args={[w * 0.42, 0.16, d * 0.7]} position={[w * 0.24, 0.46, 0.1]} mat={M.soft} />
      <Box args={[w, 0.1, d * 0.3]} position={[0, 0.12, -d / 2 + 0.12]} mat={M.dark} />
    </group>
  );
}

function Table({ o }) {
  const w = o.width, d = o.depth;
  return (
    <group>
      <Box args={[w, 0.07, d]} position={[0, 0.74, 0]} mat={M.wood} />
      {[
        [-1, -1], [1, -1], [-1, 1], [1, 1],
      ].map(([sx, sz], i) => (
        <Box key={i} args={[0.06, 0.7, 0.06]} position={[(w / 2 - 0.08) * sx, 0.36, (d / 2 - 0.08) * sz]} mat={M.dark} />
      ))}
    </group>
  );
}

function Desk({ o }) {
  const w = o.width, d = o.depth;
  return (
    <group>
      <Box args={[w, 0.06, d]} position={[0, 0.73, 0]} mat={M.wood} />
      <Box args={[w, 0.5, 0.05]} position={[0, 0.48, d / 2 - 0.02]} mat={M.dark} />
      {[
        [-1, -1], [1, -1],
      ].map(([sx, sz], i) => (
        <Box key={i} args={[0.06, 0.7, 0.06]} position={[(w / 2 - 0.08) * sx, 0.36, (d / 2 - 0.08) * sz]} mat={M.dark} />
      ))}
      <Box args={[w * 0.4, 0.02, d * 0.8]} position={[0, 0.77, 0]} mat={M.accent} />
    </group>
  );
}

function Chair({ o }) {
  return (
    <group>
      <Box args={[0.46, 0.07, 0.46]} position={[0, 0.44, 0]} mat={M.soft} />
      <Box args={[0.46, 0.5, 0.07]} position={[0, 0.72, -0.2]} mat={M.soft} />
      <Box args={[0.46, 0.07, 0.3]} position={[0, 0.58, 0.1]} mat={M.soft} />
      {[
        [-1, -1], [1, -1], [-1, 1], [1, 1],
      ].map(([sx, sz], i) => (
        <Cyl key={i} args={[0.02, 0.02, 0.42]} position={[0.19 * sx, 0.21, 0.19 * sz]} mat={M.dark} />
      ))}
    </group>
  );
}

function Wardrobe({ o }) {
  const w = o.width, h = o.height, d = o.depth;
  return (
    <group>
      <Box args={[w, h, d]} position={[0, h / 2, 0]} mat={M.wood} />
      <Box args={[w * 0.48, h * 0.92, 0.02]} position={[-w * 0.25, h * 0.5, d / 2 + 0.011]} mat={M.body} />
      <Box args={[w * 0.48, h * 0.92, 0.02]} position={[w * 0.25, h * 0.5, d / 2 + 0.011]} mat={M.body} />
      <Box args={[w * 0.02, h * 0.55, 0.02]} position={[0, h * 0.35, d / 2 + 0.02]} mat={M.accent} />
      <Box args={[w * 0.02, h * 0.55, 0.02]} position={[-w * 0.25, h * 0.35, d / 2 + 0.021]} mat={M.accent} />
      <Box args={[w * 0.02, h * 0.55, 0.02]} position={[w * 0.25, h * 0.35, d / 2 + 0.021]} mat={M.accent} />
    </group>
  );
}

function Cabinet({ o }) {
  const w = o.width, h = o.height, d = o.depth;
  return (
    <group>
      <Box args={[w, h, d]} position={[0, h / 2, 0]} mat={M.wood} />
      <Box args={[w * 0.9, h * 0.85, 0.02]} position={[0, h * 0.48, d / 2 + 0.011]} mat={M.dark} />
      <Box args={[w * 0.02, h * 0.5, 0.02]} position={[0, h * 0.4, d / 2 + 0.02]} mat={M.accent} />
    </group>
  );
}

function Door({ o }) {
  const w = o.width, h = o.height;
  return (
    <group>
      {/* frame */}
      <Box args={[w + 0.24, h, 0.06]} position={[0, h / 2, 0]} mat={M.dark} />
      {/* open panel */}
      <Box args={[w, h - 0.1, 0.04]} position={[0, (h - 0.1) / 2 + 0.05, 0.06]} rotation={[0, -0.35, 0]} mat={M.wood} />
      <Box args={[w * 0.5, h * 0.35, 0.02]} position={[0, h * 0.62, 0.085]} mat={M.glass} />
    </group>
  );
}

function Window({ o }) {
  const w = o.width, h = o.height;
  return (
    <group>
      <Box args={[w, h, 0.08]} position={[0, h / 2, 0]} mat={M.dark} />
      <Box args={[w * 0.86, h * 0.86, 0.02]} position={[0, h / 2, 0.05]} mat={M.glass} />
      <Box args={[w * 0.02, h * 0.86, 0.04]} position={[0, h / 2, 0.05]} mat={M.body} />
      <Box args={[w * 0.86, 0.02, 0.04]} position={[0, h / 2, 0.05]} mat={M.body} />
    </group>
  );
}

function Television({ o }) {
  const w = o.width, h = o.height;
  return (
    <group>
      <Box args={[w, h, 0.06]} position={[0, h / 2 + 0.45, 0]} mat={M.dark} />
      <Box args={[w * 0.96, h * 0.96, 0.02]} position={[0, h / 2 + 0.45, 0.04]} mat={M.glow} />
      <Box args={[0.24, 0.05, 0.24]} position={[0, 0.42, 0]} mat={M.dark} />
      <Box args={[0.4, 0.4, 0.08]} position={[0, 0.2, 0]} mat={M.dark} />
    </group>
  );
}

function Shelf({ o }) {
  const w = o.width, h = o.height, d = o.depth;
  return (
    <group>
      <Box args={[0.06, h, d]} position={[-w / 2 + 0.03, h / 2, 0]} mat={M.wood} />
      <Box args={[0.06, h, d]} position={[w / 2 - 0.03, h / 2, 0]} mat={M.wood} />
      {[0.25, 0.5, 0.75].map((f, i) => (
        <Box key={i} args={[w, 0.05, d]} position={[0, h * f, 0]} mat={M.wood} />
      ))}
      <Box args={[w * 0.4, 0.02, d * 0.6]} position={[0, h * 0.62, 0]} mat={M.accent} />
    </group>
  );
}

function Plant({ o }) {
  return (
    <group>
      <Cyl args={[0.14, 0.11, 0.3, 12]} position={[0, 0.15, 0]} mat={M.dark} />
      <mesh position={[0, 0.62, 0]}>
        <icosahedronGeometry args={[0.34, 0]} />
        <meshStandardMaterial color="#2f7d4f" roughness={0.9} />
      </mesh>
      <mesh position={[0.14, 0.4, 0.1]}>
        <icosahedronGeometry args={[0.16, 0]} />
        <meshStandardMaterial color="#3d9160" roughness={0.9} />
      </mesh>
    </group>
  );
}

function Lamp({ o }) {
  const h = Math.min(o.height, 1.6);
  return (
    <group>
      <Cyl args={[0.16, 0.2, 0.04, 16]} position={[0, 0.02, 0]} mat={M.dark} />
      <Cyl args={[0.02, 0.02, h, 8]} position={[0, h / 2, 0]} mat={M.dark} />
      <Cyl args={[0.16, 0.12, 0.22, 20]} position={[0, h + 0.11, 0]} mat={M.glow} />
    </group>
  );
}

function Rug({ o }) {
  return <Box args={[o.width, 0.015, o.depth]} position={[0, 0.008, 0]} mat={{ color: "#12354a", roughness: 1, emissive: "#0e7490", emissiveIntensity: 0.12 }} />;
}

const RENDERERS = {
  bed: Bed,
  sofa: Sofa,
  table: Table,
  desk: Desk,
  chair: Chair,
  wardrobe: Wardrobe,
  cabinet: Cabinet,
  door: Door,
  window: Window,
  television: Television,
  shelf: Shelf,
  plant: Plant,
  lamp: Lamp,
  rug: Rug,
};

const LABEL_TYPES = new Set(["bed", "sofa", "desk", "wardrobe", "door", "window", "table"]);

export default function Furniture({ objects }) {
  const items = useMemo(() => objects ?? [], [objects]);
  return (
    <group>
      {items.map((o, i) => {
        const Renderer = RENDERERS[o.type];
        if (!Renderer) return null;
        return (
          <group key={`${o.type}-${i}`} position={[o.x, o.y, o.z]} rotation={[0, o.rotation || 0, 0]}>
            <Renderer o={o} />
            {LABEL_TYPES.has(o.type) && (
              <Text
                position={[0, (o.height || 1) + 0.35, 0]}
                fontSize={0.14}
                color="#8fb6d8"
                anchorX="center"
                anchorY="middle"
                letterSpacing={0.04}
              >
                {o.name}
              </Text>
            )}
          </group>
        );
      })}
    </group>
  );
}

import React, { Component, Suspense, useEffect, useMemo } from "react";
import { useGLTF } from "@react-three/drei";
import { staticFile } from "remotion";
import * as THREE from "three";
import type { V3 } from "../types";

const safeVec = (v?: V3, fallback: V3 = [0, 0, 0]): V3 =>
  Array.isArray(v) && v.length === 3 ? [Number(v[0]) || 0, Number(v[1]) || 0, Number(v[2]) || 0] : fallback;

const safeHex = (c?: string, fallback = "#3B4E6B"): string =>
  typeof c === "string" && c.trim() ? c.trim() : fallback;

const liftStructuralHex = (hex: string): string => {
  try {
    const c = new THREE.Color(hex);
    const lum = 0.299 * c.r + 0.587 * c.g + 0.114 * c.b;
    if (lum < 0.08) {
      c.lerp(new THREE.Color("#364A66"), 0.72);
      return "#" + c.getHexString();
    }
    if (lum < 0.14) {
      c.lerp(new THREE.Color("#425878"), 0.45);
      return "#" + c.getHexString();
    }
    return hex;
  } catch {
    return "#364A66";
  }
};

export const MatteBox: React.FC<{
  pos?: V3;
  rot?: V3;
  size?: V3;
  color?: string;
  emissive?: string;
  emissiveIntensity?: number;
  roughness?: number;
  metalness?: number;
  opacity?: number;
  edges?: boolean;
  edgeColor?: string;
}> = ({
  pos,
  rot,
  size = [1, 1, 1],
  color = "#3B4E6B",
  emissive,
  emissiveIntensity = 1.4,
  roughness = 0.42,
  metalness = 0.32,
  opacity = 1,
  edges = true,
  edgeColor = "#7DD3FC",
}) => {
  const s = safeVec(size, [1, 1, 1]);
  const sx = Math.max(0.01, s[0]);
  const sy = Math.max(0.01, s[1]);
  const sz = Math.max(0.01, s[2]);

  const { geo, edgeGeo } = useMemo(() => {
    const g = new THREE.BoxGeometry(sx, sy, sz);
    const e = new THREE.EdgesGeometry(g, 20);
    return { geo: g, edgeGeo: e };
  }, [sx, sy, sz]);

  useEffect(() => () => {
    geo.dispose();
    edgeGeo.dispose();
  }, [geo, edgeGeo]);

  const finalColor = emissive ? safeHex(color) : liftStructuralHex(safeHex(color));

  return (
    <group position={safeVec(pos)} rotation={safeVec(rot)}>
      <mesh geometry={geo}>
        <meshStandardMaterial
          color={finalColor}
          emissive={emissive ? safeHex(emissive) : "#000000"}
          emissiveIntensity={emissive ? emissiveIntensity : 0}
          roughness={roughness}
          metalness={metalness}
          transparent={opacity < 1}
          opacity={opacity}
        />
      </mesh>
      {edges && !emissive && (
        <lineSegments geometry={edgeGeo}>
          <lineBasicMaterial color={safeHex(edgeColor)} transparent opacity={0.44} />
        </lineSegments>
      )}
    </group>
  );
};

export const MatteCylinder: React.FC<{
  pos?: V3;
  rot?: V3;
  radiusTop?: number;
  radiusBottom?: number;
  height?: number;
  segments?: number;
  openEnded?: boolean;
  thetaStart?: number;
  thetaLength?: number;
  doubleSide?: boolean;
  color?: string;
  emissive?: string;
  emissiveIntensity?: number;
  roughness?: number;
  metalness?: number;
  edges?: boolean;
  edgeColor?: string;
}> = ({
  pos,
  rot,
  radiusTop = 0.5,
  radiusBottom = 0.5,
  height = 1,
  segments = 24,
  openEnded = false,
  thetaStart = 0,
  thetaLength = Math.PI * 2,
  doubleSide = false,
  color = "#475569",
  emissive,
  emissiveIntensity = 1.4,
  roughness = 0.36,
  metalness = 0.4,
  edges = true,
  edgeColor = "#93C5FD",
}) => {
  const { geo, edgeGeo } = useMemo(() => {
    const g = new THREE.CylinderGeometry(
      radiusTop,
      radiusBottom,
      height,
      segments,
      1,
      openEnded,
      thetaStart,
      thetaLength
    );
    const e = new THREE.EdgesGeometry(g, 24);
    return { geo: g, edgeGeo: e };
  }, [radiusTop, radiusBottom, height, segments, openEnded, thetaStart, thetaLength]);

  useEffect(() => () => {
    geo.dispose();
    edgeGeo.dispose();
  }, [geo, edgeGeo]);

  const finalColor = emissive ? safeHex(color) : liftStructuralHex(safeHex(color));

  return (
    <group position={safeVec(pos)} rotation={safeVec(rot)}>
      <mesh geometry={geo}>
        <meshStandardMaterial
          color={finalColor}
          emissive={emissive ? safeHex(emissive) : "#000000"}
          emissiveIntensity={emissive ? emissiveIntensity : 0}
          roughness={roughness}
          metalness={metalness}
          side={doubleSide ? THREE.DoubleSide : THREE.FrontSide}
        />
      </mesh>
      {edges && !emissive && (
        <lineSegments geometry={edgeGeo}>
          <lineBasicMaterial color={safeHex(edgeColor)} transparent opacity={0.44} />
        </lineSegments>
      )}
    </group>
  );
};

export const MatteSphere: React.FC<{
  pos?: V3;
  scale?: V3;
  radius?: number;
  color?: string;
  emissive?: string;
  emissiveIntensity?: number;
  roughness?: number;
  metalness?: number;
}> = ({
  pos,
  scale,
  radius = 0.5,
  color = "#64748B",
  emissive,
  emissiveIntensity = 1.5,
  roughness = 0.35,
  metalness = 0.3,
}) => (
  <mesh position={safeVec(pos)} scale={safeVec(scale, [1, 1, 1])}>
    <sphereGeometry args={[radius, 18, 16]} />
    <meshStandardMaterial
      color={emissive ? safeHex(color) : liftStructuralHex(safeHex(color))}
      emissive={emissive ? safeHex(emissive) : "#000000"}
      emissiveIntensity={emissive ? emissiveIntensity : 0}
      roughness={roughness}
      metalness={metalness}
    />
  </mesh>
);

export const MatteTorus: React.FC<{
  pos?: V3;
  rot?: V3;
  radius?: number;
  tube?: number;
  arc?: number;
  color?: string;
  emissive?: string;
  emissiveIntensity?: number;
}> = ({
  pos,
  rot,
  radius = 1,
  tube = 0.12,
  arc = Math.PI * 2,
  color = "#475569",
  emissive,
  emissiveIntensity = 1.5,
}) => (
  <mesh position={safeVec(pos)} rotation={safeVec(rot)}>
    <torusGeometry args={[radius, tube, 12, 28, arc]} />
    <meshStandardMaterial
      color={emissive ? safeHex(color) : liftStructuralHex(safeHex(color))}
      emissive={emissive ? safeHex(emissive) : "#000000"}
      emissiveIntensity={emissive ? emissiveIntensity : 0}
      roughness={0.35}
      metalness={0.45}
    />
  </mesh>
);

export const MatteCone: React.FC<{
  pos?: V3;
  rot?: V3;
  radius?: number;
  height?: number;
  segments?: number;
  color?: string;
  emissive?: string;
  emissiveIntensity?: number;
  edges?: boolean;
  edgeColor?: string;
}> = ({
  pos,
  rot,
  radius = 0.5,
  height = 1,
  segments = 20,
  color = "#475569",
  emissive,
  emissiveIntensity = 1.4,
  edges = true,
  edgeColor = "#93C5FD",
}) => {
  const { geo, edgeGeo } = useMemo(() => {
    const g = new THREE.ConeGeometry(radius, height, segments);
    const e = new THREE.EdgesGeometry(g, 24);
    return { geo: g, edgeGeo: e };
  }, [radius, height, segments]);

  useEffect(() => () => {
    geo.dispose();
    edgeGeo.dispose();
  }, [geo, edgeGeo]);

  return (
    <group position={safeVec(pos)} rotation={safeVec(rot)}>
      <mesh geometry={geo}>
        <meshStandardMaterial
          color={emissive ? safeHex(color) : liftStructuralHex(safeHex(color))}
          emissive={emissive ? safeHex(emissive) : "#000000"}
          emissiveIntensity={emissive ? emissiveIntensity : 0}
          roughness={0.4}
          metalness={0.35}
        />
      </mesh>
      {edges && !emissive && (
        <lineSegments geometry={edgeGeo}>
          <lineBasicMaterial color={safeHex(edgeColor)} transparent opacity={0.44} />
        </lineSegments>
      )}
    </group>
  );
};

export const GlassShell: React.FC<{
  pos?: V3;
  rot?: V3;
  shape?: "box" | "cylinder";
  size?: V3;
  radius?: number;
  height?: number;
  color?: string;
  edgeColor?: string;
  opacity?: number;
}> = ({
  pos,
  rot,
  shape = "box",
  size = [2, 2, 2],
  radius = 1,
  height = 2,
  color = "#38BDF8",
  edgeColor = "#7DD3FC",
  opacity = 0.22,
}) => {
  const s = safeVec(size, [2, 2, 2]);
  const { geo, edgeGeo } = useMemo(() => {
    const g =
      shape === "cylinder"
        ? new THREE.CylinderGeometry(radius, radius, height, 24)
        : new THREE.BoxGeometry(s[0], s[1], s[2]);
    const e = new THREE.EdgesGeometry(g, 24);
    return { geo: g, edgeGeo: e };
  }, [shape, radius, height, s[0], s[1], s[2]]);

  useEffect(() => () => {
    geo.dispose();
    edgeGeo.dispose();
  }, [geo, edgeGeo]);

  return (
    <group position={safeVec(pos)} rotation={safeVec(rot)}>
      <mesh geometry={geo}>
        <meshStandardMaterial
          color={safeHex(color)}
          transparent
          opacity={opacity}
          roughness={0.15}
          metalness={0.15}
          depthWrite={false}
        />
      </mesh>
      <lineSegments geometry={edgeGeo}>
        <lineBasicMaterial color={safeHex(edgeColor)} transparent opacity={0.7} />
      </lineSegments>
    </group>
  );
};

export const HardwareRack: React.FC<{
  pos?: V3;
  rot?: V3;
  size?: V3;
  bays?: number;
  accentHex?: string;
  frame: number;
}> = ({ pos, rot, size = [1.0, 2.2, 1.0], bays = 6, accentHex = "#22D3EE", frame }) => {
  const [w, h, d] = safeVec(size, [1.0, 2.2, 1.0]);
  const safeBays = Math.max(3, Math.min(10, Math.round(bays)));
  const bayStep = (h * 0.78) / safeBays;

  return (
    <group position={safeVec(pos)} rotation={safeVec(rot)}>
      <MatteBox pos={[0, 0, 0]} size={[w, h, d]} color="#2F4059" edgeColor={accentHex} />
      <MatteBox pos={[0, 0, d * 0.04]} size={[w * 0.86, h * 0.88, d * 0.94]} color="#1E293B" edges={false} />
      {[-w * 0.44, w * 0.44].map((rx, ri) => (
        <MatteBox key={ri} pos={[rx, 0, d * 0.48]} size={[w * 0.08, h * 0.96, 0.05]} color="#64748B" />
      ))}
      {Array.from({ length: safeBays }).map((_, bi) => {
        const by = -h * 0.36 + bi * bayStep;
        const pulse = 0.7 + 0.9 * Math.max(0, Math.sin((frame / 30) * 4.5 - bi * 0.6));
        return (
          <group key={bi} position={[0, by, d * 0.47]}>
            <MatteBox size={[w * 0.78, bayStep * 0.68, 0.08]} color="#475569" edgeColor="#94A3B8" />
            <MatteBox
              pos={[-w * 0.25, 0, 0.05]}
              size={[w * 0.22, bayStep * 0.22, 0.02]}
              color={accentHex}
              emissive={accentHex}
              emissiveIntensity={pulse}
              edges={false}
            />
          </group>
        );
      })}
      <MatteBox pos={[0, h * 0.52, 0]} size={[w * 0.84, 0.08, d * 0.84]} color="#64748B" edgeColor={accentHex} />
    </group>
  );
};

export const DataHallBuilding: React.FC<{
  pos?: V3;
  size?: V3;
  accentHex?: string;
  progress: number;
  frame: number;
}> = ({ pos, size = [3.2, 1.5, 2.2], accentHex = "#22D3EE", progress, frame }) => {
  const [w, h, d] = safeVec(size, [3.2, 1.5, 2.2]);
  const span = 0.45;
  const raw = Math.max(0, Math.min(1, (progress - 0.18) / span));
  const lift = raw * raw * (3 - 2 * raw) * 1.15;

  return (
    <group position={safeVec(pos)}>
      {/* Concrete Slab Base */}
      <MatteBox pos={[0, -h * 0.52, 0]} size={[w * 1.12, 0.16, d * 1.15]} color="#334155" edgeColor={accentHex} />
      {/* 4 Ribbed Concrete Walls (Open Top for Roof Cutaway) */}
      <MatteBox pos={[0, 0, -d * 0.48]} size={[w, h, 0.14]} color="#475569" edgeColor={accentHex} />
      <MatteBox pos={[0, 0, d * 0.48]} size={[w, h, 0.14]} color="#3B4E6B" edgeColor={accentHex} />
      <MatteBox pos={[-w * 0.48, 0, 0]} size={[0.14, h, d]} color="#475569" edgeColor={accentHex} />
      <MatteBox pos={[w * 0.48, 0, 0]} size={[0.14, h, d]} color="#475569" edgeColor={accentHex} />
      {/* Vertical Concrete Pilaster Buttresses */}
      {[-w * 0.3, 0, w * 0.3].map((px, i) => (
        <MatteBox key={i} pos={[px, 0, d * 0.53]} size={[0.18, h * 1.02, 0.1]} color="#64748B" edgeColor={accentHex} />
      ))}
      {/* Glowing Internal Racks Revealed Inside */}
      {[-w * 0.25, 0, w * 0.25].map((rx, ri) => (
        <HardwareRack key={ri} pos={[rx, -0.05, 0]} size={[w * 0.2, h * 0.82, d * 0.65]} bays={4} accentHex={accentHex} frame={frame} />
      ))}
      {/* Lifting Cutaway Roof Slab + Rooftop Chillers */}
      <group position={[0, h * 0.54 + lift, 0]}>
        <MatteBox size={[w * 1.04, 0.14, d * 1.04]} color="#64748B" edgeColor={accentHex} />
        {[-w * 0.28, 0, w * 0.28].map((cx, ci) => (
          <MatteBox key={ci} pos={[cx, 0.16, 0]} size={[0.45, 0.2, d * 0.55]} color="#3B4E6B" edgeColor={accentHex} />
        ))}
      </group>
    </group>
  );
};

export const CitySkylineBlock: React.FC<{
  pos?: V3;
  scale?: number;
  accentHex?: string;
  frame: number;
}> = ({ pos, scale = 1, accentHex = "#F59E0B", frame }) => {
  const towers: { x: number; z: number; w: number; h: number; d: number }[] = [
    { x: -0.9, z: -0.4, w: 0.42, h: 1.5, d: 0.42 },
    { x: -0.35, z: 0.1, w: 0.5, h: 2.2, d: 0.5 },
    { x: 0.25, z: -0.25, w: 0.46, h: 1.85, d: 0.46 },
    { x: 0.85, z: 0.2, w: 0.4, h: 1.3, d: 0.4 },
    { x: -0.55, z: 0.65, w: 0.36, h: 1.1, d: 0.36 },
    { x: 0.45, z: 0.65, w: 0.44, h: 1.6, d: 0.44 },
  ];

  return (
    <group position={safeVec(pos)} scale={[scale, scale, scale]}>
      <MatteBox pos={[0, -0.82, 0]} size={[2.7, 0.14, 2.0]} color="#2F4059" edgeColor={accentHex} />
      {towers.map((t, i) => {
        const flicker = 1.0 + 0.45 * Math.sin((frame / 30) * 3.0 + i * 1.1);
        return (
          <group key={i} position={[t.x, -0.75 + t.h * 0.5, t.z]}>
            <MatteBox size={[t.w, t.h, t.d]} color="#3B4E6B" edgeColor="#7DD3FC" />
            {[0.25, 0, -0.25].map((wy, wi) => (
              <MatteBox
                key={wi}
                pos={[0, wy * t.h, t.d * 0.51]}
                size={[t.w * 0.72, 0.09, 0.02]}
                color={accentHex}
                emissive={accentHex}
                emissiveIntensity={flicker}
                edges={false}
              />
            ))}
          </group>
        );
      })}
    </group>
  );
};

export const PowerPylon: React.FC<{
  pos?: V3;
  height?: number;
  accentHex?: string;
}> = ({ pos, height = 2.4, accentHex = "#F59E0B" }) => (
  <group position={safeVec(pos)}>
    <MatteBox pos={[0, -height * 0.48, 0]} size={[0.9, 0.14, 0.9]} color="#334155" edgeColor={accentHex} />
    <MatteCylinder
      pos={[0, 0, 0]}
      radiusTop={0.14}
      radiusBottom={0.44}
      height={height}
      segments={4}
      color="#64748B"
      edgeColor={accentHex}
    />
    {[height * 0.2, height * 0.38].map((cy, ci) => {
      const span = ci === 0 ? 1.55 : 1.15;
      return (
        <group key={ci} position={[0, cy, 0]}>
          <MatteBox size={[span, 0.08, 0.14]} color="#94A3B8" edgeColor={accentHex} />
          {[-span * 0.45, span * 0.45].map((ix, ii) => (
            <MatteCylinder
              key={ii}
              pos={[ix, -0.14, 0]}
              radiusTop={0.05}
              radiusBottom={0.07}
              height={0.22}
              color={accentHex}
              emissive={accentHex}
              emissiveIntensity={1.6}
              edges={false}
            />
          ))}
        </group>
      );
    })}
  </group>
);

export const CoolingTower: React.FC<{
  pos?: V3;
  radius?: number;
  height?: number;
  accentHex?: string;
  cutaway?: boolean;
  frame: number;
}> = ({ pos, radius = 0.95, height = 2.2, accentHex = "#38BDF8", cutaway = true, frame }) => {
  const segH = height / 3;
  const spin = (frame / 30) * 5.0;

  return (
    <group position={safeVec(pos)}>
      <MatteCylinder pos={[0, -height * 0.48, 0]} radiusTop={radius * 1.15} radiusBottom={radius * 1.18} height={0.14} color="#334155" edgeColor={accentHex} />
      {[
        { y: -segH, rTop: radius * 0.85, rBot: radius * 1.08 },
        { y: 0, rTop: radius * 0.72, rBot: radius * 0.85 },
        { y: segH, rTop: radius * 0.8, rBot: radius * 0.72 },
      ].map((seg, i) => (
        <MatteCylinder
          key={i}
          pos={[0, seg.y, 0]}
          radiusTop={seg.rTop}
          radiusBottom={seg.rBot}
          height={segH + 0.02}
          openEnded={true}
          thetaStart={cutaway ? 0.55 : 0}
          thetaLength={cutaway ? Math.PI * 1.38 : Math.PI * 2}
          doubleSide={true}
          color="#475569"
          edgeColor={accentHex}
        />
      ))}
      <MatteCylinder pos={[0, -height * 0.4, 0]} radiusTop={radius * 0.96} radiusBottom={radius * 0.96} height={0.14} color={accentHex} emissive={accentHex} emissiveIntensity={1.4} edges={false} />
      <group position={[0, -height * 0.12, 0]} rotation={[0, spin, 0]}>
        <MatteBox size={[radius * 1.25, 0.06, 0.16]} color="#CBD5E1" edgeColor={accentHex} />
        <MatteBox size={[0.16, 0.06, radius * 1.25]} color="#CBD5E1" edgeColor={accentHex} />
      </group>
      <RisingParticles origin={[0, height * 0.45, 0]} spread={radius * 0.55} height={1.4} count={8} size={0.16} color="#E2E8F0" speed={0.45} frame={frame} />
    </group>
  );
};

export const BatteryContainer: React.FC<{
  pos?: V3;
  size?: V3;
  accentHex?: string;
  frame: number;
}> = ({ pos, size = [1.5, 1.3, 1.1], accentHex = "#10B981", frame }) => {
  const [w, h, d] = safeVec(size, [1.5, 1.3, 1.1]);
  const charge = 0.35 + 0.65 * (0.5 + 0.5 * Math.sin((frame / 30) * 2.2));
  return (
    <group position={safeVec(pos)}>
      <MatteBox size={[w, h, d]} color="#475569" edgeColor={accentHex} />
      <MatteBox pos={[0, h * 0.55, 0]} size={[w * 0.72, 0.14, d * 0.72]} color="#64748B" edgeColor={accentHex} />
      {[-w * 0.25, 0, w * 0.25].map((vx, i) => (
        <MatteBox key={i} pos={[vx, 0.05, d * 0.51]} size={[w * 0.14, h * 0.65, 0.03]} color="#2B3B52" />
      ))}
      <MatteBox
        pos={[w * 0.38, -h * 0.38 + charge * h * 0.38, d * 0.52]}
        size={[0.14, Math.max(0.14, charge * h * 0.75), 0.04]}
        color={accentHex}
        emissive={accentHex}
        emissiveIntensity={1.9}
        edges={false}
      />
    </group>
  );
};

export const FinnedHousing: React.FC<{
  pos?: V3;
  rot?: V3;
  radius?: number;
  height?: number;
  finCount?: number;
  color?: string;
  accentHex?: string;
  cutaway?: boolean;
  frame: number;
}> = ({
  pos,
  rot,
  radius = 0.9,
  height = 1.8,
  finCount = 8,
  color = "#3B4E6B",
  accentHex = "#22D3EE",
  cutaway = false,
  frame,
}) => {
  const safeFins = Math.max(4, Math.min(12, Math.round(finCount)));
  const pulse = 1.2 + Math.sin((frame / 30) * 3.5) * 0.35;

  return (
    <group position={safeVec(pos)} rotation={safeVec(rot)}>
      <MatteCylinder pos={[0, height * 0.48, 0]} radiusTop={radius * 1.18} radiusBottom={radius * 1.18} height={0.14} color="#64748B" edgeColor={accentHex} />
      <MatteCylinder pos={[0, -height * 0.48, 0]} radiusTop={radius * 1.18} radiusBottom={radius * 1.18} height={0.14} color="#64748B" edgeColor={accentHex} />
      {cutaway ? (
        <>
          <MatteCylinder pos={[0, 0, 0]} radiusTop={radius} radiusBottom={radius} height={height * 0.9} thetaStart={0.5} thetaLength={Math.PI * 1.35} doubleSide={true} color={color} edgeColor={accentHex} />
          <GlassShell pos={[0, 0, 0]} shape="cylinder" radius={radius * 0.96} height={height * 0.88} color={accentHex} edgeColor={accentHex} opacity={0.18} />
        </>
      ) : (
        <MatteCylinder pos={[0, 0, 0]} radiusTop={radius} radiusBottom={radius} height={height * 0.9} color={color} edgeColor={accentHex} />
      )}
      <MatteCylinder pos={[0, 0, 0]} radiusTop={radius * 0.45} radiusBottom={radius * 0.45} height={height * 0.78} color={accentHex} emissive={accentHex} emissiveIntensity={pulse} edges={false} />
      {Array.from({ length: safeFins }).map((_, fi) => {
        const a = (fi / safeFins) * Math.PI * 2;
        if (cutaway && a > 4.6 && a < 6.1) return null;
        return (
          <MatteBox
            key={fi}
            pos={[Math.cos(a) * radius * 1.02, 0, Math.sin(a) * radius * 1.02]}
            rot={[0, -a, 0]}
            size={[0.24, height * 0.82, 0.05]}
            color="#475569"
            edgeColor="#94A3B8"
          />
        );
      })}
    </group>
  );
};

export const PipeConduit: React.FC<{
  points: V3[];
  tubeRadius?: number;
  pipeColor?: string;
  fluidColor?: string;
  flangeCount?: number;
  count?: number;
  speed?: number;
  frame: number;
}> = ({
  points,
  tubeRadius = 0.11,
  pipeColor = "#475569",
  fluidColor = "#22D3EE",
  flangeCount = 4,
  count = 6,
  speed = 0.75,
  frame,
}) => {
  const safePts = useMemo(() => {
    const valid = Array.isArray(points) && points.length >= 2 ? points : [[-2, 0, 0] as V3, [2, 0, 0] as V3];
    return valid.map((p) => {
      const sv = safeVec(p);
      return new THREE.Vector3(sv[0], sv[1], sv[2]);
    });
  }, [points]);

  const curve = useMemo(() => new THREE.CatmullRomCurve3(safePts), [safePts]);

  const flanges = useMemo(() => {
    const fCount = Math.max(2, Math.min(8, Math.round(flangeCount)));
    const up = new THREE.Vector3(0, 1, 0);
    return Array.from({ length: fCount }).map((_, idx) => {
      const u = (idx + 0.5) / fCount;
      const pt = curve.getPoint(u);
      const tangent = curve.getTangent(u).normalize();
      const quat = new THREE.Quaternion().setFromUnitVectors(up, tangent);
      const euler = new THREE.Euler().setFromQuaternion(quat);
      return {
        pos: [pt.x, pt.y, pt.z] as V3,
        rot: [euler.x, euler.y, euler.z] as V3,
      };
    });
  }, [curve, flangeCount]);

  const t = (frame / 30) * speed;
  const safeCount = Math.max(2, Math.min(18, Math.round(count)));

  return (
    <group>
      <mesh>
        <tubeGeometry args={[curve, 40, tubeRadius, 12, false]} />
        <meshStandardMaterial color={safeHex(pipeColor)} transparent opacity={0.34} roughness={0.22} metalness={0.4} depthWrite={false} />
      </mesh>
      <mesh>
        <tubeGeometry args={[curve, 40, tubeRadius * 0.28, 8, false]} />
        <meshStandardMaterial color={safeHex(fluidColor)} emissive={safeHex(fluidColor)} emissiveIntensity={0.65} />
      </mesh>
      {flanges.map((fl, fi) => (
        <MatteCylinder key={fi} pos={fl.pos} rot={fl.rot} radiusTop={tubeRadius * 1.45} radiusBottom={tubeRadius * 1.45} height={0.07} color="#64748B" edgeColor={fluidColor} />
      ))}
      {Array.from({ length: safeCount }).map((_, idx) => {
        const u = ((t + idx / safeCount) % 1 + 1) % 1;
        const pt = curve.getPoint(u);
        return (
          <mesh key={idx} position={[pt.x, pt.y, pt.z]}>
            <sphereGeometry args={[tubeRadius * 0.68, 10, 10]} />
            <meshStandardMaterial color={safeHex(fluidColor)} emissive={safeHex(fluidColor)} emissiveIntensity={2.1} />
          </mesh>
        );
      })}
    </group>
  );
};

export const HeatSinkArray: React.FC<{
  pos?: V3;
  rot?: V3;
  size?: V3;
  finCount?: number;
  color?: string;
  pipeColor?: string;
  glowColor?: string;
}> = ({
  pos,
  rot,
  size = [1.8, 0.7, 1.4],
  finCount = 8,
  color = "#64748B",
  pipeColor = "#D97706",
  glowColor = "#22D3EE",
}) => {
  const [w, h, d] = safeVec(size, [1.8, 0.7, 1.4]);
  const safeFins = Math.max(4, Math.min(14, Math.round(finCount)));
  const step = w / safeFins;

  return (
    <group position={safeVec(pos)} rotation={safeVec(rot)}>
      <MatteBox pos={[0, -h * 0.36, 0]} size={[w, h * 0.24, d]} color={pipeColor} edgeColor="#FBBF24" />
      {Array.from({ length: safeFins }).map((_, fi) => {
        const fx = -w * 0.45 + fi * step;
        return (
          <MatteBox key={fi} pos={[fx, h * 0.08, 0]} size={[step * 0.35, h * 0.72, d * 0.94]} color={color} edgeColor={glowColor} />
        );
      })}
      {[-d * 0.25, d * 0.25].map((pz, pi) => (
        <MatteCylinder key={pi} pos={[0, h * 0.04, pz]} rot={[0, 0, Math.PI / 2]} radiusTop={0.07} radiusBottom={0.07} height={w * 1.12} color={pipeColor} edgeColor="#FDE68A" />
      ))}
    </group>
  );
};

export const SpinGroup: React.FC<{
  pos?: V3;
  rot?: V3;
  axis?: "x" | "y" | "z";
  speed?: number;
  frame: number;
  children?: React.ReactNode;
}> = ({ pos, rot, axis = "y", speed = 1, frame, children }) => {
  const base = safeVec(rot);
  const delta = (frame / 30) * speed;
  const finalRot: V3 = [
    base[0] + (axis === "x" ? delta : 0),
    base[1] + (axis === "y" ? delta : 0),
    base[2] + (axis === "z" ? delta : 0),
  ];
  return (
    <group position={safeVec(pos)} rotation={finalRot}>
      {children}
    </group>
  );
};

export const BobGroup: React.FC<{
  pos?: V3;
  rot?: V3;
  axis?: "x" | "y" | "z";
  amp?: number;
  speed?: number;
  phase?: number;
  frame: number;
  children?: React.ReactNode;
}> = ({ pos, rot, axis = "y", amp = 0.15, speed = 1.5, phase = 0, frame, children }) => {
  const base = safeVec(pos);
  const delta = Math.sin((frame / 30) * speed + phase) * amp;
  const finalPos: V3 = [
    base[0] + (axis === "x" ? delta : 0),
    base[1] + (axis === "y" ? delta : 0),
    base[2] + (axis === "z" ? delta : 0),
  ];
  return (
    <group position={finalPos} rotation={safeVec(rot)}>
      {children}
    </group>
  );
};

export const RevealSlideGroup: React.FC<{
  startPos?: V3;
  endPos?: V3;
  startScale?: number;
  endScale?: number;
  progress: number;
  startAt?: number;
  endAt?: number;
  children?: React.ReactNode;
}> = ({
  startPos = [0, 0, 0],
  endPos = [0, 1.5, 0],
  startScale = 1,
  endScale = 1,
  progress,
  startAt = 0.15,
  endAt = 0.65,
  children,
}) => {
  const span = Math.max(0.01, endAt - startAt);
  const raw = Math.max(0, Math.min(1, (progress - startAt) / span));
  const t = raw * raw * (3 - 2 * raw);
  const s = safeVec(startPos);
  const e = safeVec(endPos, [0, 1.5, 0]);
  const sc = startScale + (endScale - startScale) * t;
  return (
    <group
      position={[s[0] + (e[0] - s[0]) * t, s[1] + (e[1] - s[1]) * t, s[2] + (e[2] - s[2]) * t]}
      scale={[sc, sc, sc]}
    >
      {children}
    </group>
  );
};

export const FlowStream: React.FC<{
  points: V3[];
  tubeRadius?: number;
  tubeColor?: string;
  particleColor?: string;
  particleSize?: number;
  count?: number;
  speed?: number;
  frame: number;
}> = ({
  points,
  tubeRadius = 0.08,
  tubeColor = "#3B4E6B",
  particleColor = "#22D3EE",
  particleSize = 0.09,
  count = 6,
  speed = 0.7,
  frame,
}) => (
  <PipeConduit
    points={points}
    tubeRadius={Math.max(tubeRadius, particleSize * 1.15)}
    pipeColor={tubeColor}
    fluidColor={particleColor}
    flangeCount={3}
    count={count}
    speed={speed}
    frame={frame}
  />
);

export const RisingParticles: React.FC<{
  origin?: V3;
  spread?: number;
  height?: number;
  count?: number;
  size?: number;
  color?: string;
  speed?: number;
  frame: number;
}> = ({
  origin = [0, 0, 0],
  spread = 0.75,
  height = 2.0,
  count = 8,
  size = 0.1,
  color = "#F97316",
  speed = 0.45,
  frame,
}) => {
  const o = safeVec(origin);
  const t = (frame / 30) * speed;
  const safeCount = Math.max(1, Math.min(16, Math.round(count)));

  return (
    <group>
      {Array.from({ length: safeCount }).map((_, i) => {
        const life = ((t + i / safeCount) % 1 + 1) % 1;
        const angle = i * 2.3 + t * 0.8;
        const r = 0.12 + life * spread;
        const s = Math.max(0.25, 1.0 - life * 0.65);
        return (
          <mesh
            key={i}
            position={[o[0] + Math.cos(angle) * r, o[1] + life * height, o[2] + Math.sin(angle) * r]}
            scale={[s, s, s]}
          >
            <sphereGeometry args={[size, 10, 10]} />
            <meshStandardMaterial
              color={safeHex(color)}
              emissive={safeHex(color)}
              emissiveIntensity={1.6 * (1 - life * 0.5)}
            />
          </mesh>
        );
      })}
    </group>
  );
};

export const OrbitRing: React.FC<{
  center?: V3;
  radius?: number;
  count?: number;
  size?: number;
  color?: string;
  speed?: number;
  tilt?: V3;
  frame: number;
}> = ({
  center = [0, 0, 0],
  radius = 1.6,
  count = 8,
  size = 0.09,
  color = "#22D3EE",
  speed = 0.8,
  tilt = [0, 0, 0],
  frame,
}) => {
  const t = (frame / 30) * speed;
  const safeCount = Math.max(1, Math.min(18, Math.round(count)));
  return (
    <group position={safeVec(center)} rotation={safeVec(tilt)}>
      <MatteTorus pos={[0, 0, 0]} rot={[Math.PI / 2, 0, 0]} radius={radius} tube={0.03} color="#475569" />
      {Array.from({ length: safeCount }).map((_, i) => {
        const a = t + (i / safeCount) * Math.PI * 2;
        return (
          <mesh key={i} position={[Math.cos(a) * radius, 0, Math.sin(a) * radius]}>
            <sphereGeometry args={[size, 10, 10]} />
            <meshStandardMaterial color={safeHex(color)} emissive={safeHex(color)} emissiveIntensity={1.9} />
          </mesh>
        );
      })}
    </group>
  );
};

class GlbErrorBoundary extends Component<{ children: React.ReactNode }, { err: boolean }> {
  constructor(props: { children: React.ReactNode }) {
    super(props);
    this.state = { err: false };
  }
  static getDerivedStateFromError() {
    return { err: true };
  }
  render() {
    return this.state.err ? null : this.props.children;
  }
}

const GlbInner: React.FC<{ file: string; pos?: V3; rot?: V3; scale?: number; spinSpeed?: number; frame: number }> = ({
  file,
  pos,
  rot,
  scale = 1,
  spinSpeed = 0.35,
  frame,
}) => {
  const { scene } = useGLTF(staticFile(`models/${file}`));
  const cloned = useMemo(() => scene.clone(), [scene]);
  const r = safeVec(rot);
  return (
    <group position={safeVec(pos)} rotation={[r[0], r[1] + (frame / 30) * spinSpeed, r[2]]} scale={[scale, scale, scale]}>
      <primitive object={cloned} />
    </group>
  );
};

export const GlbModel: React.FC<{
  file: string;
  pos?: V3;
  rot?: V3;
  scale?: number;
  spinSpeed?: number;
  frame: number;
}> = (props) => (
  <GlbErrorBoundary>
    <Suspense fallback={null}>
      <GlbInner {...props} />
    </Suspense>
  </GlbErrorBoundary>
);

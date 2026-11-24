import React, { useLayoutEffect, useMemo } from "react";
import { ThreeCanvas } from "@remotion/three";
import { useThree } from "@react-three/fiber";
import { interpolateColors, useCurrentFrame, useVideoConfig } from "remotion";
import { SCENE_REGISTRY } from "../generated/SceneRegistry";
import type { DocumentaryPlan, DocumentaryScene } from "../types";

function smoothstep(edge0: number, edge1: number, x: number): number {
  const t = Math.max(0, Math.min(1, (x - edge0) / Math.max(1e-6, edge1 - edge0)));
  return t * t * (3 - 2 * t);
}

function lerp(a: number, b: number, t: number): number {
  return a + (b - a) * t;
}

function sampleSceneCamera(
  scene: DocumentaryScene,
  tSec: number,
  frame: number,
  isVertical: boolean
): { pos: [number, number, number]; look: [number, number, number] } {
  const beats = scene.beats;
  if (!beats || beats.length === 0) {
    return {
      pos: [scene.worldPos[0] + 3.8, scene.worldPos[1] + 2.0, scene.worldPos[2] + 4.3],
      look: [scene.worldPos[0], scene.worldPos[1] + 0.3, scene.worldPos[2]],
    };
  }

  let bIdx = beats.findIndex((b) => tSec >= b.startSec && tSec <= b.endSec);
  if (bIdx === -1) bIdx = beats.length - 1;

  const currBeat = beats[bIdx];
  const nextBeat = beats[Math.min(beats.length - 1, bIdx + 1)];
  const bDur = Math.max(0.1, currBeat.endSec - currBeat.startSec);
  const localU = Math.max(0, Math.min(1, (tSec - currBeat.startSec) / bDur));
  const glideU = smoothstep(0.15, 0.95, localU);

  const driftX = Math.sin(frame * 0.02) * 0.11;
  const driftY = Math.cos(frame * 0.016) * 0.07;
  const pull = isVertical ? 1.15 : 1.0;

  return {
    pos: [
      scene.worldPos[0] + lerp(currBeat.cameraOffset[0], nextBeat.cameraOffset[0], glideU) * pull + driftX,
      scene.worldPos[1] + lerp(currBeat.cameraOffset[1], nextBeat.cameraOffset[1], glideU) + driftY,
      scene.worldPos[2] + lerp(currBeat.cameraOffset[2], nextBeat.cameraOffset[2], glideU) * pull,
    ],
    look: [
      scene.worldPos[0] + lerp(currBeat.lookOffset[0], nextBeat.lookOffset[0], glideU),
      scene.worldPos[1] + lerp(currBeat.lookOffset[1], nextBeat.lookOffset[1], glideU),
      scene.worldPos[2] + lerp(currBeat.lookOffset[2], nextBeat.lookOffset[2], glideU),
    ],
  };
}

interface CameraState {
  camPos: [number, number, number];
  lookAt: [number, number, number];
  bgHex: string;
  accentHex: string;
}

function computeContinuousCamera(
  plan: DocumentaryPlan,
  tSec: number,
  frame: number,
  isVertical: boolean
): CameraState {
  const scenes = plan.scenes;
  if (scenes.length === 0) {
    return { camPos: [0, 2, 5], lookAt: [0, 0.25, 0], bgHex: "#101B2E", accentHex: "#22D3EE" };
  }

  let activeIdx = scenes.findIndex((s) => tSec >= s.startSec && tSec <= s.endSec);
  if (activeIdx === -1) activeIdx = scenes.length - 1;

  const current = scenes[activeIdx];
  const currSample = sampleSceneCamera(current, tSec, frame, isVertical);
  const halfWin = isVertical ? 0.75 : 0.9;

  if (activeIdx < scenes.length - 1) {
    const distToEnd = current.endSec - tSec;
    if (distToEnd <= halfWin) {
      const next = scenes[activeIdx + 1];
      const nextSample = sampleSceneCamera(next, tSec, frame, isVertical);
      const blend = smoothstep(0, 1, (halfWin - distToEnd) / (halfWin * 2));
      return {
        camPos: [
          lerp(currSample.pos[0], nextSample.pos[0], blend),
          lerp(currSample.pos[1], nextSample.pos[1], blend),
          lerp(currSample.pos[2], nextSample.pos[2], blend),
        ],
        lookAt: [
          lerp(currSample.look[0], nextSample.look[0], blend),
          lerp(currSample.look[1], nextSample.look[1], blend),
          lerp(currSample.look[2], nextSample.look[2], blend),
        ],
        bgHex: interpolateColors(blend, [0, 1], [current.bgHex, next.bgHex]),
        accentHex: interpolateColors(blend, [0, 1], [current.accentHex, next.accentHex]),
      };
    }
  }

  if (activeIdx > 0) {
    const distFromStart = tSec - current.startSec;
    if (distFromStart < halfWin) {
      const prev = scenes[activeIdx - 1];
      const prevSample = sampleSceneCamera(prev, tSec, frame, isVertical);
      const blend = smoothstep(0, 1, 0.5 + distFromStart / (halfWin * 2));
      return {
        camPos: [
          lerp(prevSample.pos[0], currSample.pos[0], blend),
          lerp(prevSample.pos[1], currSample.pos[1], blend),
          lerp(prevSample.pos[2], currSample.pos[2], blend),
        ],
        lookAt: [
          lerp(prevSample.look[0], currSample.look[0], blend),
          lerp(prevSample.look[1], currSample.look[1], blend),
          lerp(prevSample.look[2], currSample.look[2], blend),
        ],
        bgHex: interpolateColors(blend, [0, 1], [prev.bgHex, current.bgHex]),
        accentHex: interpolateColors(blend, [0, 1], [prev.accentHex, current.accentHex]),
      };
    }
  }

  return {
    camPos: currSample.pos,
    lookAt: currSample.look,
    bgHex: current.bgHex,
    accentHex: current.accentHex,
  };
}

const CameraController: React.FC<{ camPos: [number, number, number]; lookAt: [number, number, number] }> = ({
  camPos,
  lookAt,
}) => {
  const camera = useThree((state) => state.camera);
  camera.position.set(camPos[0], camPos[1], camPos[2]);
  camera.lookAt(lookAt[0], lookAt[1], lookAt[2]);
  camera.updateMatrixWorld();

  useLayoutEffect(() => {
    camera.position.set(camPos[0], camPos[1], camPos[2]);
    camera.lookAt(lookAt[0], lookAt[1], lookAt[2]);
    camera.updateMatrixWorld();
  }, [camera, camPos, lookAt]);

  return null;
};

export const Continuous3DWorld: React.FC<{ plan: DocumentaryPlan }> = ({ plan }) => {
  const frame = useCurrentFrame();
  const { width, height, fps } = useVideoConfig();
  const tSec = frame / fps;
  const isVertical = height > width;

  const camState = computeContinuousCamera(plan, tSec, frame, isVertical);
  const visibleScenes = plan.scenes.filter(
    (s) => tSec >= s.startSec - 2.2 && tSec <= s.endSec + 2.2
  );

  // World-locked blueprint grid snapping every 1.0 unit so floor lines never slide during camera flight
  const gridX = Math.round(camState.lookAt[0]);
  const gridY = Math.round(camState.lookAt[1] - 1.35);
  const gridZ = Math.round(camState.lookAt[2]);

  return (
    <ThreeCanvas
      width={width}
      height={height}
      camera={{ fov: isVertical ? 50 : 38, near: 0.1, far: 45, position: camState.camPos }}
      gl={{ antialias: true, powerPreference: "high-performance" }}
    >
      <color attach="background" args={[camState.bgHex]} />
      <fog attach="fog" args={[camState.bgHex, 9.0, 20.5]} />

      <CameraController camPos={camState.camPos} lookAt={camState.lookAt} />

      {/* Grounded Technical CAD Blueprint Floor Grid */}
      <gridHelper args={[56, 56, "#1E4B68", "#1C2D46"]} position={[gridX, gridY, gridZ]} />

      {/* 3-Point Studio + Hemisphere Lighting */}
      <hemisphereLight args={["#E2E8F0", "#263750", 1.25]} />
      <directionalLight
        position={[camState.camPos[0] + 8, camState.camPos[1] + 12, camState.camPos[2] + 7]}
        intensity={2.2}
        color="#FFFFFF"
      />
      <directionalLight
        position={[camState.camPos[0] - 9, camState.camPos[1] + 5, camState.camPos[2] - 8]}
        intensity={1.5}
        color="#7DD3FC"
      />
      <pointLight
        position={[camState.lookAt[0] - 3.5, camState.lookAt[1] + 3, camState.lookAt[2] + 3]}
        intensity={1.7}
        color={camState.accentHex}
      />

      {visibleScenes.map((scene) => {
        const Comp = SCENE_REGISTRY[scene.id];
        if (!Comp) return null;
        const dur = Math.max(0.1, scene.endSec - scene.startSec);
        const progress = Math.max(0, Math.min(1, (tSec - scene.startSec) / dur));
        const localFrame = Math.max(0, frame - Math.round(scene.startSec * fps));
        return (
          <group key={scene.id} position={scene.worldPos}>
            <Comp
              frame={frame}
              localFrame={localFrame}
              progress={progress}
              accentHex={scene.accentHex}
            />
          </group>
        );
      })}
    </ThreeCanvas>
  );
};

import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { SCENE_REGISTRY } from "../generated/SceneRegistry";
import type { CartoonPlan, Transition2D } from "../types";

function computeTransitionTransform(
  transition: Transition2D,
  enterProg: number,
  width: number,
  height: number
): { transform?: string; opacity: number } {
  const p = Math.max(0, Math.min(1, enterProg));
  const ease = p * p * (3 - 2 * p);

  switch (transition) {
    case "slide_left":
      return { transform: `translateX(${(1 - ease) * width}px)`, opacity: 1 };
    case "slide_up":
      return { transform: `translateY(${(1 - ease) * height}px)`, opacity: 1 };
    case "wipe_right":
      return { transform: `translateX(${-(1 - ease) * width}px)`, opacity: 1 };
    case "zoom_dissolve":
      return { transform: `scale(${0.92 + 0.08 * ease})`, opacity: ease };
    case "flash_cut":
    default:
      return { opacity: Math.min(1, p * 2.5) };
  }
}

export const CartoonStage2D: React.FC<{ plan: CartoonPlan }> = ({ plan }) => {
  const frame = useCurrentFrame();
  const { width, height, fps } = useVideoConfig();
  const tSec = frame / fps;
  const isVertical = height > width;
  const transSec = 0.24;

  let activeIdx = plan.scenes.findIndex((s) => tSec >= s.startSec && tSec <= s.endSec);
  if (activeIdx === -1) activeIdx = plan.scenes.length - 1;

  const activeScene = plan.scenes[activeIdx];
  const prevScene = activeIdx > 0 ? plan.scenes[activeIdx - 1] : null;
  if (!activeScene) return null;

  const timeIntoScene = tSec - activeScene.startSec;
  const inTransition = Boolean(prevScene && timeIntoScene < transSec);
  const enterProg = inTransition ? Math.max(0, Math.min(1, timeIntoScene / transSec)) : 1;

  const ActiveComp = SCENE_REGISTRY[activeScene.id];
  const PrevComp = prevScene ? SCENE_REGISTRY[prevScene.id] : null;

  const activeDur = Math.max(0.1, activeScene.endSec - activeScene.startSec);
  const activeProgress = Math.max(0, Math.min(1, timeIntoScene / activeDur));
  const activeStyle = inTransition
    ? computeTransitionTransform(activeScene.transition, enterProg, width, height)
    : { opacity: 1 };

  const flashOpacity =
    inTransition && activeScene.transition === "flash_cut"
      ? interpolate(enterProg, [0, 0.35, 1], [0.85, 0.4, 0], { extrapolateRight: "clamp" })
      : 0;

  return (
    <AbsoluteFill style={{ backgroundColor: "#050811", overflow: "hidden" }}>
      {inTransition && prevScene && PrevComp && (
        <AbsoluteFill>
          <PrevComp
            frame={frame}
            localFrame={Math.max(0, frame - Math.round(prevScene.startSec * fps))}
            localTime={tSec - prevScene.startSec}
            durationSec={Math.max(0.1, prevScene.endSec - prevScene.startSec)}
            progress={1}
            peakTimes={prevScene.localPeakTimes}
            accentHex={prevScene.accentHex}
            backdropTheme={prevScene.backdropTheme}
            cameraMove={prevScene.cameraMove}
            isVertical={isVertical}
          />
        </AbsoluteFill>
      )}

      {ActiveComp && (
        <AbsoluteFill style={activeStyle}>
          <ActiveComp
            frame={frame}
            localFrame={Math.max(0, frame - Math.round(activeScene.startSec * fps))}
            localTime={timeIntoScene}
            durationSec={activeDur}
            progress={activeProgress}
            peakTimes={activeScene.localPeakTimes}
            accentHex={activeScene.accentHex}
            backdropTheme={activeScene.backdropTheme}
            cameraMove={activeScene.cameraMove}
            isVertical={isVertical}
          />
        </AbsoluteFill>
      )}

      {flashOpacity > 0 && (
        <AbsoluteFill style={{ backgroundColor: "#FFFFFF", opacity: flashOpacity, pointerEvents: "none" }} />
      )}
    </AbsoluteFill>
  );
};

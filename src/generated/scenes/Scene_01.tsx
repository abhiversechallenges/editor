import React from "react";
import {
  SceneBackdrop2D,
  Camera2D,
  CartoonCharacter2D,
  Microchip2D,
  InkCallout2D,
} from "../../components/CartoonKit2D";
import type { Scene2DProps } from "../../types";

export const Scene_01: React.FC<Scene2DProps> = (props) => {
  const { frame, localTime, progress, peakTimes, accentHex, backdropTheme, cameraMove, isVertical } = props;
  const vb = isVertical ? "0 0 1080 1920" : "0 0 1920 1080";
  return (
    <svg viewBox={vb} style={{ width: "100%", height: "100%", display: "block" }}>
      <SceneBackdrop2D theme={backdropTheme} frame={frame} accentHex={accentHex} />
      <Camera2D move={cameraMove} progress={progress} frame={frame} peakTimes={peakTimes} localTime={localTime}>
        <CartoonCharacter2D
          x={isVertical ? 330 : 540}
          y={isVertical ? 1120 : 690}
          scale={1.35}
          variant="ceo"
          mood="worried"
          pose="hold_up"
          glasses={true}
          sweatDrop={true}
          frame={frame}
        />
        <Microchip2D
          x={isVertical ? 650 : 1220}
          y={isVertical ? 760 : 530}
          scale={1.45}
          color={accentHex}
          cracked={true}
          frame={frame}
          progress={progress}
        />
        <InkCallout2D
          x={isVertical ? 540 : 1480}
          y={isVertical ? 320 : 210}
          text="$100B"
          color="#EF4444"
          fontSize={86}
          localTime={localTime}
          delaySec={0.2}
        />
      </Camera2D>
    </svg>
  );
};

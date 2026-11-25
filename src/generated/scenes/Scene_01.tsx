import React from "react";
import {
  SceneBackdrop2D, Camera2D, TelemetryHUD2D, MicrochannelColdPlate2D, TechnicalCallout2D
} from "../../components/CartoonKit2D";
import type { Scene2DProps } from "../../types";

export const Scene_01: React.FC<Scene2DProps> = (props) => {
  const { frame, localTime, progress, peakTimes, accentHex, backdropTheme, cameraMove, isVertical } = props;
  const vb = isVertical ? "0 0 1080 1920" : "0 0 1920 1080";
  return (
    <svg viewBox={vb} style={{ width: "100%", height: "100%", display: "block" }}>
      <SceneBackdrop2D theme={backdropTheme} frame={frame} accentHex={accentHex} />
      <Camera2D move={cameraMove} progress={progress} frame={frame} peakTimes={peakTimes} localTime={localTime}>
        <MicrochannelColdPlate2D
          x={isVertical ? 540 : 880}
          y={isVertical ? 960 : 540}
          scale={1.3}
          coolantTempC={62}
          frame={frame}
          progress={progress}
        />
        <TelemetryHUD2D
          x={isVertical ? 120 : 120}
          y={isVertical ? 240 : 180}
          title="COLD PLATE TELEMETRY"
          metrics={[
            { label: "COOLANT INLET", value: "32.0", unit: "C" },
            { label: "COOLANT OUTLET", value: "62.4", unit: "C", alert: true },
            { label: "FLOW RATE", value: "2.1", unit: "LPM" },
          ]}
          progress={progress}
        />
        <TechnicalCallout2D
          x={isVertical ? 540 : 1420}
          y={isVertical ? 1520 : 480}
          text="40um COPPER CHANNELS"
          subtext="Direct-to-Die Interface"
          color="#00F0FF"
          localTime={localTime}
          delaySec={0.2}
          arrowTo={[isVertical ? 540 : 880, isVertical ? 960 : 540]}
        />
      </Camera2D>
    </svg>
  );
};

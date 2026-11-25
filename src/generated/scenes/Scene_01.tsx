import React from "react";
import { SceneBackdrop2D, Camera2D, DataHall25D, TelemetryHUD2D } from "../../components/CartoonKit2D";
import type { Scene2DProps } from "../../types";

export const Scene_01: React.FC<Scene2DProps> = (props) => {
  const { frame, localTime, progress, peakTimes, accentHex, backdropTheme, cameraMove, chapterTag, isVertical } = props;
  const vb = isVertical ? "0 0 1080 1920" : "0 0 1920 1080";
  return (
    <svg viewBox={vb} style={{ width: "100%", height: "100%", display: "block" }}>
      <SceneBackdrop2D theme={backdropTheme} frame={frame} accentHex={accentHex} chapterTag={chapterTag} />
      <Camera2D move={cameraMove} progress={progress} frame={frame} peakTimes={peakTimes} localTime={localTime}>
        <DataHall25D accentHex={accentHex} frame={frame} progress={progress} isVertical={isVertical} />
        <TelemetryHUD2D
          x={isVertical ? 120 : 1310}
          y={isVertical ? 160 : 120}
          w={isVertical ? 840 : 540}
          title="DATA HALL TELEMETRY"
          metrics={[
            { label: "CAMPUS POWER", value: "1,000", unit: "MW", barPct: 95 },
            { label: "RACK DENSITY", value: "600", unit: "kW", alert: true, barPct: 90 },
            { label: "TOTAL CAPEX", value: "$100", unit: "B", barPct: 84 },
            { label: "COOLANT INLET", value: "18.0", unit: "C", barPct: 45 },
          ]}
          progress={progress}
        />
      </Camera2D>
    </svg>
  );
};

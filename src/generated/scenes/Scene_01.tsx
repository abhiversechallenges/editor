import React from "react";
import {
  DataHallBuilding,
  CitySkylineBlock,
  PowerPylon,
  PipeConduit,
} from "../../components/StudioKit";
import type { DynamicSceneProps } from "../../types";

export const Scene_01: React.FC<DynamicSceneProps> = ({ frame, progress, accentHex }) => {
  return (
    <group>
      <DataHallBuilding pos={[-0.9, -0.2, 0]} size={[3.0, 1.5, 2.2]} accentHex={accentHex} progress={progress} frame={frame} />
      <PowerPylon pos={[0.95, 0.0, -0.6]} height={2.3} accentHex="#F59E0B" />
      <CitySkylineBlock pos={[2.1, -0.25, 0.4]} scale={0.85} accentHex="#F59E0B" frame={frame} />
      <PipeConduit
        points={[[-0.9, -0.8, 0.9], [0.95, 0.4, -0.6], [2.1, -0.6, 0.4]]}
        fluidColor={accentHex}
        flangeCount={3}
        speed={0.85}
        frame={frame}
      />
    </group>
  );
};

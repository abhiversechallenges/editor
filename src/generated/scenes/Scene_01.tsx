import React from "react";
import {
  MatteBox,
  HardwareRack,
  FinnedHousing,
  PipeConduit,
  RevealSlideGroup,
} from "../../components/StudioKit";
import type { DynamicSceneProps } from "../../types";

export const Scene_01: React.FC<DynamicSceneProps> = ({ frame, progress, accentHex }) => {
  return (
    <group>
      <MatteBox pos={[0, -1.0, 0]} size={[5.6, 0.22, 3.8]} color="#2B3B52" edgeColor={accentHex} />
      <HardwareRack pos={[-1.4, 0.1, 0]} size={[1.1, 2.0, 1.1]} bays={6} accentHex={accentHex} frame={frame} />
      <FinnedHousing pos={[1.2, 0.1, 0]} radius={0.85} height={1.8} finCount={8} accentHex={accentHex} cutaway={true} frame={frame} />
      <RevealSlideGroup startPos={[0, 0, 0]} endPos={[0, 1.4, 0]} progress={progress} startAt={0.2} endAt={0.65}>
        <MatteBox pos={[0, 1.2, 0]} size={[4.2, 0.16, 2.6]} color="#3B4E6B" edgeColor={accentHex} />
      </RevealSlideGroup>
      <PipeConduit
        points={[[-1.4, 0.3, 0.65], [-0.4, -0.1, 0.9], [0.4, -0.1, 0.9], [1.2, 0.3, 0.65]]}
        fluidColor={accentHex}
        flangeCount={3}
        speed={0.85}
        frame={frame}
      />
    </group>
  );
};

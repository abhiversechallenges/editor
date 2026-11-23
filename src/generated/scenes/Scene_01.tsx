import React from "react";
import {
  MatteBox,
  MatteCylinder,
  RevealSlideGroup,
  SpinGroup,
  FlowStream,
} from "../../components/StudioKit";
import type { DynamicSceneProps } from "../../types";

export const Scene_01: React.FC<DynamicSceneProps> = ({ frame, progress, accentHex }) => {
  return (
    <group>
      <MatteBox pos={[0, -0.7, 0]} size={[5.4, 0.2, 3.8]} color="#141C2B" />
      <MatteBox pos={[0, 0.05, 0]} size={[3.6, 1.1, 2.2]} color="#243146" />
      <RevealSlideGroup startPos={[0, 0, 0]} endPos={[0, 1.8, 0]} progress={progress} startAt={0.2} endAt={0.65}>
        <MatteBox pos={[0, 0.65, 0]} size={[3.7, 0.14, 2.3]} color="#334155" />
        <SpinGroup pos={[-0.9, 0.8, 0]} axis="y" speed={4.0} frame={frame}>
          <MatteCylinder radiusTop={0.25} radiusBottom={0.25} height={0.12} color={accentHex} emissive={accentHex} />
        </SpinGroup>
        <SpinGroup pos={[0.9, 0.8, 0]} axis="y" speed={4.0} frame={frame}>
          <MatteCylinder radiusTop={0.25} radiusBottom={0.25} height={0.12} color={accentHex} emissive={accentHex} />
        </SpinGroup>
      </RevealSlideGroup>
      <FlowStream
        points={[[-2.6, -0.35, 0], [-0.9, -0.35, 0], [0.9, -0.35, 0], [2.6, -0.35, 0]]}
        tubeColor="#1E293B"
        particleColor={accentHex}
        count={6}
        speed={0.8}
        frame={frame}
      />
    </group>
  );
};

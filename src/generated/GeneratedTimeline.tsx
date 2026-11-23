import React from "react";
import { AbsoluteFill } from "remotion";
import { Continuous3DWorld } from "../components/Continuous3DWorld";
import { SCENE_PLAN } from "./ScenesData";

export const GENERATED_TOTAL_FRAMES = 300;

export const GeneratedTimeline: React.FC = () => {
  return (
    <AbsoluteFill>
      <Continuous3DWorld plan={SCENE_PLAN} />
    </AbsoluteFill>
  );
};

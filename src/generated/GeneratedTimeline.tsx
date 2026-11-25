import React from "react";
import { AbsoluteFill } from "remotion";
import { CartoonStage2D } from "../components/CartoonStage2D";
import { SCENE_PLAN } from "./ScenesData";

export const GENERATED_TOTAL_FRAMES = 180;

export const GeneratedTimeline: React.FC = () => (
  <AbsoluteFill>
    <CartoonStage2D plan={SCENE_PLAN} />
  </AbsoluteFill>
);

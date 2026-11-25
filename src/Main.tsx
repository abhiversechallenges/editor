import React from "react";
import { AbsoluteFill } from "remotion";
import { GeneratedTimeline } from "./generated/GeneratedTimeline";

export const Main: React.FC = () => (
  <AbsoluteFill style={{ backgroundColor: "#04070E" }}>
    <GeneratedTimeline />
  </AbsoluteFill>
);

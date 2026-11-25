import React from "react";
import { AbsoluteFill } from "remotion";
import { GeneratedTimeline } from "./generated/GeneratedTimeline";

export const Main: React.FC = () => (
  <AbsoluteFill style={{ backgroundColor: "#050811" }}>
    <GeneratedTimeline />
  </AbsoluteFill>
);

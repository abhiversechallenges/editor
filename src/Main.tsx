import React from "react";
import { AbsoluteFill } from "remotion";
import { GeneratedTimeline } from "./generated/GeneratedTimeline";

export const Main: React.FC = () => {
  return (
    <AbsoluteFill style={{ backgroundColor: "#08101E" }}>
      <GeneratedTimeline />
    </AbsoluteFill>
  );
};

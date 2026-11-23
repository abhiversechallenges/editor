import type { DocumentaryPlan } from "../types";

export const SCENE_PLAN: DocumentaryPlan = {
  channel: "InfraVerse",
  fps: 30,
  width: 1920,
  height: 1080,
  totalDurationSec: 10,
  hasAudio: false,
  bpm: 96,
  emphasisPeaksSec: [3, 7],
  scenes: [
    {
      id: "scene_01",
      componentName: "Scene_01",
      visualConcept: "Baseline AI Data Center Cutaway",
      visualSpec: "Data center cutaway roof lift with glowing fiber flows",
      startSec: 0,
      endSec: 10,
      worldPos: [0, 0, 0],
      bgHex: "#08101E",
      accentHex: "#22D3EE",
      cameraWaypoints: [
        { offset: [5.5, 3.0, 6.0], lookOffset: [0, 0.2, 0] },
        { offset: [0.5, 1.8, 4.2], lookOffset: [0, 0.1, 0] },
        { offset: [-3.5, 2.2, 4.8], lookOffset: [0, 0, 0] },
      ],
    },
  ],
};

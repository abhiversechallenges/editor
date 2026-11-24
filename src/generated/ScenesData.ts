import type { DocumentaryPlan } from "../types";

export const SCENE_PLAN: DocumentaryPlan = {
  channel: "InfraVerse",
  fps: 30,
  width: 1920,
  height: 1080,
  totalDurationSec: 8,
  hasAudio: false,
  bpm: 102,
  emphasisPeaksSec: [1.5, 5.2],
  subtitleChunks: [],
  scenes: [
    {
      id: "scene_01",
      componentName: "Scene_01",
      visualConcept: "Multi-Part AI Rack & Cooling Core",
      visualSpec: "HardwareRack paired with FinnedHousing and PipeConduit",
      startSec: 0,
      endSec: 8,
      worldPos: [0, 0, 0],
      bgHex: "#0E1729",
      accentHex: "#22D3EE",
      beats: [
        {
          id: "b_01_01",
          startSec: 0,
          endSec: 4,
          triggerSec: 0.4,
          cameraOffset: [5.6, 3.0, 6.0],
          lookOffset: [0, 0.2, 0],
          callouts: [{ label: "600 kW / RACK", anchorPct: [42, 48], boxPct: [22, 26] }],
          statCounter: { label: "CAMPUS POWER", fromVal: 0, toVal: 1000, suffix: " MW" },
        },
        {
          id: "b_01_02",
          startSec: 4,
          endSec: 8,
          triggerSec: 4.3,
          cameraOffset: [1.8, 1.5, 3.8],
          lookOffset: [0.2, 0.1, 0],
          callouts: [{ label: "CLOSED-LOOP CDU", anchorPct: [58, 52], boxPct: [74, 28] }],
          statCounter: null,
        },
      ],
    },
  ],
};

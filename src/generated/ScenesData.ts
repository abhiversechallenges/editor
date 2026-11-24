import type { DocumentaryPlan } from "../types";

export const SCENE_PLAN: DocumentaryPlan = {
  channel: "InfraVerse",
  fps: 30,
  width: 1920,
  height: 1080,
  totalDurationSec: 8,
  hasAudio: false,
  bpm: 102,
  emphasisPeaksSec: [0.2, 4.5],
  subtitleChunks: [],
  scenes: [
    {
      id: "scene_01",
      componentName: "Scene_01",
      visualConcept: "Data Hall Campus & City Grid",
      visualSpec: "DataHallBuilding + PowerPylon + CitySkylineBlock",
      startSec: 0,
      endSec: 8,
      worldPos: [0, 0, 0],
      bgHex: "#101B2E",
      accentHex: "#22D3EE",
      beats: [
        {
          id: "b_01_01",
          startSec: 0,
          endSec: 4,
          triggerSec: 0.0,
          cameraOffset: [3.8, 2.0, 4.3],
          lookOffset: [0, 0.3, 0],
          callouts: [{ label: "1,000 MW DATA HALL", anchorPct: [44, 52], boxPct: [74, 24] }],
          statCounter: { label: "TOTAL CAMPUS CAPEX", fromVal: 0, toVal: 100, prefix: "$", suffix: "B", decimals: 0 },
        },
        {
          id: "b_01_02",
          startSec: 4,
          endSec: 8,
          triggerSec: 4.2,
          cameraOffset: [1.5, 1.3, 3.0],
          lookOffset: [0.15, 0.25, 0],
          callouts: [{ label: "CITY POWER DRAW", anchorPct: [60, 56], boxPct: [22, 34] }],
          statCounter: null,
        },
      ],
    },
  ],
};

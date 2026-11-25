import type { CartoonPlan } from "../types";

export const SCENE_PLAN: CartoonPlan = {
  channel: "CoreToGrid",
  fps: 30,
  width: 1920,
  height: 1080,
  totalDurationSec: 5,
  bpm: 105,
  emphasisPeaksSec: [0.4, 2.8],
  scenes: [
    {
      id: "scene_01",
      componentName: "Scene_01",
      chapterTag: "01 // 1-GIGAWATT DATA HALL",
      visualConcept: "2.5D Isometric Data Hall + Right Telemetry HUD",
      visualSpec: "2.5D racks on left 65%, telemetry HUD right 30%, labeled cooling loops bottom",
      titleText: "",
      stampText: "600 KW HEAT",
      stampColor: "#EF4444",
      stampTriggerSec: 1.2,
      statCounter: { label: "FACILITY EFFICIENCY", startVal: 1.48, endVal: 1.12, suffix: " PUE", decimals: 2, color: "#00F0FF", triggerSec: 0.2 },
      backdropTheme: "isometric_blueprint",
      cameraMove: "push_in",
      transition: "flash_cut",
      sfx: "impact",
      accentHex: "#00F0FF",
      startSec: 0,
      endSec: 5,
      localPeakTimes: [0.4, 2.8],
    },
  ],
};

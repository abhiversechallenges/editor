import type { CartoonPlan } from "../types";

export const SCENE_PLAN: CartoonPlan = {
  channel: "CoreToGrid",
  fps: 30,
  width: 1920,
  height: 1080,
  totalDurationSec: 6,
  bpm: 105,
  scenes: [
    {
      id: "scene_01",
      componentName: "Scene_01",
      visualConcept: "Baseline Microchannel Cold Plate",
      visualSpec: "Exploded copper plate with live telemetry HUD",
      titleText: "",
      backdropTheme: "isometric_blueprint",
      cameraMove: "push_in",
      transition: "flash_cut",
      sfx: "sub_impact",
      accentHex: "#00F0FF",
      startSec: 0,
      endSec: 6,
      localPeakTimes: [0.4, 3.2],
    },
  ],
};

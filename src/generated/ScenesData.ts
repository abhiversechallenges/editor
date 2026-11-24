import type { CartoonPlan } from "../types";

export const SCENE_PLAN: CartoonPlan = {
  channel: "InfraVerse2D",
  fps: 30,
  width: 1920,
  height: 1080,
  totalDurationSec: 6,
  hasAudio: false,
  bpm: 104,
  emphasisPeaksSec: [0.4, 3.2],
  scenes: [
    {
      id: "scene_01",
      componentName: "Scene_01",
      visualConcept: "Baseline 2D Cartoon Scene",
      visualSpec: "Character holding cracking chip on night mountains",
      titleText: "",
      backdropTheme: "night_mountains",
      cameraMove: "push_in",
      transition: "flash_cut",
      sfx: "sub_impact",
      accentHex: "#22C55E",
      startSec: 0,
      endSec: 6,
      localPeakTimes: [0.4, 3.2],
    },
  ],
};

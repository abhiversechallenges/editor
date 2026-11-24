export type BackdropTheme =
  | "night_mountains"
  | "sunset_horizon"
  | "daylight_city"
  | "graph_paper"
  | "notebook_lined"
  | "world_map"
  | "warm_office"
  | "steel_vault"
  | "dark_industrial"
  | "news_document"
  | "split_3panel"
  | "black_title_card";

export type CameraMove2D =
  | "push_in"
  | "pull_out"
  | "pan_right"
  | "pan_left"
  | "pan_up"
  | "shake_hit";

export type Transition2D =
  | "slide_left"
  | "slide_up"
  | "wipe_right"
  | "zoom_dissolve"
  | "flash_cut";

export interface Scene2DProps {
  frame: number;
  localFrame: number;
  localTime: number;
  durationSec: number;
  progress: number;
  peakTimes: number[];
  accentHex: string;
  backdropTheme: BackdropTheme;
  cameraMove: CameraMove2D;
  isVertical: boolean;
}

export interface CartoonScene {
  id: string;
  componentName: string;
  visualConcept: string;
  visualSpec: string;
  titleText: string;
  backdropTheme: BackdropTheme;
  cameraMove: CameraMove2D;
  transition: Transition2D;
  sfx: string;
  accentHex: string;
  startSec: number;
  endSec: number;
  localPeakTimes: number[];
}

export interface CartoonPlan {
  channel: string;
  fps: number;
  width: number;
  height: number;
  totalDurationSec: number;
  hasAudio: boolean;
  bpm: number;
  emphasisPeaksSec: number[];
  scenes: CartoonScene[];
}

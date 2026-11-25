export type BackdropTheme =
  | "isometric_blueprint"
  | "xray_cutaway"
  | "substation_grid"
  | "cleanroom_fab"
  | "thermal_flow"
  | "server_corridor"
  | "dark_industrial"
  | "black_title_card"
  | "split_3panel";

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
  bpm: number;
  scenes: CartoonScene[];
}

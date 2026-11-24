export type V3 = [number, number, number];

export interface DynamicSceneProps {
  frame: number;
  localFrame: number;
  progress: number;
  accentHex: string;
}

export interface HudCallout {
  label: string;
  anchorPct: [number, number];
  boxPct: [number, number];
}

export interface StatCounter {
  label: string;
  fromVal: number;
  toVal: number;
  prefix?: string;
  suffix?: string;
  decimals?: number;
}

export interface VisualBeat {
  id: string;
  startSec: number;
  endSec: number;
  triggerSec: number;
  cameraOffset: V3;
  lookOffset: V3;
  callouts: HudCallout[];
  statCounter: StatCounter | null;
}

export interface SubtitleWord {
  text: string;
  highlight: boolean;
}

export interface SubtitleChunk {
  startSec: number;
  endSec: number;
  words: SubtitleWord[];
}

export interface DocumentaryScene {
  id: string;
  componentName: string;
  visualConcept: string;
  visualSpec: string;
  startSec: number;
  endSec: number;
  worldPos: V3;
  bgHex: string;
  accentHex: string;
  beats: VisualBeat[];
}

export interface DocumentaryPlan {
  channel: string;
  fps: number;
  width: number;
  height: number;
  totalDurationSec: number;
  hasAudio: boolean;
  bpm: number;
  emphasisPeaksSec: number[];
  subtitleChunks: SubtitleChunk[];
  scenes: DocumentaryScene[];
}

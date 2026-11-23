import type React from "react";
import type { DynamicSceneProps } from "../types";
import { Scene_01 } from "./scenes/Scene_01";

export const SCENE_REGISTRY: Record<string, React.FC<DynamicSceneProps>> = {
  scene_01: Scene_01,
};

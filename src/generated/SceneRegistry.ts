import type React from "react";
import type { Scene2DProps } from "../types";
import { Scene_01 } from "./scenes/Scene_01";

export const SCENE_REGISTRY: Record<string, React.FC<Scene2DProps>> = {
  scene_01: Scene_01,
};

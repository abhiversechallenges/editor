import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gemini_helper import clean_tsx_text, generate_with_fallback, get_client, parse_json_strict

ROOT = Path(__file__).resolve().parent.parent
WORK_DIR = ROOT / "work"
GENERATED_DIR = ROOT / "src" / "generated"
SCENES_DIR = GENERATED_DIR / "scenes"

BACKDROP_THEMES = [
    "night_mountains",
    "sunset_horizon",
    "daylight_city",
    "graph_paper",
    "notebook_lined",
    "world_map",
    "warm_office",
    "steel_vault",
    "dark_industrial",
    "news_document",
    "split_3panel",
    "black_title_card",
]

CAMERA_MOVES = [
    "push_in",
    "pull_out",
    "pan_right",
    "pan_left",
    "pan_up",
    "shake_hit",
]

TRANSITIONS = [
    "slide_left",
    "slide_up",
    "wipe_right",
    "zoom_dissolve",
    "flash_cut",
]

SFX_CUES = ["whoosh", "pop_snap", "marker_swipe", "sub_impact", "tick"]

CARTOON_KIT_DOC = """
Available components in "../../components/CartoonKit2D" (ONLY import React, CartoonKit2D, and Scene2DProps):
import React from "react";
import {
  SceneBackdrop2D, Camera2D, CartoonCharacter2D, TitleCard2D,
  InkCallout2D, LineChart2D, BarChart2D, PieChart2D, BalanceScale2D,
  ConveyorBelt2D, WorldMapArc2D, QuoteHighlight2D, CalendarFlip2D, Stopwatch2D,
  SplitScreen3Panel, ReactorVessel2D, CoolingTower2D, ServerRack2D,
  Microchip2D, PowerPylon2D, BatteryBank2D, AnimatedPipe2D, ExplosionBurst2D
} from "../../components/CartoonKit2D";
import type { Scene2DProps } from "../../types";

Props Reference (Coordinates operate inside a clean 1920x1080 SVG stage! Even on 9:16 Shorts, the camera frames smoothly, or use `isVertical` prop to stack vertically!):
- Scene2DProps: { frame: number; localFrame: number; localTime: number; durationSec: number; progress: number; peakTimes: number[]; accentHex: string; backdropTheme: BackdropTheme; cameraMove: CameraMove2D; isVertical: boolean }
- SceneBackdrop2D: { theme: BackdropTheme; frame: number; accentHex?: string }
  (Always render SceneBackdrop2D first!)
- Camera2D: { move: CameraMove2D; progress: number; frame: number; peakTimes?: number[]; localTime: number; children?: React.ReactNode }
  (Wrap foreground visual content inside Camera2D so there is ALWAYS smooth continuous camera motion and punchy micro-shakes on vocal peaks!)
- CartoonCharacter2D: { x: number; y: number; scale?: number; variant?: "ceo"|"engineer"|"worker"|"suit"|"operator"; mood?: "neutral"|"shocked"|"worried"|"happy"|"smug"|"angry"; pose?: "stand"|"point_right"|"point_up"|"hold_up"|"hands_head"|"celebrate"; glasses?: boolean; hardHat?: boolean; sweatDrop?: boolean; flip?: boolean; frame: number }
- TitleCard2D: { text: string; progress: number; accentHex?: string }
  (Use ONLY when theme is "black_title_card" — handwritten white Caveat marker text!)
- InkCallout2D: { x: number; y: number; text: string; color?: string; fontSize?: number; delaySec?: number; localTime: number; rotateDeg?: number; arrowTo?: [number, number] }
- LineChart2D: { x: number; y: number; w?: number; h?: number; label?: string; startVal?: number; endVal?: number; prefix?: string; suffix?: string; decimals?: number; color?: string; points?: number[]; progress: number }
- BarChart2D: { x: number; y: number; w?: number; h?: number; bars: { label: string; value: number; color?: string }[]; multiplierTag?: string; suffix?: string; prefix?: string; progress: number }
- PieChart2D: { x: number; y: number; radius?: number; slicePct: number; label: string; color?: string; progress: number }
- BalanceScale2D: { x: number; y: number; leftLabel: string; rightLabel: string; tiltDeg?: number; leftColor?: string; rightColor?: string; progress: number }
- ConveyorBelt2D: { x: number; y: number; w?: number; items: string[]; accentHex?: string; frame: number; progress: number }
- WorldMapArc2D: { x: number; y: number; w?: number; h?: number; startPct?: [number, number]; endPct?: [number, number]; accentHex?: string; zoomLabel?: string; progress: number; frame: number }
- QuoteHighlight2D: { x: number; y: number; w?: number; sourceTag: string; quoteBefore: string; highlightText: string; quoteAfter?: string; markStamp?: string; progress: number }
- CalendarFlip2D: { x: number; y: number; pages: { month: string; day: string }[]; progress: number }
- Stopwatch2D: { x: number; y: number; radius?: number; maxSecLabel?: string; progress: number }
- SplitScreen3Panel: { progress: number; panel1: React.ReactNode; panel2: React.ReactNode; panel3: React.ReactNode }
  (Reveals Panel 1 -> Panel 2 -> Panel 3 sequentially across progress 0..0.7 — use inside 1920x1080 viewBox!)
- ReactorVessel2D: { x: number; y: number; scale?: number; accentHex?: string; frame: number; progress: number }
- CoolingTower2D: { x: number; y: number; scale?: number; accentHex?: string; frame: number }
- ServerRack2D: { x: number; y: number; scale?: number; accentHex?: string; frame: number }
- Microchip2D: { x: number; y: number; scale?: number; color?: string; cracked?: boolean; overheating?: boolean; frame: number; progress: number }
- PowerPylon2D: { x: number; y: number; scale?: number; accentHex?: string; frame: number }
- BatteryBank2D: { x: number; y: number; scale?: number; accentHex?: string; frame: number; progress: number }
- AnimatedPipe2D: { d: string; color?: string; fluidColor?: string; strokeWidth?: number; frame: number }
  (Bold ink-outlined curved SVG pipe with dashed glowing fluid moving continuously!)
- ExplosionBurst2D: { x: number; y: number; color?: string; triggerSec: number; localTime: number }

STRICT RULES FOR SCENE COMPONENTS:
1. Export EXACTLY `export const Scene_XX: React.FC<Scene2DProps> = (props) => { ... }`.
2. Return a single `<svg viewBox="0 0 1920 1080" style={{ width: "100%", height: "100%", display: "block" }}>` (or if `isVertical`, compose cleanly inside `viewBox="0 0 1080 1920"` when building vertical, OR use `isVertical` to adjust positions! Even simpler: render `<SceneBackdrop2D theme={props.backdropTheme} frame={props.frame} accentHex={props.accentHex} />` and `<Camera2D move={props.cameraMove} progress={props.progress} frame={props.frame} peakTimes={props.peakTimes} localTime={props.localTime}>` inside an `<svg viewBox={props.isVertical ? "0 0 1080 1920" : "0 0 1920 1080"} style={{ width: "100%", height: "100%", display: "block" }}>`!).
   CRITICAL: Notice `SceneBackdrop2D` and `Camera2D` return SVG `<g>` elements! Everything inside `<svg>` MUST be valid SVG (`<g>`, `<rect>`, `<circle>`, `<path>`, `<line>`, `<polygon>`, `<text>`) or `CartoonKit2D` components! NEVER put `<div>` inside `<svg>`!
3. NEVER import `three`, `@react-three`, `remotion`, `useFrame`, `useEffect`, or `useState`.
4. NEVER use hardcoded `id="..."` on `<linearGradient>` or `<clipPath>` inside generated scenes (use solid/rgba colors + bold `#111827` `strokeWidth={5}` black outlines for crisp Video 1 ink style!).
5. NO bottom subtitle boxes! Use `InkCallout2D`, `QuoteHighlight2D`, `TitleCard2D`, charts, and expressive characters synced to `localTime` & `peakTimes`.
6. EVERY scene MUST be alive on every frame (character blinking/moving, pipes flowing, charts drawing, clouds/stars moving, camera moving).
"""

FORBIDDEN_CODE_PATTERNS = (
    "<div",
    "<span",
    "useFrame",
    "useEffect",
    "useState",
    "from 'three'",
    'from "three"',
    "@react-three",
    "from 'remotion'",
    'from "remotion"',
)


def get_input_dir() -> Path:
    folder = os.environ.get("INPUT_FOLDER", "input").strip() or "input"
    return ROOT / folder


def load_visuals_prompt(input_dir: Path) -> str:
    if not input_dir.exists():
        return ""
    candidates = [
        p
        for p in input_dir.iterdir()
        if p.is_file() and p.suffix.lower() == ".txt" and p.name != "visuals_EXAMPLE.txt"
    ]
    if not candidates:
        return ""
    for p in candidates:
        if p.name.lower() == "visuals.txt":
            return p.read_text(encoding="utf-8").strip()

    def git_ts(path: Path) -> int:
        res = subprocess.run(
            ["git", "log", "-n", "1", "--format=%ct", "--", str(path.relative_to(ROOT))],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            check=False,
        )
        out = (res.stdout or "").strip()
        return int(out) if out.isdigit() else int(path.stat().st_mtime)

    return max(candidates, key=git_ts).read_text(encoding="utf-8").strip()


def compute_scene_range(duration_sec: float, is_short: bool) -> tuple[int, int]:
    if is_short:
        if duration_sec <= 20:
            return 4, 6
        if duration_sec <= 40:
            return 6, 9
        return 8, 12
    if duration_sec <= 25:
        return 4, 6
    if duration_sec <= 65:
        return 10, 14
    if duration_sec <= 150:
        return 18, 25
    if duration_sec <= 360:
        return 34, 48
    return 52, 72


def snap_to_boundary(target: float, boundaries: List[float], min_val: float, max_val: float) -> float:
    best = target
    best_dist = 0.6
    for b in boundaries:
        d = abs(b - target)
        if d <= best_dist and min_val < b < max_val:
            best = b
            best_dist = d
    return round(best, 3)


def sanitize_hex(val: Any, fallback: str) -> str:
    if isinstance(val, str) and re.fullmatch(r"#[0-9A-Fa-f]{6}", val.strip()):
        return val.strip()
    return fallback


def build_safe_fallback_scene_tsx(
    scene_num: int,
    backdrop: str,
    accent: str,
    concept: str,
    title_text: str,
) -> str:
    safe_comment = re.sub(r"[^A-Za-z0-9 ,.-]", "", concept)[:60]
    safe_title = json.dumps(title_text or concept[:28])
    variant = scene_num % 6

    if backdrop == "black_title_card":
        inner = f"""
      <TitleCard2D text={{{safe_title}}} progress={{progress}} accentHex={{"{accent}"}} />"""
    elif variant == 0:
        inner = f"""
      <ReactorVessel2D x={{isVertical ? 540 : 620}} y={{isVertical ? 840 : 570}} scale={{1.25}} accentHex={{"{accent}"}} frame={{frame}} progress={{progress}} />
      <CartoonCharacter2D x={{isVertical ? 280 : 1280}} y={{isVertical ? 1280 : 720}} scale={{1.15}} variant="engineer" mood="worried" hardHat={{true}} sweatDrop={{true}} pose="point_right" flip={{true}} frame={{frame}} />
      <InkCallout2D x={{isVertical ? 540 : 1240}} y={{isVertical ? 320 : 280}} text="CORE HEAT" color={{"{accent}"}} localTime={{localTime}} delaySec={{0.2}} />"""
    elif variant == 1:
        inner = f"""
      <LineChart2D x={{isVertical ? 140 : 420}} y={{isVertical ? 420 : 230}} w={{isVertical ? 800 : 1080}} h={{520}} label="POWER LOAD" startVal={{120}} endVal={{1000}} suffix=" MW" color={{"{accent}"}} progress={{progress}} />
      <CartoonCharacter2D x={{isVertical ? 540 : 240}} y={{isVertical ? 1320 : 730}} scale={{1.05}} variant="ceo" mood="shocked" glasses={{true}} sweatDrop={{true}} pose="hands_head" frame={{frame}} />"""
    elif variant == 2:
        inner = f"""
      <ServerRack2D x={{isVertical ? 340 : 540}} y={{isVertical ? 760 : 540}} scale={{1.15}} accentHex={{"{accent}"}} frame={{frame}} />
      <ServerRack2D x={{isVertical ? 740 : 940}} y={{isVertical ? 760 : 540}} scale={{1.15}} accentHex={{"{accent}"}} frame={{frame}} />
      <Microchip2D x={{isVertical ? 540 : 1380}} y={{isVertical ? 1260 : 540}} scale={{1.1}} color={{"{accent}"}} overheating={{true}} cracked={{true}} frame={{frame}} progress={{progress}} />
      <AnimatedPipe2D d={{isVertical ? "M 340 420 L 740 420 L 740 960" : "M 540 240 L 940 240 L 1380 420"}} fluidColor={{"{accent}"}} frame={{frame}} />"""
    elif variant == 3:
        inner = f"""
      <BalanceScale2D x={{isVertical ? 540 : 960}} y={{isVertical ? 900 : 560}} leftLabel="GRID SUPPLY" rightLabel="AI DEMAND" tiltDeg={{18}} leftColor="#10B981" rightColor="#EF4444" progress={{progress}} />
      <InkCallout2D x={{isVertical ? 540 : 960}} y={{isVertical ? 340 : 190}} text="BOTTLENECK" color="#EF4444" localTime={{localTime}} delaySec={{0.4}} />"""
    elif variant == 4:
        inner = f"""
      <CoolingTower2D x={{isVertical ? 380 : 620}} y={{isVertical ? 780 : 560}} scale={{1.15}} accentHex={{"{accent}"}} frame={{frame}} />
      <PowerPylon2D x={{isVertical ? 740 : 1140}} y={{isVertical ? 820 : 560}} scale={{1.1}} accentHex="#F59E0B" frame={{frame}} />
      <BatteryBank2D x={{isVertical ? 540 : 1540}} y={{isVertical ? 1320 : 620}} scale={{1.05}} accentHex="#10B981" frame={{frame}} progress={{progress}} />"""
    else:
        inner = f"""
      <WorldMapArc2D x={{isVertical ? 90 : 320}} y={{isVertical ? 460 : 200}} w={{isVertical ? 900 : 1280}} h={{640}} accentHex={{"{accent}"}} zoomLabel="SUBSEA LINK" progress={{progress}} frame={{frame}} />
      <Stopwatch2D x={{isVertical ? 540 : 1620}} y={{isVertical ? 1380 : 340}} radius={{120}} maxSecLabel="24/7" progress={{progress}} />"""

    return f"""import React from "react";
import {{
  SceneBackdrop2D, Camera2D, CartoonCharacter2D, TitleCard2D,
  InkCallout2D, LineChart2D, BalanceScale2D, WorldMapArc2D, Stopwatch2D,
  ReactorVessel2D, CoolingTower2D, ServerRack2D, Microchip2D, PowerPylon2D, BatteryBank2D, AnimatedPipe2D
}} from "../../components/CartoonKit2D";
import type {{ Scene2DProps }} from "../../types";

// Fallback 2D scene: {safe_comment}
export const Scene_{scene_num:02d}: React.FC<Scene2DProps> = (props) => {{
  const {{ frame, localTime, progress, peakTimes, accentHex, backdropTheme, cameraMove, isVertical }} = props;
  const vb = isVertical ? "0 0 1080 1920" : "0 0 1920 1080";
  return (
    <svg viewBox={{vb}} style={{{{ width: "100%", height: "100%", display: "block" }}}}>
      <SceneBackdrop2D theme={{backdropTheme}} frame={{frame}} accentHex={{accentHex}} />
      <Camera2D move={{cameraMove}} progress={{progress}} frame={{frame}} peakTimes={{peakTimes}} localTime={{localTime}}>{inner}
      </Camera2D>
    </svg>
  );
}};
"""


def extract_scenes_dict(raw_text: str) -> Dict[str, str]:
    cleaned = clean_tsx_text(raw_text)
    try:
        parsed = json.loads(cleaned)
        if isinstance(parsed, dict):
            return {str(k): str(v) for k, v in parsed.items()}
    except Exception:
        pass

    blocks: Dict[str, str] = {}
    parts = re.split(r"//\s*===\s*(Scene_\d+)\s*===", cleaned)
    if len(parts) >= 3:
        for i in range(1, len(parts), 2):
            blocks[parts[i].strip()] = parts[i + 1].strip()
    return blocks


def sanitize_scene_tsx(code: str, scene_num: int) -> str:
    txt = clean_tsx_text(code)
    for bad in FORBIDDEN_CODE_PATTERNS:
        if bad in txt:
            raise ValueError(f"Scene_{scene_num:02d} contained forbidden token: {bad}")
    expected_export = f"Scene_{scene_num:02d}"
    if expected_export not in txt:
        txt = re.sub(r"export\s+const\s+Scene_\d+\s*:", f"export const {expected_export}:", txt)
    if expected_export not in txt:
        raise ValueError(f"Missing export {expected_export}")
    return txt.strip() + "\n"


def normalize_storyboard(
    raw_board: Dict[str, Any],
    duration_sec: float,
    bpm: float,
    peaks: List[float],
    sentence_ends: List[float],
    fps: int,
    width: int,
    height: int,
) -> Dict[str, Any]:
    raw_scenes = raw_board.get("scenes") or []
    if not raw_scenes:
        raise ValueError("Storyboard returned empty scenes list.")

    snap_points = sorted(set(peaks + sentence_ends))
    count = len(raw_scenes)
    avg_len = duration_sec / count
    cursor = 0.0
    scenes: List[Dict[str, Any]] = []
    seen_concepts: set[str] = set()
    prev_backdrop = ""
    prev_transition = ""

    for idx, sc in enumerate(raw_scenes):
        is_last = idx == count - 1
        start_sec = round(cursor, 3)

        backdrop = str(sc.get("backdropTheme") or "").strip()
        if backdrop not in BACKDROP_THEMES:
            backdrop = BACKDROP_THEMES[idx % (len(BACKDROP_THEMES) - 1)]
        # Never repeat same backdrop on consecutive scenes
        if backdrop == prev_backdrop and backdrop != "black_title_card":
            b_idx = BACKDROP_THEMES.index(backdrop)
            backdrop = BACKDROP_THEMES[(b_idx + 1) % (len(BACKDROP_THEMES) - 1)]
        prev_backdrop = backdrop

        if is_last:
            end_sec = round(duration_sec, 3)
        else:
            raw_end = float(sc.get("endSec", (idx + 1) * avg_len))
            if backdrop == "black_title_card":
                target_dur = min(2.6, max(1.4, raw_end - start_sec))
                end_sec = round(min(duration_sec - 2.0, start_sec + target_dur), 3)
            else:
                min_gap = 2.8 if duration_sec <= 45 else 3.4
                max_gap = 8.2
                clamped = min(max(raw_end, start_sec + min_gap), min(start_sec + max_gap, duration_sec - (count - idx - 1) * 2.2))
                end_sec = snap_to_boundary(clamped, snap_points, start_sec + min_gap - 0.3, duration_sec - 1.8)
        cursor = end_sec

        concept = str(sc.get("visualConcept") or f"Scene Concept {idx + 1}").strip()[:110]
        if concept.lower() in seen_concepts:
            concept = f"{concept} ({idx + 1})"
        seen_concepts.add(concept.lower())

        cam = str(sc.get("cameraMove") or "").strip()
        if cam not in CAMERA_MOVES:
            cam = CAMERA_MOVES[idx % len(CAMERA_MOVES)]

        trans = str(sc.get("transition") or "").strip()
        if trans not in TRANSITIONS or trans == prev_transition:
            trans = TRANSITIONS[(idx + 1) % len(TRANSITIONS)]
        prev_transition = trans

        sfx = str(sc.get("sfx") or "").strip()
        if sfx not in SFX_CUES:
            sfx = "marker_swipe" if backdrop == "black_title_card" else SFX_CUES[idx % len(SFX_CUES)]

        accent_hex = sanitize_hex(sc.get("accentHex"), ["#22C55E", "#38BDF8", "#F97316", "#F59E0B", "#22D3EE"][idx % 5])

        local_peaks = [round(p - start_sec, 3) for p in peaks if start_sec + 0.25 <= p <= end_sec - 0.25]

        scenes.append(
            {
                "id": f"scene_{idx + 1:02d}",
                "componentName": f"Scene_{idx + 1:02d}",
                "visualConcept": concept,
                "visualSpec": str(sc.get("visualSpec") or concept)[:500],
                "titleText": str(sc.get("titleText") or "")[:45],
                "backdropTheme": backdrop,
                "cameraMove": cam,
                "transition": trans,
                "sfx": sfx,
                "accentHex": accent_hex,
                "startSec": start_sec,
                "endSec": end_sec,
                "localPeakTimes": local_peaks,
            }
        )

    return {
        "channel": "InfraVerse2D",
        "fps": fps,
        "width": width,
        "height": height,
        "totalDurationSec": round(duration_sec, 3),
        "hasAudio": True,
        "bpm": bpm,
        "emphasisPeaksSec": peaks,
        "scenes": scenes,
    }


def write_registry_and_timeline(plan: Dict[str, Any]) -> None:
    SCENES_DIR.mkdir(parents=True, exist_ok=True)
    fps = int(plan["fps"])
    total_frames = max(60, int(round(plan["totalDurationSec"] * fps)))

    imports: List[str] = []
    entries: List[str] = []
    for sc in plan["scenes"]:
        cname = sc["componentName"]
        imports.append(f'import {{ {cname} }} from "./scenes/{cname}";')
        entries.append(f'  {sc["id"]}: {cname},')

    registry_ts = (
        'import type React from "react";\n'
        'import type { Scene2DProps } from "../types";\n'
        + "\n".join(imports)
        + "\n\nexport const SCENE_REGISTRY: Record<string, React.FC<Scene2DProps>> = {\n"
        + "\n".join(entries)
        + "\n};\n"
    )
    (GENERATED_DIR / "SceneRegistry.ts").write_text(registry_ts, encoding="utf-8")

    scenes_data_ts = (
        'import type { CartoonPlan } from "../types";\n\n'
        f"export const SCENE_PLAN: CartoonPlan = {json.dumps(plan, indent=2, ensure_ascii=False)};\n"
    )
    (GENERATED_DIR / "ScenesData.ts").write_text(scenes_data_ts, encoding="utf-8")

    timeline_tsx = f"""import React from "react";
import {{ AbsoluteFill }} from "remotion";
import {{ CartoonStage2D }} from "../components/CartoonStage2D";
import {{ SCENE_PLAN }} from "./ScenesData";

export const GENERATED_TOTAL_FRAMES = {total_frames};

export const GeneratedTimeline: React.FC = () => {{
  return (
    <AbsoluteFill>
      <CartoonStage2D plan={{SCENE_PLAN}} />
    </AbsoluteFill>
  );
}};
"""
    (GENERATED_DIR / "GeneratedTimeline.tsx").write_text(timeline_tsx, encoding="utf-8")


def run_tsc_check() -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["npx", "tsc", "--noEmit"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
    )


def self_heal_scenes(client: Any, plan: Dict[str, Any]) -> None:
    scene_map = {sc["componentName"]: sc for sc in plan["scenes"]}

    for attempt in range(1, 3):
        res = run_tsc_check()
        if res.returncode == 0:
            print("[self_heal] TypeScript compiled cleanly with 0 errors!")
            return

        output = (res.stdout or "") + "\n" + (res.stderr or "")
        broken_names = sorted(set(re.findall(r"src/generated/scenes/(Scene_\d+)\.tsx", output)))
        if not broken_names:
            print(f"[self_heal] Non-scene tsc output:\n{output[:1200]}")
            break

        print(f"[self_heal] Attempt {attempt}: Repairing {len(broken_names)} scene(s): {broken_names}")
        for cname in broken_names:
            sc_path = SCENES_DIR / f"{cname}.tsx"
            broken_code = sc_path.read_text(encoding="utf-8") if sc_path.exists() else ""
            err_lines = [ln for ln in output.splitlines() if cname in ln][:8]
            fix_prompt = f"""
Fix the TypeScript errors in `{cname}.tsx`.

{CARTOON_KIT_DOC}

ERRORS:
{chr(10).join(err_lines)}

CODE:
{broken_code}

Return ONLY the fixed complete TSX file.
"""
            try:
                fixed_raw = generate_with_fallback(client, fix_prompt, role="flash", json_mode=False)
                scene_num = int(cname.split("_")[1])
                sc_path.write_text(sanitize_scene_tsx(fixed_raw, scene_num), encoding="utf-8")
            except Exception as exc:
                print(f"[self_heal] Repair skipped for {cname} ({exc}).")
            time.sleep(2)

    final_res = run_tsc_check()
    if final_res.returncode != 0:
        final_out = (final_res.stdout or "") + "\n" + (final_res.stderr or "")
        still_broken = sorted(set(re.findall(r"src/generated/scenes/(Scene_\d+)\.tsx", final_out)))
        for cname in still_broken:
            num = int(cname.split("_")[1])
            sc_meta = scene_map.get(cname, {})
            print(f"[self_heal] Swapping stubborn {cname} to unique 2D cartoon fallback.")
            (SCENES_DIR / f"{cname}.tsx").write_text(
                build_safe_fallback_scene_tsx(
                    num,
                    sc_meta.get("backdropTheme", "night_mountains"),
                    sc_meta.get("accentHex", "#22C55E"),
                    sc_meta.get("visualConcept", cname),
                    sc_meta.get("titleText", ""),
                ),
                encoding="utf-8",
            )
        verify = run_tsc_check()
        if verify.returncode != 0:
            raise RuntimeError(f"TypeScript failed after fallbacks:\n{verify.stdout}\n{verify.stderr}")


def main() -> None:
    transcript = json.loads((WORK_DIR / "transcript.json").read_text(encoding="utf-8"))
    beats = json.loads((WORK_DIR / "beats.json").read_text(encoding="utf-8"))
    duration_sec = float(beats["duration_sec"])
    bpm = float(beats["bpm"])
    peaks = list(beats["emphasis_peaks"])
    sentence_ends = [float(s["end"]) for s in transcript.get("segments", [])]

    video_format = os.environ.get("VIDEO_FORMAT", "long_16_9").strip()
    quality = os.environ.get("QUALITY_PRESET", "1080p_30fps").strip()
    is_short = video_format == "short_9_16"

    if is_short:
        width, height, fps = 1080, 1920, 30
    elif quality == "720p_24fps":
        width, height, fps = 1280, 720, 24
    else:
        width, height, fps = 1920, 1080, 30

    input_dir = get_input_dir()
    visuals_prompt = load_visuals_prompt(input_dir)
    min_sc, max_sc = compute_scene_range(duration_sec, is_short=is_short)

    aspect_note = (
        "VERTICAL 9:16 SHORT (viewBox 0..1080 wide x 0..1920 tall): Stack foreground characters & machinery cleanly vertically (x around 200..880, y around 320..1550)."
        if is_short
        else "WIDESCREEN 16:9 (viewBox 0..1920 wide x 0..1080 tall): Compose foreground characters, cutaways, charts & callouts cleanly across the full frame (x 160..1760, y 140..960)."
    )

    storyboard_prompt = f"""
You are the Lead 2D Animated Explainer Director (exact Video-1 hand-inked 2D cartoon documentary style: expressive pill-characters, bold ink outlines, rich varied environments, visual metaphors, highlighter quotes, charts, and dramatic black handwritten title cards).

ASPECT:
{aspect_note}

USER VISUAL & STYLE DIRECTION (Follow EVERY environment style, mood, and element requested here!):
{visuals_prompt if visuals_prompt else "(No visuals.txt uploaded — design a richly varied Video-1-style cartoon visual journey matching every sentence of the narration!)"}

VOICEOVER SEGMENTS ({duration_sec:.2f}s):
{json.dumps([{"start": s["start"], "end": s["end"], "text": s["text"]} for s in transcript.get("segments", [])], ensure_ascii=False)}

VOCAL EMPHASIS PEAKS (seconds):
{json.dumps(peaks[:120])}

AVAILABLE BACKDROP THEMES:
{json.dumps(BACKDROP_THEMES)}

AVAILABLE CAMERA MOVES: {json.dumps(CAMERA_MOVES)}
AVAILABLE TRANSITIONS: {json.dumps(TRANSITIONS)}
AVAILABLE SFX CUES: {json.dumps(SFX_CUES)}

HARD STORYBOARD RULES:
1. Break the {duration_sec:.2f}s voiceover into {min_sc} to {max_sc} snappy scenes synced to exact sentence boundaries!
   - Normal cartoon scenes MUST stay 3.5 to 8.0 seconds (never dull long holds).
   - Drop 2–4 short `black_title_card` scenes (1.5–2.3s long, with a punchy 2–4 word `titleText` like `"Nobody noticed."`, `"The Cooling Trap"`, `"Zero Margin."`) right at major story turns!
2. ZERO VISUAL REPETITION: Every scene MUST have a unique `visualConcept` AND vary `backdropTheme` and `transition` across consecutive scenes so it feels genuinely human-edited!
3. MATCH SPOKEN NOUNS & METAPHORS LITERALLY: Use `SplitScreen3Panel` when listing 3 things (`bank / substation / city`), `LineChart2D` or `BarChart2D` for surging power/costs, `BalanceScale2D` for comparisons, `ConveyorBelt2D` for chip generations, `WorldMapArc2D` for subsea cables/global routes, `QuoteHighlight2D` for reports/quotes, `CartoonCharacter2D` reacting emotionally, and `ReactorVessel2D` / `CoolingTower2D` / `ServerRack2D` / `Microchip2D` / `PowerPylon2D` / `BatteryBank2D` + custom SVG art!

Return ONLY valid JSON:
{{
  "scenes": [
    {{
      "visualConcept": "Short unique concept summary",
      "visualSpec": "Specific 2D layout, characters, moods, props, callout text, chart/scale numbers & animations synced to spoken words",
      "titleText": "Optional short text if backdropTheme is black_title_card",
      "backdropTheme": "night_mountains",
      "cameraMove": "push_in",
      "transition": "slide_left",
      "sfx": "sub_impact",
      "accentHex": "#22C55E",
      "endSec": 6.7
    }}
  ]
}}
"""

    client = get_client()
    print(f"[generate_scenes] Planning Video-1 2D storyboard from {input_dir.name}/ ({width}x{height} @ {fps}fps)...")
    raw_board = generate_with_fallback(client, storyboard_prompt, role="pro", json_mode=True)
    plan = normalize_storyboard(
        parse_json_strict(raw_board),
        duration_sec=duration_sec,
        bpm=bpm,
        peaks=peaks,
        sentence_ends=sentence_ends,
        fps=fps,
        width=width,
        height=height,
    )
    (WORK_DIR / "scene_plan.json").write_text(json.dumps(plan, indent=2, ensure_ascii=False), encoding="utf-8")

    SCENES_DIR.mkdir(parents=True, exist_ok=True)
    for old_file in SCENES_DIR.glob("Scene_*.tsx"):
        old_file.unlink()

    scenes = plan["scenes"]
    batch_size = 4
    print(f"[generate_scenes] Drawing {len(scenes)} unique 2D cartoon scenes in batches of {batch_size}...")

    for b_start in range(0, len(scenes), batch_size):
        batch = scenes[b_start : b_start + batch_size]
        batch_specs = [
            {
                "componentName": sc["componentName"],
                "visualConcept": sc["visualConcept"],
                "visualSpec": sc["visualSpec"],
                "titleText": sc["titleText"],
                "backdropTheme": sc["backdropTheme"],
                "accentHex": sc["accentHex"],
                "durationSec": round(sc["endSec"] - sc["startSec"], 2),
                "localPeakTimes": sc["localPeakTimes"],
            }
            for sc in batch
        ]
        code_prompt = f"""
You are an Expert 2D Cartoon Vector Animator coding SVG + CartoonKit2D scenes in Remotion.
{aspect_note}
{CARTOON_KIT_DOC}

BATCH TO ILLUSTRATE (Make EVERY scene visually rich, lively, full of motion, with bold #111827 ink outlines, expressive CartoonCharacter2D reactions, animated charts/scales/cutaways/pipes, and clean InkCallout2D stats synced to localPeakTimes):
{json.dumps(batch_specs, indent=2)}

Return ONLY valid JSON mapping each exact `componentName` (e.g. "Scene_01") to its complete valid TSX file string starting with `import React from "react";`.
"""
        try:
            raw_code_json = generate_with_fallback(
                client,
                code_prompt,
                role="flash",
                json_mode=True,
                max_output_tokens=65536,
            )
            generated_map = extract_scenes_dict(raw_code_json)
        except Exception as exc:
            print(f"[generate_scenes] Batch {b_start+1} API failed ({exc}); using 2D fallbacks.")
            generated_map = {}

        for sc in batch:
            cname = sc["componentName"]
            num = int(cname.split("_")[1])
            raw_tsx = generated_map.get(cname, "")
            out_path = SCENES_DIR / f"{cname}.tsx"
            try:
                if not raw_tsx.strip():
                    raise ValueError(f"Empty code returned for {cname}")
                out_path.write_text(sanitize_scene_tsx(raw_tsx, num), encoding="utf-8")
                print(f"  + Illustrated {cname}.tsx [{sc['backdropTheme']}] ({sc['visualConcept'][:44]})")
            except Exception as exc:
                print(f"  ! {cname} sanitize issue ({exc}); writing unique 2D fallback.")
                out_path.write_text(
                    build_safe_fallback_scene_tsx(
                        num,
                        sc["backdropTheme"],
                        sc["accentHex"],
                        sc["visualConcept"],
                        sc["titleText"],
                    ),
                    encoding="utf-8",
                )

        if b_start + batch_size < len(scenes):
            time.sleep(4)

    write_registry_and_timeline(plan)
    self_heal_scenes(client, plan)
    print(f"[generate_scenes] Complete: {len(scenes)} unique 2D cartoon scenes verified!")


if __name__ == "__main__":
    main()

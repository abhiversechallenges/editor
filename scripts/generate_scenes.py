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
    "isometric_blueprint",
    "xray_cutaway",
    "substation_grid",
    "cleanroom_fab",
    "thermal_flow",
    "server_corridor",
    "dark_industrial",
    "black_title_card",
    "split_3panel",
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

BLUEPRINT_KIT_DOC = """
Available components in "../../components/CartoonKit2D" (ONLY import React, CartoonKit2D components, and Scene2DProps):
import React from "react";
import {
  SceneBackdrop2D, Camera2D, TitleCard2D, TechnicalCallout2D,
  LineChart2D, BarChart2D, BalanceScale2D, TelemetryHUD2D,
  AnimatedFluidPipe2D, MicrochannelColdPlate2D, ServerRack800kW2D,
  TransformerSubstation2D, NuclearSMRVessel2D, Microchip2D,
  PowerPylon2D, BatteryBank2D, SplitScreen3Panel
} from "../../components/CartoonKit2D";
import type { Scene2DProps } from "../../types";

Props Reference (Canvas is 1920x1080 SVG viewBox, or 1080x1920 when isVertical is true):
- SceneBackdrop2D: { theme: BackdropTheme; frame: number; accentHex?: string }
- Camera2D: { move: CameraMove2D; progress: number; frame: number; peakTimes?: number[]; localTime: number; children?: React.ReactNode }
- TelemetryHUD2D: { x: number; y: number; title: string; metrics: { label: string; value: string; unit?: string; alert?: boolean }[]; progress: number }
- AnimatedFluidPipe2D: { d: string; color?: string; fluidColor?: string; strokeWidth?: number; frame: number }
- MicrochannelColdPlate2D: { x: number; y: number; scale?: number; coolantTempC?: number; frame: number; progress: number }
- ServerRack800kW2D: { x: number; y: number; scale?: number; accentHex?: string; frame: number; progress: number }
- TransformerSubstation2D: { x: number; y: number; scale?: number; voltageKV?: number; frame: number }
- NuclearSMRVessel2D: { x: number; y: number; scale?: number; cherenkovGlow?: boolean; frame: number; progress: number }
- Microchip2D: { x: number; y: number; scale?: number; color?: string; cracked?: boolean; overheating?: boolean; frame: number; progress: number }
- PowerPylon2D: { x: number; y: number; scale?: number; accentHex?: string; frame: number }
- BatteryBank2D: { x: number; y: number; scale?: number; accentHex?: string; frame: number; progress: number }
- TechnicalCallout2D: { x: number; y: number; text: string; subtext?: string; color?: string; localTime: number; delaySec?: number; arrowTo?: [number, number] }
- TitleCard2D: { text: string; progress: number; accentHex?: string }
- LineChart2D: { x: number; y: number; w?: number; h?: number; label?: string; startVal?: number; endVal?: number; prefix?: string; suffix?: string; color?: string; progress: number }
- BarChart2D: { x: number; y: number; w?: number; h?: number; bars: { label: string; value: number; color?: string }[]; progress: number }
- BalanceScale2D: { x: number; y: number; leftLabel: string; rightLabel: string; tiltDeg?: number; leftColor?: string; rightColor?: string; progress: number }
- SplitScreen3Panel: { progress: number; panel1: React.ReactNode; panel2: React.ReactNode; panel3: React.ReactNode }

CRITICAL RULES:
1. Export EXACTLY `export const Scene_XX: React.FC<Scene2DProps> = (props) => { ... }`.
2. Return a single `<svg viewBox={props.isVertical ? "0 0 1080 1920" : "0 0 1920 1080"} style={{ width: "100%", height: "100%", display: "block" }}>`.
3. NEVER put <div> or <span> inside <svg>. Every element inside must be valid SVG (<g>, <rect>, <path>, <text>) or a CartoonKit2D component.
4. NEVER import `three`, `remotion`, `useEffect`, or `useState`.
"""

FORBIDDEN_CODE_PATTERNS = (
    "<div", "<span", "useFrame", "useEffect", "useState", "from 'three'", 'from "three"', "@react-three", "from 'remotion'", 'from "remotion"'
)


def get_input_dir() -> Path:
    folder = os.environ.get("INPUT_FOLDER", "input").strip() or "input"
    return ROOT / folder


def load_visuals_prompt(input_dir: Path) -> str:
    if not input_dir.exists():
        return ""
    candidates = [
        p for p in input_dir.iterdir()
        if p.is_file() and p.suffix.lower() == ".txt" and p.name != "visuals_EXAMPLE.txt"
    ]
    if not candidates:
        return ""
    for p in candidates:
        if p.name.lower() == "visuals.txt":
            return p.read_text(encoding="utf-8").strip()
    return candidates[0].read_text(encoding="utf-8").strip()


def build_fallback_scene_tsx(scene_num: int, backdrop: str, accent: str, concept: str, title_text: str) -> str:
    variant = scene_num % 5
    if backdrop == "black_title_card":
        inner = f'<TitleCard2D text={{{json.dumps(title_text or concept[:30])}}} progress={{progress}} accentHex={{{json.dumps(accent)}}} />'
    elif variant == 0:
        inner = f"""
      <MicrochannelColdPlate2D x={{isVertical ? 540 : 860}} y={{isVertical ? 960 : 540}} scale={{1.3}} coolantTempC={{62}} frame={{frame}} progress={{progress}} />
      <TelemetryHUD2D x={{isVertical ? 120 : 120}} y={{isVertical ? 240 : 180}} title="COLD PLATE TELEMETRY" metrics={{[{{ label: "INLET TEMP", value: "32.4", unit: "C" }}, {{ label: "OUTLET TEMP", value: "62.1", unit: "C", alert: true }}, {{ label: "FLOW RATE", value: "2.1", unit: "LPM" }}]}} progress={{progress}} />
      <TechnicalCallout2D x={{isVertical ? 540 : 1420}} y={{isVertical ? 1520 : 480}} text="40um MICROCHANNELS" subtext="Direct Copper Interface" color={{{json.dumps(accent)}}} localTime={{localTime}} delaySec={{0.2}} arrowTo={{[isVertical ? 540 : 960, isVertical ? 960 : 540]}} />"""
    elif variant == 1:
        inner = f"""
      <ServerRack800kW2D x={{isVertical ? 540 : 720}} y={{isVertical ? 920 : 540}} scale={{1.2}} accentHex={{{json.dumps(accent)}}} frame={{frame}} progress={{progress}} />
      <TelemetryHUD2D x={{isVertical ? 120 : 1320}} y={{isVertical ? 240 : 200}} title="RACK POWER SPEC" metrics={{[{{ label: "RACK LOAD", value: "132.8", unit: "kW", alert: true }}, {{ label: "BUSBAR V", value: "48.0", unit: "V DC" }}, {{ label: "CDU DELTA-P", value: "14.2", unit: "PSI" }}]}} progress={{progress}} />
      <AnimatedFluidPipe2D d={{isVertical ? "M 180 500 L 540 500 L 540 1400" : "M 200 840 L 720 840 L 720 340"}} fluidColor="#00F0FF" frame={{frame}} />"""
    elif variant == 2:
        inner = f"""
      <TransformerSubstation2D x={{isVertical ? 540 : 960}} y={{isVertical ? 980 : 570}} scale={{1.25}} voltageKV={{345}} frame={{frame}} />
      <TelemetryHUD2D x={{isVertical ? 120 : 160}} y={{isVertical ? 240 : 180}} title="GRID INTERCONNECTION" metrics={{[{{ label: "GRID VOLTAGE", value: "345", unit: "kV" }}, {{ label: "INTERCONNECT QUEUE", value: "4.2", unit: "YRS", alert: true }}, {{ label: "TRANSFORMER EFF", value: "99.2", unit: "%" }}]}} progress={{progress}} />
      <TechnicalCallout2D x={{isVertical ? 540 : 1440}} y={{isVertical ? 1480 : 420}} text="345 kV STEP-DOWN" subtext="Grain-Oriented Steel Core" color="#F59E0B" localTime={{localTime}} delaySec={{0.3}} />"""
    elif variant == 3:
        inner = f"""
      <NuclearSMRVessel2D x={{isVertical ? 540 : 880}} y={{isVertical ? 980 : 560}} scale={{1.25}} cherenkovGlow={{true}} frame={{frame}} progress={{progress}} />
      <TelemetryHUD2D x={{isVertical ? 120 : 1340}} y={{isVertical ? 240 : 220}} title="SMR CORE STATS" metrics={{[{{ label: "THERMAL MW", value: "300", unit: "MWt" }}, {{ label: "ELECTRIC MW", value: "100", unit: "MWe" }}, {{ label: "CAPACITY FACTOR", value: "96.4", unit: "%" }}]}} progress={{progress}} />
      <AnimatedFluidPipe2D d={{isVertical ? "M 200 600 L 540 600 L 540 1300" : "M 300 780 L 880 780 L 880 320"}} fluidColor="#38BDF8" frame={{frame}} />"""
    else:
        inner = f"""
      <LineChart2D x={{isVertical ? 140 : 380}} y={{isVertical ? 540 : 260}} w={{isVertical ? 800 : 1160}} h={{520}} label="CAMPUS LOAD SURGE" startVal={{120}} endVal={{1000}} suffix=" MW" color="#EF4444" progress={{progress}} />
      <TelemetryHUD2D x={{isVertical ? 120 : 140}} y={{isVertical ? 240 : 220}} title="GRID CAPACITY" metrics={{[{{ label: "INITIAL", value: "120", unit: "MW" }}, {{ label: "TARGET", value: "1,000", unit: "MW", alert: true }}]}} progress={{progress}} />"""

    return f"""import React from "react";
import {{
  SceneBackdrop2D, Camera2D, TitleCard2D, TechnicalCallout2D,
  LineChart2D, TelemetryHUD2D, AnimatedFluidPipe2D,
  MicrochannelColdPlate2D, ServerRack800kW2D, TransformerSubstation2D, NuclearSMRVessel2D
}} from "../../components/CartoonKit2D";
import type {{ Scene2DProps }} from "../../types";

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
            raise ValueError(f"Forbidden token '{bad}' found in Scene_{scene_num:02d}")
    expected = f"Scene_{scene_num:02d}"
    if expected not in txt:
        txt = re.sub(r"export\s+const\s+Scene_\d+\s*:", f"export const {expected}:", txt)
    if expected not in txt:
        raise ValueError(f"Missing export {expected}")
    return txt.strip() + "\n"


def run_tsc_check() -> subprocess.CompletedProcess[str]:
    return subprocess.run(["npx", "tsc", "--noEmit"], cwd=str(ROOT), capture_output=True, text=True, check=False)


def self_heal_scenes(client: Any, plan: Dict[str, Any]) -> None:
    scene_map = {sc["componentName"]: sc for sc in plan["scenes"]}
    for attempt in range(1, 3):
        res = run_tsc_check()
        if res.returncode == 0:
            print("[self_heal] TypeScript compiled cleanly with 0 errors!")
            return
        output = (res.stdout or "") + "\n" + (res.stderr or "")
        broken = sorted(set(re.findall(r"src/generated/scenes/(Scene_\d+)\.tsx", output)))
        if not broken:
            break
        print(f"[self_heal] Attempt {attempt}: Repairing {len(broken)} scene(s)...")
        for cname in broken:
            sc_path = SCENES_DIR / f"{cname}.tsx"
            code = sc_path.read_text(encoding="utf-8") if sc_path.exists() else ""
            err_lines = [ln for ln in output.splitlines() if cname in ln][:6]
            fix_prompt = f"Fix TS errors in `{cname}.tsx`.\n{BLUEPRINT_KIT_DOC}\nERRORS:\n{chr(10).join(err_lines)}\nCODE:\n{code}\nReturn ONLY valid fixed TSX."
            try:
                fixed = generate_with_fallback(client, fix_prompt, role="flash", json_mode=False)
                sc_path.write_text(sanitize_scene_tsx(fixed, int(cname.split("_")[1])), encoding="utf-8")
            except Exception as exc:
                print(f"[self_heal] Repair skipped for {cname}: {exc}")
            time.sleep(3)

    final_res = run_tsc_check()
    if final_res.returncode != 0:
        final_out = (final_res.stdout or "") + "\n" + (final_res.stderr or "")
        still_broken = sorted(set(re.findall(r"src/generated/scenes/(Scene_\d+)\.tsx", final_out)))
        for cname in still_broken:
            num = int(cname.split("_")[1])
            sc_meta = scene_map.get(cname, {})
            print(f"[self_heal] Swapping stubborn {cname} to clean 2D blueprint fallback.")
            (SCENES_DIR / f"{cname}.tsx").write_text(
                build_fallback_scene_tsx(num, sc_meta.get("backdropTheme", "isometric_blueprint"), sc_meta.get("accentHex", "#00F0FF"), sc_meta.get("visualConcept", cname), sc_meta.get("titleText", "")),
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

    video_format = os.environ.get("VIDEO_FORMAT", "long_16_9").strip()
    is_short = video_format == "short_9_16"
    width, height, fps = (1080, 1920, 30) if is_short else (1920, 1080, 30)

    input_dir = get_input_dir()
    visuals_prompt = load_visuals_prompt(input_dir)
    scene_count = max(4, min(140, int(round(duration_sec / 5.5))))
    avg_dur = duration_sec / scene_count

    storyboard_prompt = f"""
You are the Lead Visual Director for CoreToGrid (70%+ retention 2D/2.5D Technical CAD & Blueprint Documentary).
Total Duration: {duration_sec:.2f}s | Target Scenes: {scene_count}
Niche: AI Hardware, 800kW Data Center Engineering & Energy Infrastructure.

VOICEOVER TRANSCRIPT:
{json.dumps([{"start": s["start"], "end": s["end"], "text": s["text"]} for s in transcript.get("segments", [])], ensure_ascii=False)}

USER DIRECTIVES:
{visuals_prompt or "Create a deeply technical blueprint journey showing exact physical mechanisms, flow rates, and scale ladders."}

AVAILABLE THEMES: {json.dumps(BACKDROP_THEMES)}
AVAILABLE CAMERA MOVES: {json.dumps(CAMERA_MOVES)}

Return JSON with "scenes" array containing {scene_count} scenes. Every scene needs:
- visualConcept, visualSpec, backdropTheme, cameraMove
- transition ("slide_left"|"slide_up"|"wipe_right"|"zoom_dissolve"|"flash_cut")
- sfx ("sub_impact"|"whoosh"|"marker_swipe"|"pop_snap"|"tick")
- accentHex ("#00F0FF"|"#EF4444"|"#F59E0B"|"#10B981")
- titleText: punchy 2-4 words if backdropTheme is black_title_card
- endSec: float timestamp
"""

    client = get_client()
    print(f"[generate_scenes] Directing {scene_count} technical blueprint scenes...")
    raw_board = generate_with_fallback(client, storyboard_prompt, role="pro", json_mode=True)
    board = parse_json_strict(raw_board)

    raw_scenes = board.get("scenes", [])
    scenes = []
    cursor = 0.0
    for idx, sc in enumerate(raw_scenes):
        start_sec = round(cursor, 3)
        end_sec = round(float(sc.get("endSec", (idx + 1) * avg_dur)), 3)
        if idx == len(raw_scenes) - 1 or end_sec <= start_sec:
            end_sec = round(duration_sec, 3)
        cursor = end_sec

        backdrop = sc.get("backdropTheme") if sc.get("backdropTheme") in BACKDROP_THEMES else BACKDROP_THEMES[idx % len(BACKDROP_THEMES)]
        cname = f"Scene_{idx + 1:02d}"
        local_peaks = [round(p - start_sec, 3) for p in peaks if start_sec + 0.25 <= p <= end_sec - 0.25]

        scenes.append({
            "id": f"scene_{idx + 1:02d}",
            "componentName": cname,
            "visualConcept": sc.get("visualConcept", f"Engineering Metric {idx + 1}"),
            "visualSpec": sc.get("visualSpec", ""),
            "titleText": sc.get("titleText", ""),
            "backdropTheme": backdrop,
            "cameraMove": sc.get("cameraMove", "push_in"),
            "transition": sc.get("transition", "slide_left"),
            "sfx": sc.get("sfx", "pop_snap"),
            "accentHex": sc.get("accentHex", "#00F0FF"),
            "startSec": start_sec,
            "endSec": end_sec,
            "localPeakTimes": local_peaks,
        })

    plan = {
        "channel": "CoreToGrid",
        "fps": fps,
        "width": width,
        "height": height,
        "totalDurationSec": round(duration_sec, 3),
        "bpm": bpm,
        "scenes": scenes,
    }
    (WORK_DIR / "scene_plan.json").write_text(json.dumps(plan, indent=2, ensure_ascii=False), encoding="utf-8")

    SCENES_DIR.mkdir(parents=True, exist_ok=True)
    for f in SCENES_DIR.glob("Scene_*.tsx"):
        f.unlink()

    # Larger batches (10 scenes per call) keep total requests tiny so free-tier RPM/RPD never exhausts!
    batch_size = 10
    for b_start in range(0, len(scenes), batch_size):
        batch = scenes[b_start : b_start + batch_size]
        code_prompt = f"""
You are an Elite 2D Technical Vector Illustrator coding React SVG scenes in Remotion.
Canvas: {width}x{height} SVG.
{BLUEPRINT_KIT_DOC}

BATCH TO CODE:
{json.dumps([{"componentName": s["componentName"], "visualConcept": s["visualConcept"], "visualSpec": s["visualSpec"], "backdropTheme": s["backdropTheme"], "accentHex": s["accentHex"], "titleText": s["titleText"]} for s in batch], indent=2)}

Return ONLY JSON mapping each componentName (e.g. "Scene_01") to its complete TSX code starting with 'import React from "react";'.
"""
        generated_map = {}
        try:
            raw_tsx = generate_with_fallback(client, code_prompt, role="flash", json_mode=True)
            generated_map = extract_scenes_dict(raw_tsx)
        except Exception as exc:
            print(f"[generate_scenes] Batch {b_start+1} fallback ({exc})")

        for sc in batch:
            cname = sc["componentName"]
            s_num = int(cname.split("_")[1])
            code = generated_map.get(cname, "")
            out_file = SCENES_DIR / f"{cname}.tsx"
            try:
                if not code.strip():
                    raise ValueError("Empty code")
                out_file.write_text(sanitize_scene_tsx(code, s_num), encoding="utf-8")
                print(f"  + Illustrated {cname}.tsx [{sc['backdropTheme']}]")
            except Exception:
                out_file.write_text(
                    build_fallback_scene_tsx(s_num, sc["backdropTheme"], sc["accentHex"], sc["visualConcept"], sc["titleText"]),
                    encoding="utf-8",
                )

        if b_start + batch_size < len(scenes):
            time.sleep(13)  # Respect 5 RPM free-tier bursts smoothly

    imports = [f'import {{ {s["componentName"]} }} from "./scenes/{s["componentName"]}";' for s in scenes]
    entries = [f'  {s["id"]}: {s["componentName"]},' for s in scenes]
    registry_ts = 'import type React from "react";\nimport type { Scene2DProps } from "../types";\n' + "\n".join(imports) + "\n\nexport const SCENE_REGISTRY: Record<string, React.FC<Scene2DProps>> = {\n" + "\n".join(entries) + "\n};\n"
    (GENERATED_DIR / "SceneRegistry.ts").write_text(registry_ts, encoding="utf-8")

    (GENERATED_DIR / "ScenesData.ts").write_text(
        f'import type {{ CartoonPlan }} from "../types";\n\nexport const SCENE_PLAN: CartoonPlan = {json.dumps(plan, indent=2, ensure_ascii=False)};\n',
        encoding="utf-8",
    )

    total_frames = max(60, int(round(duration_sec * fps)))
    timeline_tsx = f"""import React from "react";
import {{ AbsoluteFill }} from "remotion";
import {{ CartoonStage2D }} from "../components/CartoonStage2D";
import {{ SCENE_PLAN }} from "./ScenesData";

export const GENERATED_TOTAL_FRAMES = {total_frames};

export const GeneratedTimeline: React.FC = () => (
  <AbsoluteFill>
    <CartoonStage2D plan={{SCENE_PLAN}} />
  </AbsoluteFill>
);
"""
    (GENERATED_DIR / "GeneratedTimeline.tsx").write_text(timeline_tsx, encoding="utf-8")

    self_heal_scenes(client, plan)
    print(f"[generate_scenes] Complete: {len(scenes)} technical blueprint scenes verified!")


if __name__ == "__main__":
    main()

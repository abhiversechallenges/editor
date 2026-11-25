import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gemini_helper import clean_tsx_text, generate_with_fallback, get_client, parse_json_strict

ROOT = Path(__file__).resolve().parent.parent
WORK_DIR = ROOT / "work"
GENERATED_DIR = ROOT / "src" / "generated"
SCENES_DIR = GENERATED_DIR / "scenes"

BACKDROP_THEMES = [
    "isometric_blueprint",
    "spec_document",
    "xray_cutaway",
    "thermal_flow",
    "us_grid_map",
    "substation_grid",
    "server_corridor",
    "black_title_card",
]

CAMERA_MOVES = ["push_in", "pull_out", "pan_right", "pan_left", "pan_up", "shake_hit"]
SFX_CUES = ["whoosh", "pop", "tick", "alert", "impact"]

BLUEPRINT_KIT_DOC = """
Available components in "../../components/CartoonKit2D":
import React from "react";
import {
  SceneBackdrop2D, Camera2D, TitleCard2D, TechnicalCallout2D,
  LineChart2D, BarChart2D, BalanceScale2D, TelemetryHUD2D, StatCounter2D, BlueprintStamp2D,
  DataHall25D, SpecDocument2D, USGridMap2D, AnimatedFluidPipe2D,
  MicrochannelColdPlate2D, ServerRack800kW2D, TransformerSubstation2D,
  NuclearSMRVessel2D, Microchip2D, PowerPylon2D, BatteryBank2D, SplitScreen3Panel
} from "../../components/CartoonKit2D";
import type { Scene2DProps } from "../../types";

Layout Rules (1920x1080 SVG, or 1080x1920 when isVertical is true):
- Render `<SceneBackdrop2D theme={props.backdropTheme} frame={props.frame} accentHex={props.accentHex} chapterTag={props.chapterTag} />` first.
- Wrap foreground in `<Camera2D move={props.cameraMove} progress={props.progress} frame={props.frame} peakTimes={props.peakTimes} localTime={props.localTime}>`.
- Keep hero visuals in left 65% (x: 60..1240), and fill right 30% with `<TelemetryHUD2D x={isVertical ? 120 : 1310} y={isVertical ? 160 : 120} w={isVertical ? 840 : 540} ... />`.
- Export EXACTLY `export const Scene_XX: React.FC<Scene2DProps> = (props) => { ... }`.
- Return single `<svg viewBox={props.isVertical ? "0 0 1080 1920" : "0 0 1920 1080"} style={{ width: "100%", height: "100%", display: "block" }}>`.
- NEVER use <div>, <span>, `three`, `remotion`, `useEffect`, or `useState`.
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
    candidates = [p for p in input_dir.iterdir() if p.is_file() and p.suffix.lower() == ".txt" and p.name != "visuals_EXAMPLE.txt"]
    if not candidates:
        return ""
    for p in candidates:
        if p.name.lower() == "visuals.txt":
            return p.read_text(encoding="utf-8").strip()
    return candidates[0].read_text(encoding="utf-8").strip()


def build_fallback_scene_tsx(scene_num: int, backdrop: str, accent: str, concept: str, title_text: str) -> str:
    variant = scene_num % 6
    if backdrop == "black_title_card":
        inner = f'<TitleCard2D text={{{json.dumps(title_text or concept[:32])}}} progress={{progress}} accentHex={{{json.dumps(accent)}}} />'
    elif variant == 0:
        inner = f"""
      <DataHall25D accentHex={{{json.dumps(accent)}}} frame={{frame}} progress={{progress}} isVertical={{isVertical}} />
      <TelemetryHUD2D x={{isVertical ? 120 : 1310}} y={{isVertical ? 160 : 120}} w={{isVertical ? 840 : 540}} title="DATA HALL TELEMETRY" metrics={{[{{ label: "CAMPUS POWER", value: "1,000", unit: "MW", barPct: 95 }}, {{ label: "RACK DENSITY", value: "600", unit: "kW", alert: true, barPct: 90 }}, {{ label: "TOTAL CAPEX", value: "$100", unit: "B", barPct: 82 }}]}} progress={{progress}} />"""
    elif variant == 1:
        inner = f"""
      <SpecDocument2D x={{isVertical ? 80 : 70}} y={{isVertical ? 360 : 150}} w={{isVertical ? 920 : 1160}} title="$100B AI INFRASTRUCTURE CAPEX SPLIT" items={{[{{ label: "COMPUTE SILICON & INTERCONNECT", value: "$55B", pct: 88, color: "#00F0FF" }}, {{ label: "HIGH-VOLTAGE SUBSTATIONS & GRID", value: "$25B", pct: 55, color: "#F59E0B" }}, {{ label: "LIQUID COOLING & CHILLER PLANTS", value: "$20B", pct: 44, color: "#EF4444" }}]}} progress={{progress}} />
      <TelemetryHUD2D x={{isVertical ? 120 : 1310}} y={{isVertical ? 1300 : 120}} w={{isVertical ? 840 : 540}} title="CAPITAL INTENSITY" metrics={{[{{ label: "COST PER MW", value: "$100", unit: "M", barPct: 88 }}, {{ label: "COOLING SHARE", value: "20", unit: "%", alert: true, barPct: 65 }}]}} progress={{progress}} />"""
    elif variant == 2:
        inner = f"""
      <BarChart2D x={{isVertical ? 100 : 90}} y={{isVertical ? 460 : 200}} w={{isVertical ? 880 : 1120}} h={{500}} bars={{[{{ label: "2020 AIR RACK", value: 12, suffix: " kW", color: "#38BDF8" }}, {{ label: "2024 AI POD", value: 130, suffix: " kW", color: "#F59E0B" }}, {{ label: "2026 LIQUID", value: 600, suffix: " kW", color: "#EF4444" }}]}} progress={{progress}} />
      <TelemetryHUD2D x={{isVertical ? 120 : 1310}} y={{isVertical ? 1260 : 120}} w={{isVertical ? 840 : 540}} title="THERMAL WALL" metrics={{[{{ label: "AIR CEILING", value: "35", unit: "kW", barPct: 30 }}, {{ label: "LIQUID TARGET", value: "600", unit: "kW", alert: true, barPct: 96 }}]}} progress={{progress}} />"""
    elif variant == 3:
        inner = f"""
      <MicrochannelColdPlate2D x={{isVertical ? 540 : 640}} y={{isVertical ? 820 : 470}} scale={{1.25}} coolantTempC={{45}} frame={{frame}} progress={{progress}} />
      <AnimatedFluidPipe2D d={{isVertical ? "M 140 1200 L 940 1200" : "M 120 880 L 1200 880"}} fluidColor="#00F0FF" label="CHILLED COOLANT IN -> 18C" labelX={{isVertical ? 540 : 420}} labelY={{isVertical ? 1160 : 840}} frame={{frame}} />
      <AnimatedFluidPipe2D d={{isVertical ? "M 940 1300 L 140 1300" : "M 1200 965 L 120 965"}} fluidColor="#EF4444" label="<- HEATED RETURN 45C" labelX={{isVertical ? 540 : 880}} labelY={{isVertical ? 1345 : 1005}} frame={{frame}} />
      <TelemetryHUD2D x={{isVertical ? 120 : 1310}} y={{isVertical ? 160 : 120}} w={{isVertical ? 840 : 540}} title="COLD PLATE TELEMETRY" metrics={{[{{ label: "COOLANT INLET", value: "18.0", unit: "C", barPct: 36 }}, {{ label: "COOLANT OUTLET", value: "45.0", unit: "C", alert: true, barPct: 86 }}, {{ label: "FLOW RATE", value: "2.4", unit: "LPM", barPct: 72 }}]}} progress={{progress}} />"""
    elif variant == 4:
        inner = f"""
      <USGridMap2D x={{isVertical ? 60 : 70}} y={{isVertical ? 450 : 160}} w={{isVertical ? 960 : 1160}} h={{680}} accentHex="#F59E0B" frame={{frame}} progress={{progress}} />
      <AnimatedFluidPipe2D d={{isVertical ? "M 120 1250 L 960 1250" : "M 80 940 L 1220 940"}} fluidColor="#F59E0B" label="345 kV INTERCONNECT BUS" labelX={{isVertical ? 540 : 650}} labelY={{isVertical ? 1210 : 900}} frame={{frame}} />
      <TelemetryHUD2D x={{isVertical ? 120 : 1310}} y={{isVertical ? 160 : 120}} w={{isVertical ? 840 : 540}} title="NATIONAL GRID QUEUE" metrics={{[{{ label: "GRID VOLTAGE", value: "345", unit: "kV", barPct: 82 }}, {{ label: "TRANSFORMER WAIT", value: "3.8", unit: "YRS", alert: true, barPct: 92 }}]}} progress={{progress}} />"""
    else:
        inner = f"""
      <TransformerSubstation2D x={{isVertical ? 540 : 640}} y={{isVertical ? 840 : 500}} scale={{1.2}} voltageKV={{345}} frame={{frame}} />
      <AnimatedFluidPipe2D d={{isVertical ? "M 120 1260 L 960 1260" : "M 100 940 L 1200 940"}} fluidColor="#F59E0B" label="345 kV POWER BUS" labelX={{isVertical ? 540 : 650}} labelY={{isVertical ? 1220 : 900}} frame={{frame}} />
      <TelemetryHUD2D x={{isVertical ? 120 : 1310}} y={{isVertical ? 160 : 120}} w={{isVertical ? 840 : 540}} title="SUBSTATION STATUS" metrics={{[{{ label: "GRID QUEUE", value: "2,600", unit: "GW", alert: true, barPct: 94 }}, {{ label: "EFFICIENCY", value: "99.2", unit: "%", barPct: 99 }}]}} progress={{progress}} />"""

    return f"""import React from "react";
import {{
  SceneBackdrop2D, Camera2D, TitleCard2D, DataHall25D, SpecDocument2D,
  BarChart2D, MicrochannelColdPlate2D, USGridMap2D, TransformerSubstation2D,
  TelemetryHUD2D, AnimatedFluidPipe2D
}} from "../../components/CartoonKit2D";
import type {{ Scene2DProps }} from "../../types";

export const Scene_{scene_num:02d}: React.FC<Scene2DProps> = (props) => {{
  const {{ frame, localTime, progress, peakTimes, accentHex, backdropTheme, cameraMove, chapterTag, isVertical }} = props;
  const vb = isVertical ? "0 0 1080 1920" : "0 0 1920 1080";
  return (
    <svg viewBox={{vb}} style={{{{ width: "100%", height: "100%", display: "block" }}}}>
      <SceneBackdrop2D theme={{backdropTheme}} frame={{frame}} accentHex={{accentHex}} chapterTag={{chapterTag}} />
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
            raise ValueError(f"Forbidden token '{bad}' in Scene_{scene_num:02d}")
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
            time.sleep(2)

    final_res = run_tsc_check()
    if final_res.returncode != 0:
        final_out = (final_res.stdout or "") + "\n" + (final_res.stderr or "")
        still_broken = sorted(set(re.findall(r"src/generated/scenes/(Scene_\d+)\.tsx", final_out)))
        for cname in still_broken:
            num = int(cname.split("_")[1])
            sc_meta = scene_map.get(cname, {})
            print(f"[self_heal] Swapping stubborn {cname} to elite 2.5D blueprint fallback.")
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
    scene_count = max(4, min(180, int(round(duration_sec / 4.8))))
    avg_dur = duration_sec / scene_count

    storyboard_prompt = f"""
You are the Lead Visual Director for CoreToGrid (70%+ retention 2.5D Technical Blueprint Documentary).
Total Duration: {duration_sec:.2f}s | Target Scenes: {scene_count} (CHANGE VISUAL LAYOUT EVERY 4 TO 6 SECONDS!)

SEGMENTS:
{json.dumps([{"start": s["start"], "end": s["end"], "text": s["text"]} for s in transcript.get("segments", [])], ensure_ascii=False)}

VOCAL EMPHASIS PEAKS (seconds): {json.dumps(peaks[:100])}
USER DIRECTIVES: {visuals_prompt or "Rotate rapidly across: (1) DataHall25D + Right HUD + Labeled Pipes, (2) SpecDocument2D Capex Split, (3) BarChart2D / LineChart2D, (4) Cold Plate Cross-Section, (5) USGridMap2D + Transformer Nodes, (6) TitleCard2D."}
AVAILABLE THEMES: {json.dumps(BACKDROP_THEMES)}
AVAILABLE CAMERA MOVES: {json.dumps(CAMERA_MOVES)}
AVAILABLE SFX: {json.dumps(SFX_CUES)}

Return JSON with "scenes" array containing {scene_count} scenes. Every scene MUST have:
- chapterTag, visualConcept, visualSpec, backdropTheme (no repeats), cameraMove, transition ("slide_left"|"slide_up"|"wipe_right"|"zoom_dissolve"|"flash_cut"), sfx, accentHex, titleText
- stampText (2-word stamp like "600 KW HEAT"), stampColor, stampTriggerSec
- statCounter: {{"label": "METRIC", "startVal": 0, "endVal": 1.12, "prefix": "", "suffix": " PUE", "decimals": 2, "color": "#00F0FF", "triggerSec": 0.2}}
- endSec (3.8 to 6.2s per scene)
"""

    client = get_client()
    print(f"[generate_scenes] Directing {scene_count} rapid-cut 2.5D blueprint scenes...")
    raw_board = generate_with_fallback(client, storyboard_prompt, role="pro", json_mode=True)
    board = parse_json_strict(raw_board)

    raw_scenes = board.get("scenes", [])
    scenes = []
    cursor = 0.0
    prev_theme = ""
    for idx, sc in enumerate(raw_scenes):
        start_sec = round(cursor, 3)
        raw_end = float(sc.get("endSec", (idx + 1) * avg_dur))
        clamped_end = min(max(raw_end, start_sec + 3.6), start_sec + 6.4)
        end_sec = round(duration_sec, 3) if idx == len(raw_scenes) - 1 else round(min(clamped_end, duration_sec - (len(raw_scenes) - idx - 1) * 2.5), 3)
        if end_sec <= start_sec:
            end_sec = round(min(duration_sec, start_sec + 4.0), 3)
        cursor = end_sec

        backdrop = sc.get("backdropTheme") if sc.get("backdropTheme") in BACKDROP_THEMES else BACKDROP_THEMES[idx % len(BACKDROP_THEMES)]
        if backdrop == prev_theme and backdrop != "black_title_card":
            backdrop = BACKDROP_THEMES[(BACKDROP_THEMES.index(backdrop) + 1) % (len(BACKDROP_THEMES) - 1)]
        prev_theme = backdrop

        cname = f"Scene_{idx + 1:02d}"
        local_peaks = [round(p - start_sec, 3) for p in peaks if start_sec + 0.2 <= p <= end_sec - 0.2]
        sfx = sc.get("sfx") if sc.get("sfx") in SFX_CUES else SFX_CUES[idx % len(SFX_CUES)]

        scenes.append({
            "id": f"scene_{idx + 1:02d}",
            "componentName": cname,
            "chapterTag": str(sc.get("chapterTag") or f"{(idx // 4) + 1:02d} // CORE TO GRID")[:38],
            "visualConcept": str(sc.get("visualConcept") or f"Blueprint Step {idx + 1}"),
            "visualSpec": str(sc.get("visualSpec") or ""),
            "titleText": str(sc.get("titleText") or ""),
            "stampText": str(sc.get("stampText") or "")[:24],
            "stampColor": str(sc.get("stampColor") or "#EF4444"),
            "stampTriggerSec": float(sc.get("stampTriggerSec") or (local_peaks[0] if local_peaks else 0.7)),
            "statCounter": sc.get("statCounter") if isinstance(sc.get("statCounter"), dict) else None,
            "backdropTheme": backdrop,
            "cameraMove": sc.get("cameraMove") if sc.get("cameraMove") in CAMERA_MOVES else CAMERA_MOVES[idx % len(CAMERA_MOVES)],
            "transition": sc.get("transition", "slide_left"),
            "sfx": sfx,
            "accentHex": sc.get("accentHex", "#00F0FF"),
            "startSec": start_sec,
            "endSec": end_sec,
            "localPeakTimes": local_peaks,
        })

    plan = {"channel": "CoreToGrid", "fps": fps, "width": width, "height": height, "totalDurationSec": round(duration_sec, 3), "bpm": bpm, "emphasisPeaksSec": peaks, "scenes": scenes}
    (WORK_DIR / "scene_plan.json").write_text(json.dumps(plan, indent=2, ensure_ascii=False), encoding="utf-8")

    SCENES_DIR.mkdir(parents=True, exist_ok=True)
    for f in SCENES_DIR.glob("Scene_*.tsx"):
        f.unlink()

    batch_size = 10
    for b_start in range(0, len(scenes), batch_size):
        batch = scenes[b_start : b_start + batch_size]
        code_prompt = f"""
Code these React SVG scenes in Remotion ({width}x{height}). Keep Right 30% filled with TelemetryHUD2D!
{BLUEPRINT_KIT_DOC}
BATCH:
{json.dumps([{"componentName": s["componentName"], "chapterTag": s["chapterTag"], "visualConcept": s["visualConcept"], "visualSpec": s["visualSpec"], "backdropTheme": s["backdropTheme"], "accentHex": s["accentHex"], "titleText": s["titleText"]} for s in batch], indent=2)}
Return ONLY JSON mapping each componentName to its TSX file string.
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
                out_file.write_text(build_fallback_scene_tsx(s_num, sc["backdropTheme"], sc["accentHex"], sc["visualConcept"], sc["titleText"]), encoding="utf-8")

        if b_start + batch_size < len(scenes):
            time.sleep(10)

    imports = [f'import {{ {s["componentName"]} }} from "./scenes/{s["componentName"]}";' for s in scenes]
    entries = [f'  {s["id"]}: {s["componentName"]},' for s in scenes]
    (GENERATED_DIR / "SceneRegistry.ts").write_text(
        'import type React from "react";\nimport type { Scene2DProps } from "../types";\n' + "\n".join(imports) + "\n\nexport const SCENE_REGISTRY: Record<string, React.FC<Scene2DProps>> = {\n" + "\n".join(entries) + "\n};\n",
        encoding="utf-8",
    )
    (GENERATED_DIR / "ScenesData.ts").write_text(f'import type {{ CartoonPlan }} from "../types";\n\nexport const SCENE_PLAN: CartoonPlan = {json.dumps(plan, indent=2, ensure_ascii=False)};\n', encoding="utf-8")

    total_frames = max(60, int(round(duration_sec * fps)))
    (GENERATED_DIR / "GeneratedTimeline.tsx").write_text(
        f"""import React from "react";
import {{ AbsoluteFill }} from "remotion";
import {{ CartoonStage2D }} from "../components/CartoonStage2D";
import {{ SCENE_PLAN }} from "./ScenesData";

export const GENERATED_TOTAL_FRAMES = {total_frames};
export const GeneratedTimeline: React.FC = () => (<AbsoluteFill><CartoonStage2D plan={{SCENE_PLAN}} /></AbsoluteFill>);
""",
        encoding="utf-8",
    )

    self_heal_scenes(client, plan)
    print(f"[generate_scenes] Complete: {len(scenes)} rapid-cut 2.5D blueprint scenes verified!")


if __name__ == "__main__":
    main()

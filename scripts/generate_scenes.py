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
MODELS_DIR = ROOT / "public" / "models"
GENERATED_DIR = ROOT / "src" / "generated"
SCENES_DIR = GENERATED_DIR / "scenes"

STUDIO_KIT_API_DOC = """
Available components in "../../components/StudioKit" (and ONLY these imports are allowed):
import React from "react";
import {
  MatteBox, MatteCylinder, MatteSphere, MatteTorus, MatteCone,
  SpinGroup, BobGroup, RevealSlideGroup, FlowStream, RisingParticles, OrbitRing, GlbModel
} from "../../components/StudioKit";
import type { DynamicSceneProps } from "../../types";

Props Reference (type V3 = [number, number, number]):
- DynamicSceneProps: { frame: number; localFrame: number; progress: number; accentHex: string }
- MatteBox: { pos?: V3; rot?: V3; size?: V3; color?: string; emissive?: string; emissiveIntensity?: number; roughness?: number; metalness?: number; opacity?: number }
- MatteCylinder: { pos?: V3; rot?: V3; radiusTop?: number; radiusBottom?: number; height?: number; segments?: number; openEnded?: boolean; thetaStart?: number; thetaLength?: number; doubleSide?: boolean; color?: string; emissive?: string; emissiveIntensity?: number }
- MatteSphere: { pos?: V3; scale?: V3; radius?: number; color?: string; emissive?: string; emissiveIntensity?: number }
- MatteTorus: { pos?: V3; rot?: V3; radius?: number; tube?: number; arc?: number; color?: string; emissive?: string; emissiveIntensity?: number }
- MatteCone: { pos?: V3; rot?: V3; radius?: number; height?: number; segments?: number; color?: string; emissive?: string; emissiveIntensity?: number }
- SpinGroup: { pos?: V3; rot?: V3; axis?: "x"|"y"|"z"; speed?: number; frame: number; children?: React.ReactNode }
- BobGroup: { pos?: V3; rot?: V3; axis?: "x"|"y"|"z"; amp?: number; speed?: number; phase?: number; frame: number; children?: React.ReactNode }
- RevealSlideGroup: { startPos?: V3; endPos?: V3; startScale?: number; endScale?: number; progress: number; startAt?: number; endAt?: number; children?: React.ReactNode }
- FlowStream: { points: V3[]; tubeRadius?: number; tubeColor?: string; particleColor?: string; particleSize?: number; count?: number; speed?: number; frame: number }
- RisingParticles: { origin?: V3; spread?: number; height?: number; count?: number; size?: number; color?: string; speed?: number; frame: number }
- OrbitRing: { center?: V3; radius?: number; count?: number; size?: number; color?: string; speed?: number; tilt?: V3; frame: number }
- GlbModel: { file: string; pos?: V3; rot?: V3; scale?: number; spinSpeed?: number; frame: number }

STRICT CODE RULES:
1. Export EXACTLY `export const Scene_XX: React.FC<DynamicSceneProps> = ({ frame, localFrame, progress, accentHex }) => { ... }`.
2. NEVER import `three`, `@react-three/fiber`, `remotion`, `useFrame`, `useState`, `useEffect`, or `<Text>` / `<Html>`. Use ONLY `React`, `StudioKit`, `DynamicSceneProps`, and standard `<group>`.
3. EVERY scene MUST have continuous internal motion + cutaway animation (`RevealSlideGroup`, `SpinGroup`, `FlowStream`, `RisingParticles`, `BobGroup`).
4. ZERO text, zero labels, zero HTML overlays.
"""

PALETTES = [
    {"bgHex": "#08101E", "accentHex": "#22D3EE"},
    {"bgHex": "#0A1424", "accentHex": "#38BDF8"},
    {"bgHex": "#160D12", "accentHex": "#F97316"},
    {"bgHex": "#07181E", "accentHex": "#06B6D4"},
    {"bgHex": "#081426", "accentHex": "#60A5FA"},
    {"bgHex": "#141009", "accentHex": "#F59E0B"},
    {"bgHex": "#071915", "accentHex": "#10B981"},
    {"bgHex": "#100D22", "accentHex": "#818CF8"},
]

DEFAULT_WAYPOINTS_16_9 = [
    [
        {"offset": [5.6, 3.0, 6.0], "lookOffset": [0.0, 0.2, 0.0]},
        {"offset": [1.8, 1.5, 4.1], "lookOffset": [0.1, 0.1, 0.0]},
        {"offset": [-3.2, 2.0, 4.5], "lookOffset": [-0.1, 0.0, 0.0]},
    ],
    [
        {"offset": [-5.2, 2.7, 5.6], "lookOffset": [0.0, 0.1, 0.0]},
        {"offset": [-1.2, 1.3, 3.6], "lookOffset": [0.0, 0.2, 0.0]},
        {"offset": [3.5, 1.9, 4.4], "lookOffset": [0.1, 0.0, 0.0]},
    ],
]

DEFAULT_WAYPOINTS_9_16 = [
    [
        {"offset": [4.4, 3.2, 6.4], "lookOffset": [0.0, 0.3, 0.0]},
        {"offset": [1.2, 1.6, 4.6], "lookOffset": [0.0, 0.2, 0.0]},
        {"offset": [-2.8, 2.2, 5.2], "lookOffset": [0.0, 0.1, 0.0]},
    ],
    [
        {"offset": [-4.2, 2.8, 6.2], "lookOffset": [0.0, 0.2, 0.0]},
        {"offset": [-0.8, 1.4, 4.4], "lookOffset": [0.0, 0.3, 0.0]},
        {"offset": [2.9, 2.1, 5.1], "lookOffset": [0.0, 0.1, 0.0]},
    ],
]

FORBIDDEN_CODE_PATTERNS = (
    "<Text",
    "<Html",
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


def discover_custom_models() -> List[str]:
    if not MODELS_DIR.exists():
        return []
    return sorted(p.name for p in MODELS_DIR.iterdir() if p.is_file() and p.suffix.lower() in {".glb", ".gltf"})


def compute_scene_range(duration_sec: float, is_short: bool) -> tuple[int, int]:
    if is_short:
        if duration_sec <= 20:
            return 3, 4
        if duration_sec <= 38:
            return 4, 6
        if duration_sec <= 65:
            return 6, 9
        return 8, 12
    if duration_sec <= 25:
        return 2, 3
    if duration_sec <= 60:
        return 4, 6
    if duration_sec <= 180:
        return 8, 14
    if duration_sec <= 360:
        return 16, 26
    return 28, 42


def snap_to_peak(target: float, peaks: List[float], min_val: float, max_val: float) -> float:
    best = target
    best_dist = 0.65
    for p in peaks:
        d = abs(p - target)
        if d <= best_dist and min_val < p < max_val:
            best = p
            best_dist = d
    return round(best, 3)


def sanitize_hex(val: Any, fallback: str) -> str:
    if isinstance(val, str) and re.fullmatch(r"#[0-9A-Fa-f]{6}", val.strip()):
        return val.strip()
    return fallback


def build_safe_fallback_scene_tsx(scene_num: int, accent_hex: str, title: str) -> str:
    variant = scene_num % 4
    safe_comment = re.sub(r"[^A-Za-z0-9 ,.-]", "", title)[:60]
    if variant == 0:
        body = f"""
      <MatteBox pos={{[0, -0.8, 0]}} size={{[4.2, 0.2, 3.4]}} color="#141E2E" />
      <RevealSlideGroup startPos={{[0, 0, 0]}} endPos={{[0, 1.45, 0]}} progress={{progress}} startAt={{0.2}} endAt={{0.65}}>
        <MatteBox pos={{[0, 0.3, 0]}} size={{[2.8, 0.35, 2.0]}} color="#334155" />
      </RevealSlideGroup>
      <SpinGroup pos={{[0, -0.1, 0]}} axis="y" speed={{0.9}} frame={{frame}}>
        <MatteCylinder pos={{[0, 0, 0]}} radiusTop={{0.7}} radiusBottom={{0.9}} height={{1.2}} color="#1E293B" />
        <MatteCylinder pos={{[0, 0.1, 0]}} radiusTop={{0.42}} radiusBottom={{0.42}} height={{1.3}} color={{"{accent_hex}"}} emissive={{"{accent_hex}"}} emissiveIntensity={{1.6}} />
      </SpinGroup>
      <FlowStream points={{[[-2.0, 0.2, -0.8], [-0.7, 0.4, -0.2], [0.7, 0.4, 0.2], [2.0, 0.2, 0.8]]}} tubeColor="#1E293B" particleColor={{"{accent_hex}"}} count={{6}} speed={{0.7}} frame={{frame}} />"""
    elif variant == 1:
        body = f"""
      <MatteBox pos={{[0, -0.9, 0]}} size={{[4.0, 0.18, 3.2]}} color="#0F172A" />
      <BobGroup pos={{[0, 0.2, 0]}} axis="y" amp={{0.15}} speed={{1.5}} frame={{frame}}>
        <MatteTorus pos={{[0, 0, 0]}} radius={{1.15}} tube={{0.15}} color="#334155" />
        <MatteTorus pos={{[0, 0, 0]}} rot={{[1.57, 0, 0]}} radius={{0.88}} tube={{0.09}} color={{"{accent_hex}"}} emissive={{"{accent_hex}"}} emissiveIntensity={{1.7}} />
      </BobGroup>
      <OrbitRing center={{[0, 0.2, 0]}} radius={{1.65}} count={{8}} size={{0.1}} color={{"{accent_hex}"}} speed={{0.9}} frame={{frame}} />
      <RisingParticles origin={{[0, -0.7, 0]}} spread={{1.0}} height={{2.5}} count={{12}} color={{"{accent_hex}"}} frame={{frame}} />"""
    elif variant == 2:
        body = f"""
      <MatteBox pos={{[0, -0.85, 0]}} size={{[3.8, 0.2, 3.8]}} color="#182234" />
      <RevealSlideGroup startPos={{[0, 0, 0]}} endPos={{[1.0, 0.9, 0]}} progress={{progress}} startAt={{0.15}} endAt={{0.6}}>
        <MatteCylinder pos={{[0, 0.2, 0]}} radiusTop={{1.0}} radiusBottom={{1.0}} height={{1.9}} thetaLength={{4.2}} doubleSide={{true}} color="#475569" />
      </RevealSlideGroup>
      <SpinGroup pos={{[0, 0.2, 0]}} axis="y" speed={{1.8}} frame={{frame}}>
        <MatteBox pos={{[0, 0, 0]}} size={{[1.45, 0.22, 0.28]}} color="#CBD5E1" />
        <MatteBox pos={{[0, 0, 0]}} size={{[0.28, 0.22, 1.45]}} color="#CBD5E1" />
        <MatteSphere pos={{[0, 0.45, 0]}} radius={{0.36}} color={{"{accent_hex}"}} emissive={{"{accent_hex}"}} emissiveIntensity={{1.9}} />
      </SpinGroup>"""
    else:
        body = f"""
      <MatteBox pos={{[0, -0.85, 0]}} size={{[4.4, 0.2, 3.0]}} color="#141C2B" />
      <FlowStream points={{[[-2.0, 0.9, 0], [-0.9, 0.1, 0.3], [0.9, 0.1, -0.3], [2.0, 0.9, 0]]}} tubeColor="#334155" particleColor={{"{accent_hex}"}} count={{7}} speed={{0.85}} frame={{frame}} />
      <BobGroup pos={{[-1.3, 0.0, 0]}} axis="y" amp={{0.18}} speed={{1.6}} frame={{frame}}>
        <MatteBox size={{[0.8, 1.35, 0.8]}} color="#243146" />
      </BobGroup>
      <BobGroup pos={{[1.3, 0.0, 0]}} axis="y" amp={{0.18}} speed={{1.6}} phase={{1.5}} frame={{frame}}>
        <MatteBox size={{[0.8, 1.35, 0.8]}} color="#243146" />
      </BobGroup>
      <MatteCylinder pos={{[0, 0.1, 0]}} radiusTop={{0.42}} radiusBottom={{0.52}} height={{1.6}} color={{"{accent_hex}"}} emissive={{"{accent_hex}"}} emissiveIntensity={{1.4}} />"""

    return f"""import React from "react";
import {{
  MatteBox, MatteCylinder, MatteSphere, MatteTorus,
  SpinGroup, BobGroup, RevealSlideGroup, FlowStream, RisingParticles, OrbitRing
}} from "../../components/StudioKit";
import type {{ DynamicSceneProps }} from "../../types";

// Fallback scene: {safe_comment}
export const Scene_{scene_num:02d}: React.FC<DynamicSceneProps> = ({{ frame, progress }}) => {{
  return (
    <group>{body}
    </group>
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
    fps: int,
    width: int,
    height: int,
    is_short: bool,
) -> Dict[str, Any]:
    raw_scenes = raw_board.get("scenes") or []
    if not raw_scenes:
        raise ValueError("Storyboard returned empty scenes list.")

    count = len(raw_scenes)
    avg_len = duration_sec / count
    cursor = 0.0
    scenes: List[Dict[str, Any]] = []
    wp_bank = DEFAULT_WAYPOINTS_9_16 if is_short else DEFAULT_WAYPOINTS_16_9

    for idx, sc in enumerate(raw_scenes):
        is_last = idx == count - 1
        start_sec = round(cursor, 3)
        if is_last:
            end_sec = round(duration_sec, 3)
        else:
            raw_end = float(sc.get("endSec", (idx + 1) * avg_len))
            min_gap = 3.2 if is_short else 4.5
            min_end = start_sec + max(min_gap, avg_len * 0.5)
            max_end = duration_sec - (count - idx - 1) * min_gap
            clamped = min(max(raw_end, min_end), max(min_end, max_end))
            end_sec = snap_to_peak(clamped, peaks, start_sec + min_gap - 0.5, duration_sec - min_gap)
        cursor = end_sec

        pal = PALETTES[idx % len(PALETTES)]
        bg_hex = sanitize_hex(sc.get("bgHex"), pal["bgHex"])
        accent_hex = sanitize_hex(sc.get("accentHex"), pal["accentHex"])

        wps = sc.get("cameraWaypoints")
        default_wps = wp_bank[idx % len(wp_bank)]
        clean_wps = []
        if isinstance(wps, list) and len(wps) >= 2:
            for wi, wp in enumerate(wps[:4]):
                dwp = default_wps[wi % len(default_wps)]
                off = wp.get("offset") if isinstance(wp, dict) else None
                look = wp.get("lookOffset") if isinstance(wp, dict) else None
                if not (isinstance(off, list) and len(off) == 3):
                    off = dwp["offset"]
                if not (isinstance(look, list) and len(look) == 3):
                    look = dwp["lookOffset"]
                clean_wps.append(
                    {
                        "offset": [round(min(8.5, max(-8.5, float(x))), 3) for x in off],
                        "lookOffset": [round(min(1.5, max(-1.5, float(x))), 3) for x in look],
                    }
                )
        else:
            clean_wps = default_wps

        world_pos = [
            round(idx * 28.0, 2),
            round(2.6 if idx % 2 == 1 else 0.0, 2),
            round(-idx * 20.0 + (3.0 if idx % 3 == 1 else 0.0), 2),
        ]

        scenes.append(
            {
                "id": f"scene_{idx + 1:02d}",
                "componentName": f"Scene_{idx + 1:02d}",
                "visualConcept": str(sc.get("visualConcept") or f"Unique Engineering Concept {idx + 1}")[:120],
                "visualSpec": str(sc.get("visualSpec") or "Animated multi-part stylized 3D cutaway mechanism.")[:500],
                "startSec": start_sec,
                "endSec": end_sec,
                "worldPos": world_pos,
                "bgHex": bg_hex,
                "accentHex": accent_hex,
                "cameraWaypoints": clean_wps,
            }
        )

    return {
        "channel": "InfraVerse",
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
        'import type { DynamicSceneProps } from "../types";\n'
        + "\n".join(imports)
        + "\n\nexport const SCENE_REGISTRY: Record<string, React.FC<DynamicSceneProps>> = {\n"
        + "\n".join(entries)
        + "\n};\n"
    )
    (GENERATED_DIR / "SceneRegistry.ts").write_text(registry_ts, encoding="utf-8")

    scenes_data_ts = (
        'import type { DocumentaryPlan } from "../types";\n\n'
        f"export const SCENE_PLAN: DocumentaryPlan = {json.dumps(plan, indent=2, ensure_ascii=False)};\n"
    )
    (GENERATED_DIR / "ScenesData.ts").write_text(scenes_data_ts, encoding="utf-8")

    timeline_tsx = f"""import React from "react";
import {{ AbsoluteFill }} from "remotion";
import {{ Continuous3DWorld }} from "../components/Continuous3DWorld";
import {{ SCENE_PLAN }} from "./ScenesData";

export const GENERATED_TOTAL_FRAMES = {total_frames};

export const GeneratedTimeline: React.FC = () => {{
  return (
    <AbsoluteFill>
      <Continuous3DWorld plan={{SCENE_PLAN}} />
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

{STUDIO_KIT_API_DOC}

ERRORS:
{chr(10).join(err_lines)}

CODE:
{broken_code}

Return ONLY the fixed complete TSX file.
"""
            try:
                fixed_raw = generate_with_fallback(client, fix_prompt, role="flash", json_mode=False, temperature=0.2)
                scene_num = int(cname.split("_")[1])
                sc_path.write_text(sanitize_scene_tsx(fixed_raw, scene_num), encoding="utf-8")
            except Exception as exc:
                print(f"[self_heal] Repair skipped for {cname} ({exc}).")
            time.sleep(3)

    final_res = run_tsc_check()
    if final_res.returncode != 0:
        final_out = (final_res.stdout or "") + "\n" + (final_res.stderr or "")
        still_broken = sorted(set(re.findall(r"src/generated/scenes/(Scene_\d+)\.tsx", final_out)))
        for cname in still_broken:
            num = int(cname.split("_")[1])
            sc_meta = scene_map.get(cname, {})
            print(f"[self_heal] Swapping stubborn {cname} to unique procedural fallback.")
            (SCENES_DIR / f"{cname}.tsx").write_text(
                build_safe_fallback_scene_tsx(num, sc_meta.get("accentHex", "#22D3EE"), sc_meta.get("visualConcept", cname)),
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
    custom_models = discover_custom_models()
    min_sc, max_sc = compute_scene_range(duration_sec, is_short=is_short)

    framing_note = (
        "VERTICAL 9:16 YOUTUBE SHORT MODE (1080x1920): Keep X spread tight [-2.2 .. +2.2] and build TALL vertical stacked machinery/towers [-2.2 .. +2.8 in Y] so every visual element fills a vertical phone screen! Use punchy pacing synced tightly to the user's hook and voiceover."
        if is_short
        else "WIDESCREEN 16:9 MODE (1920x1080): Keep geometry spread within [-3.8 .. +3.8] X/Z and [-2.0 .. +2.8] Y."
    )

    storyboard_prompt = f"""
You are the Lead 3D Film Director for a stylized matte-3D engineering channel (like Professor Of How / Zack D. Films mechanical cutaways, ZERO text on screen).

ASPECT & FRAMING:
{framing_note}

USER'S LOOK, STYLE & ELEMENTS DESCRIPTION (Follow EVERY visual style, color look, mood, and element requested by the user!):
{visuals_prompt if visuals_prompt else "(No visuals.txt uploaded — invent vivid, completely unique engineering & infrastructure 3D scenes matching the voiceover!)"}

CUSTOM .GLB MODELS IN public/models/:
{json.dumps(custom_models)}

VOICEOVER TRANSCRIPT ({duration_sec:.2f}s):
{json.dumps(transcript.get("segments", []), ensure_ascii=False)}

VOCAL EMPHASIS PEAKS (seconds):
{json.dumps(peaks[:120])}

HARD RULES:
1. Build the FULL {duration_sec:.2f}s video into {min_sc} to {max_sc} continuous chapters ("scenes") matching the narration and the user's requested hook/elements/look.
2. ZERO REPETITION: Every chapter MUST have a completely DIFFERENT `visualConcept`, layout, and hero objects!
3. CONTINUOUS CUTAWAY MOTION: Describe moving parts & `RevealSlideGroup` cutaways in `visualSpec`.
4. CAMERA FLIGHT: 3 smooth `cameraWaypoints` per scene (`offset`: [x,y,z], `lookOffset`: [lx,ly,lz]).
5. HONOR USER LOOK & COLORS: Choose `bgHex` and `accentHex` matching the exact look/mood requested in the user's description (or cohesive dark studio hues if unspecified).

Return ONLY valid JSON:
{{
  "scenes": [
    {{
      "visualConcept": "Short unique concept summary",
      "visualSpec": "Detailed 3D composition & cutaway motions matching user elements",
      "endSec": 6.5,
      "bgHex": "#08101E",
      "accentHex": "#22D3EE",
      "cameraWaypoints": [
        {{"offset": [4.6, 3.0, 6.2], "lookOffset": [0.0, 0.2, 0.0]}},
        {{"offset": [1.4, 1.5, 4.4], "lookOffset": [0.0, 0.2, 0.0]}},
        {{"offset": [-2.8, 2.1, 4.9], "lookOffset": [0.0, 0.0, 0.0]}}
      ]
    }}
  ]
}}
"""

    client = get_client()
    print(f"[generate_scenes] Planning storyboard from {input_dir.name}/ ({width}x{height} @ {fps}fps)...")
    raw_board = generate_with_fallback(client, storyboard_prompt, role="pro", json_mode=True, temperature=0.45)
    plan = normalize_storyboard(
        parse_json_strict(raw_board),
        duration_sec=duration_sec,
        bpm=bpm,
        peaks=peaks,
        fps=fps,
        width=width,
        height=height,
        is_short=is_short,
    )
    (WORK_DIR / "scene_plan.json").write_text(json.dumps(plan, indent=2, ensure_ascii=False), encoding="utf-8")

    SCENES_DIR.mkdir(parents=True, exist_ok=True)
    for old_file in SCENES_DIR.glob("Scene_*.tsx"):
        old_file.unlink()

    scenes = plan["scenes"]
    batch_size = 4
    print(f"[generate_scenes] Coding {len(scenes)} unique 3D scenes in batches of {batch_size}...")

    for b_start in range(0, len(scenes), batch_size):
        batch = scenes[b_start : b_start + batch_size]
        batch_specs = [
            {
                "componentName": sc["componentName"],
                "visualConcept": sc["visualConcept"],
                "visualSpec": sc["visualSpec"],
                "accentHex": sc["accentHex"],
                "customModelsAvailable": custom_models,
            }
            for sc in batch
        ]
        code_prompt = f"""
You are an Expert Three.js / React Three Fiber 3D Technical Animator.
{framing_note}
USER LOOK GUIDANCE: {visuals_prompt[:1000] if visuals_prompt else "Sleek stylized matte-3D engineering studio."}
{STUDIO_KIT_API_DOC}

BATCH TO CODE (Make every scene visually distinct, richly detailed with 8–18 components each, with cutaway RevealSlideGroup + continuous SpinGroup/BobGroup/FlowStream/RisingParticles motion!):
{json.dumps(batch_specs, indent=2)}

Return ONLY valid JSON where each key is the exact `componentName` (e.g. "Scene_01") and each value is the complete valid TSX file string starting with `import React from "react";`.
"""
        try:
            raw_code_json = generate_with_fallback(
                client,
                code_prompt,
                role="flash",
                json_mode=True,
                max_output_tokens=32768,
                temperature=0.35,
            )
            generated_map = extract_scenes_dict(raw_code_json)
        except Exception as exc:
            print(f"[generate_scenes] Batch {b_start+1} API failed ({exc}); using safe fallbacks.")
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
                print(f"  + Generated custom {cname}.tsx ({sc['visualConcept'][:48]})")
            except Exception as exc:
                print(f"  ! {cname} sanitize issue ({exc}); writing unique fallback.")
                out_path.write_text(
                    build_safe_fallback_scene_tsx(num, sc["accentHex"], sc["visualConcept"]),
                    encoding="utf-8",
                )

        if b_start + batch_size < len(scenes):
            time.sleep(6)

    write_registry_and_timeline(plan)
    self_heal_scenes(client, plan)
    print(f"[generate_scenes] Complete: {len(scenes)} unique dynamic scenes verified!")


if __name__ == "__main__":
    main()

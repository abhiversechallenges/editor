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
  HardwareRack, FinnedHousing, PipeConduit, HeatSinkArray, GlassShell,
  SpinGroup, BobGroup, RevealSlideGroup, FlowStream, RisingParticles, OrbitRing, GlbModel
} from "../../components/StudioKit";
import type { DynamicSceneProps } from "../../types";

Props Reference (type V3 = [number, number, number]):
- DynamicSceneProps: { frame: number; localFrame: number; progress: number; accentHex: string }
- MatteBox: { pos?: V3; rot?: V3; size?: V3; color?: string; emissive?: string; emissiveIntensity?: number; roughness?: number; metalness?: number; opacity?: number; edges?: boolean; edgeColor?: string }
- MatteCylinder: { pos?: V3; rot?: V3; radiusTop?: number; radiusBottom?: number; height?: number; segments?: number; openEnded?: boolean; thetaStart?: number; thetaLength?: number; doubleSide?: boolean; color?: string; emissive?: string; emissiveIntensity?: number; edges?: boolean; edgeColor?: string }
- MatteSphere: { pos?: V3; scale?: V3; radius?: number; color?: string; emissive?: string; emissiveIntensity?: number }
- MatteTorus: { pos?: V3; rot?: V3; radius?: number; tube?: number; arc?: number; color?: string; emissive?: string; emissiveIntensity?: number }
- MatteCone: { pos?: V3; rot?: V3; radius?: number; height?: number; segments?: number; color?: string; emissive?: string; emissiveIntensity?: number; edges?: boolean; edgeColor?: string }
- HardwareRack: { pos?: V3; rot?: V3; size?: V3; bays?: number; accentHex?: string; frame: number }
  (Compound 10+ sub-part server/compute rack with CAD frame, vertical rails, recessed inner bay, individual blade trays, glowing status strips & top fan)
- FinnedHousing: { pos?: V3; rot?: V3; radius?: number; height?: number; finCount?: number; color?: string; accentHex?: string; cutaway?: boolean; frame: number }
  (Compound multi-part industrial vessel/reactor/turbine cylinder with bolted top/bottom flanges, radial cooling fins, translucent outer shell & glowing core)
- PipeConduit: { points: V3[]; tubeRadius?: number; pipeColor?: string; fluidColor?: string; flangeCount?: number; count?: number; speed?: number; frame: number }
  (Translucent cutaway conduit with bolted flange collars & bright fluid/energy capsules flowing INSIDE the pipe!)
- HeatSinkArray: { pos?: V3; rot?: V3; size?: V3; finCount?: number; color?: string; pipeColor?: string; glowColor?: string }
  (Machined baseplate + parallel CAD-edged cooling fins + twin copper heatpipes)
- GlassShell: { pos?: V3; rot?: V3; shape?: "box"|"cylinder"; size?: V3; radius?: number; height?: number; color?: string; edgeColor?: string; opacity?: number }
- SpinGroup: { pos?: V3; rot?: V3; axis?: "x"|"y"|"z"; speed?: number; frame: number; children?: React.ReactNode }
- BobGroup: { pos?: V3; rot?: V3; axis?: "x"|"y"|"z"; amp?: number; speed?: number; phase?: number; frame: number; children?: React.ReactNode }
- RevealSlideGroup: { startPos?: V3; endPos?: V3; startScale?: number; endScale?: number; progress: number; startAt?: number; endAt?: number; children?: React.ReactNode }
- FlowStream: { points: V3[]; tubeRadius?: number; tubeColor?: string; particleColor?: string; particleSize?: number; count?: number; speed?: number; frame: number }
- RisingParticles: { origin?: V3; spread?: number; height?: number; count?: number; size?: number; color?: string; speed?: number; frame: number }
- OrbitRing: { center?: V3; radius?: number; count?: number; size?: number; color?: string; speed?: number; tilt?: V3; frame: number }
- GlbModel: { file: string; pos?: V3; rot?: V3; scale?: number; spinSpeed?: number; frame: number }

STRICT HARDWARE DETAIL & CONTRAST RULES:
1. Export EXACTLY `export const Scene_XX: React.FC<DynamicSceneProps> = ({ frame, localFrame, progress, accentHex }) => { ... }`.
2. NEVER import `three`, `@react-three/fiber`, `remotion`, `useFrame`, `useState`, `useEffect`, or `<Text>` / `<Html>`.
3. READABLE CONTRAST: Use slate architectural colors (#2D3E58, #3B4E6B, #475569, #64748B, #CBD5E1, #D97706) paired with glowing `accentHex`, `#22D3EE`, `#F97316`, `#10B981`. Never use black-on-black materials.
4. NO RAW SINGLE-CYLINDER OR RANDOM-DOT PLACEHOLDERS: Every hero object MUST combine 6-14 mechanical sub-parts (use HardwareRack, FinnedHousing, PipeConduit, HeatSinkArray, GlassShell, bolted flanges, ribs, fins, and multi-stage RevealSlideGroup cutaways!).
5. Move energy/coolant packets cleanly inside visible `PipeConduit` or `FlowStream` tubes, NOT random scattered floating dots.
"""

PALETTES = [
    {"bgHex": "#0E1729", "accentHex": "#22D3EE"},
    {"bgHex": "#122038", "accentHex": "#38BDF8"},
    {"bgHex": "#1D1319", "accentHex": "#F97316"},
    {"bgHex": "#0F212B", "accentHex": "#06B6D4"},
    {"bgHex": "#11223A", "accentHex": "#60A5FA"},
    {"bgHex": "#1B1610", "accentHex": "#F59E0B"},
    {"bgHex": "#0E2420", "accentHex": "#10B981"},
    {"bgHex": "#16142E", "accentHex": "#818CF8"},
]

BEAT_CAM_PRESETS_16_9 = [
    [
        {"offset": [5.8, 3.1, 6.2], "lookOffset": [0.0, 0.2, 0.0]},
        {"offset": [2.2, 1.6, 3.8], "lookOffset": [0.2, 0.15, 0.0]},
        {"offset": [-3.4, 2.3, 4.2], "lookOffset": [-0.15, 0.05, 0.0]},
    ],
    [
        {"offset": [-5.2, 2.8, 5.6], "lookOffset": [0.0, 0.15, 0.0]},
        {"offset": [-1.3, 1.2, 3.4], "lookOffset": [0.0, 0.25, 0.0]},
        {"offset": [3.8, 1.9, 4.1], "lookOffset": [0.1, 0.05, 0.0]},
    ],
    [
        {"offset": [0.8, 4.4, 6.0], "lookOffset": [0.0, 0.0, 0.0]},
        {"offset": [3.5, 1.5, 3.6], "lookOffset": [0.0, 0.2, 0.0]},
        {"offset": [-2.2, 1.1, 3.5], "lookOffset": [0.0, 0.15, 0.0]},
    ],
]

BEAT_CAM_PRESETS_9_16 = [
    [
        {"offset": [4.5, 3.2, 6.3], "lookOffset": [0.0, 0.3, 0.0]},
        {"offset": [1.3, 1.7, 4.3], "lookOffset": [0.0, 0.25, 0.0]},
        {"offset": [-2.9, 2.2, 4.9], "lookOffset": [0.0, 0.1, 0.0]},
    ],
    [
        {"offset": [-4.2, 2.9, 6.1], "lookOffset": [0.0, 0.25, 0.0]},
        {"offset": [-0.9, 1.4, 4.2], "lookOffset": [0.0, 0.3, 0.0]},
        {"offset": [3.0, 2.0, 4.8], "lookOffset": [0.0, 0.1, 0.0]},
    ],
]

HIGHLIGHT_KEYWORDS = {
    "ai", "gpu", "gpus", "nvidia", "blackwell", "nvlink", "infiniband", "chip", "chips",
    "silicon", "die", "liquid", "cooling", "coolant", "copper", "water", "watts", "megawatts",
    "gigawatts", "mw", "kw", "gw", "kv", "nuclear", "reactor", "reactors", "smr", "uranium",
    "substation", "substations", "transformer", "transformers", "grid", "blackout", "battery",
    "batteries", "megapack", "fiber", "subsea", "cable", "cables", "heat", "thermal",
    "overheat", "overheats", "billion", "hundred", "thousand", "trillions", "data", "center",
    "supercluster", "power", "electricity", "cooling", "towers", "manifolds", "turbine",
}

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
        if duration_sec <= 22:
            return 3, 5
        if duration_sec <= 40:
            return 5, 7
        return 7, 10
    if duration_sec <= 25:
        return 3, 4
    if duration_sec <= 65:
        return 6, 9
    if duration_sec <= 150:
        return 13, 17
    if duration_sec <= 360:
        return 22, 32
    return 36, 48


def snap_to_peak(target: float, peaks: List[float], min_val: float, max_val: float) -> float:
    best = target
    best_dist = 0.55
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


def build_subtitle_chunks(words: List[Dict[str, Any]], total_dur: float) -> List[Dict[str, Any]]:
    chunks: List[Dict[str, Any]] = []
    if not words:
        return chunks

    buf: List[Dict[str, Any]] = []
    for w in words:
        text = str(w.get("word", "")).strip()
        if not text:
            continue
        buf.append({"word": text, "start": float(w["start"]), "end": float(w["end"])})
        ends_sentence = text.endswith((".", "!", "?", ","))
        if len(buf) >= 4 or (len(buf) >= 2 and ends_sentence):
            c_start = buf[0]["start"]
            c_end = min(total_dur, buf[-1]["end"] + 0.12)
            chunk_words = []
            for item in buf:
                clean_tok = re.sub(r"[^a-z0-9$%]", "", item["word"].lower())
                is_hi = bool(re.search(r"\d", clean_tok)) or clean_tok in HIGHLIGHT_KEYWORDS
                chunk_words.append({"text": item["word"], "highlight": is_hi})
            chunks.append({"startSec": round(c_start, 3), "endSec": round(c_end, 3), "words": chunk_words})
            buf = []

    if buf:
        chunk_words = []
        for item in buf:
            clean_tok = re.sub(r"[^a-z0-9$%]", "", item["word"].lower())
            is_hi = bool(re.search(r"\d", clean_tok)) or clean_tok in HIGHLIGHT_KEYWORDS
            chunk_words.append({"text": item["word"], "highlight": is_hi})
        chunks.append(
            {
                "startSec": round(buf[0]["start"], 3),
                "endSec": round(min(total_dur, buf[-1]["end"] + 0.2), 3),
                "words": chunk_words,
            }
        )
    return chunks


def build_safe_fallback_scene_tsx(scene_num: int, accent_hex: str, title: str) -> str:
    variant = scene_num % 4
    safe_comment = re.sub(r"[^A-Za-z0-9 ,.-]", "", title)[:60]
    if variant == 0:
        body = f"""
      <MatteBox pos={{[0, -0.95, 0]}} size={{[5.2, 0.22, 3.8]}} color="#2B3B52" />
      <HardwareRack pos={{[-1.3, 0.15, 0]}} size={{[1.1, 2.0, 1.1]}} bays={{6}} accentHex={{"{accent_hex}"}} frame={{frame}} />
      <HardwareRack pos={{[1.3, 0.15, 0]}} size={{[1.1, 2.0, 1.1]}} bays={{6}} accentHex={{"{accent_hex}"}} frame={{frame}} />
      <RevealSlideGroup startPos={{[0, 0, 0]}} endPos={{[0, 1.25, 0]}} progress={{progress}} startAt={{0.2}} endAt={{0.65}}>
        <HeatSinkArray pos={{[0, 0.3, 0]}} size={{[1.6, 0.65, 1.4]}} finCount={{7}} color="#64748B" glowColor={{"{accent_hex}"}} />
      </RevealSlideGroup>
      <PipeConduit points={{[[-1.3, 0.4, 0.6], [-0.4, 0.1, 0.9], [0.4, 0.1, 0.9], [1.3, 0.4, 0.6]]}} fluidColor={{"{accent_hex}"}} flangeCount={{3}} speed={{0.8}} frame={{frame}} />"""
    elif variant == 1:
        body = f"""
      <MatteBox pos={{[0, -0.95, 0]}} size={{[4.8, 0.22, 3.8]}} color="#2D3E58" />
      <FinnedHousing pos={{[0, 0.15, 0]}} radius={{1.05}} height={{2.0}} finCount={{8}} color="#3B4E6B" accentHex={{"{accent_hex}"}} cutaway={{true}} frame={{frame}} />
      <RevealSlideGroup startPos={{[0, 0, 0]}} endPos={{[0, 1.1, 0]}} progress={{progress}} startAt={{0.15}} endAt={{0.6}}>
        <SpinGroup pos={{[0, 0.15, 0]}} axis="y" speed={{2.4}} frame={{frame}}>
          <MatteCylinder pos={{[0, 0, 0]}} radiusTop={{0.42}} radiusBottom={{0.42}} height={{1.6}} color={{"{accent_hex}"}} emissive={{"{accent_hex}"}} emissiveIntensity={{1.7}} />
        </SpinGroup>
      </RevealSlideGroup>
      <PipeConduit points={{[[-2.4, -0.3, 0], [-1.05, 0.1, 0], [1.05, 0.1, 0], [2.4, 0.7, 0]]}} fluidColor={{"{accent_hex}"}} flangeCount={{4}} speed={{0.9}} frame={{frame}} />"""
    elif variant == 2:
        body = f"""
      <MatteBox pos={{[0, -0.95, 0]}} size={{[4.6, 0.22, 4.2]}} color="#2B3B52" />
      <GlassShell pos={{[0, 0.25, 0]}} shape="box" size={{[2.6, 1.9, 2.2]}} color="#38BDF8" edgeColor={{"{accent_hex}"}} opacity={{0.22}} />
      <RevealSlideGroup startPos={{[0, 0, 0]}} endPos={{[0, 0.9, 0]}} progress={{progress}} startAt={{0.2}} endAt={{0.65}}>
        <HeatSinkArray pos={{[0, 0.1, 0]}} size={{[1.8, 0.6, 1.5]}} finCount={{8}} color="#D97706" glowColor={{"{accent_hex}"}} />
      </RevealSlideGroup>
      <SpinGroup pos={{[0, 0.45, 0]}} axis="y" speed={{1.9}} frame={{frame}}>
        <MatteTorus pos={{[0, 0, 0]}} rot={{[1.57, 0, 0]}} radius={{1.4}} tube={{0.07}} color={{"{accent_hex}"}} emissive={{"{accent_hex}"}} />
      </SpinGroup>
      <PipeConduit points={{[[-2.2, 0.8, 0.4], [-0.9, 0.1, 0.4], [0.9, 0.1, -0.4], [2.2, 0.8, -0.4]]}} fluidColor="#F97316" flangeCount={{4}} speed={{0.85}} frame={{frame}} />"""
    else:
        body = f"""
      <MatteBox pos={{[0, -0.95, 0]}} size={{[5.4, 0.22, 3.4]}} color="#2D3E58" />
      <BobGroup pos={{[-1.6, 0.1, 0]}} axis="y" amp={{0.12}} speed={{1.5}} frame={{frame}}>
        <FinnedHousing pos={{[0, 0, 0]}} radius={{0.72}} height={{1.6}} finCount={{6}} color="#475569" accentHex={{"{accent_hex}"}} frame={{frame}} />
      </BobGroup>
      <BobGroup pos={{[1.6, 0.1, 0]}} axis="y" amp={{0.12}} speed={{1.5}} phase={{1.5}} frame={{frame}}>
        <FinnedHousing pos={{[0, 0, 0]}} radius={{0.72}} height={{1.6}} finCount={{6}} color="#475569" accentHex={{"{accent_hex}"}} frame={{frame}} />
      </BobGroup>
      <PipeConduit points={{[[-1.6, 0.8, 0], [-0.6, 1.2, 0.3], [0.6, 1.2, -0.3], [1.6, 0.8, 0]]}} fluidColor={{"{accent_hex}"}} flangeCount={{4}} speed={{0.95}} frame={{frame}} />"""

    return f"""import React from "react";
import {{
  MatteBox, MatteCylinder, MatteTorus,
  HardwareRack, FinnedHousing, PipeConduit, HeatSinkArray, GlassShell,
  SpinGroup, BobGroup, RevealSlideGroup
}} from "../../components/StudioKit";
import type {{ DynamicSceneProps }} from "../../types";

// Multi-part fallback: {safe_comment}
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


def normalize_callouts(raw_callouts: Any, is_short: bool) -> List[Dict[str, Any]]:
    if not isinstance(raw_callouts, list):
        return []
    clean: List[Dict[str, Any]] = []
    for ci, item in enumerate(raw_callouts[:2]):
        if not isinstance(item, dict):
            continue
        label = str(item.get("label") or "").strip().upper()[:28]
        if not label:
            continue
        anc = item.get("anchorPct")
        box = item.get("boxPct")
        if not (isinstance(anc, list) and len(anc) == 2):
            anc = [50, 48] if ci == 0 else [45, 58]
        if not (isinstance(box, list) and len(box) == 2):
            box = [70, 22] if not is_short else [60, 22]
        # Clamp safely away from top-left stat counter and bottom subtitles
        ax = round(min(78.0, max(22.0, float(anc[0]))), 1)
        ay = round(min(72.0, max(24.0, float(anc[1]))), 1)
        bx = round(min(82.0, max(16.0, float(box[0]))), 1)
        by = round(min(72.0, max(18.0, float(box[1]))), 1)
        if bx < 36 and by < 32:
            bx = 68.0
        clean.append({"label": label, "anchorPct": [ax, ay], "boxPct": [bx, by]})
    return clean


def normalize_stat_counter(raw_stat: Any) -> Any:
    if not isinstance(raw_stat, dict):
        return None
    label = str(raw_stat.get("label") or "").strip().upper()[:26]
    if not label:
        return None
    try:
        from_val = float(raw_stat.get("fromVal", 0))
        to_val = float(raw_stat.get("toVal", 100))
    except Exception:
        return None
    return {
        "label": label,
        "fromVal": from_val,
        "toVal": to_val,
        "prefix": str(raw_stat.get("prefix") or "")[:6],
        "suffix": str(raw_stat.get("suffix") or "")[:10],
        "decimals": max(0, min(2, int(raw_stat.get("decimals", 0) or 0))),
    }


def normalize_storyboard(
    raw_board: Dict[str, Any],
    duration_sec: float,
    bpm: float,
    peaks: List[float],
    words: List[Dict[str, Any]],
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
    cam_bank = BEAT_CAM_PRESETS_9_16 if is_short else BEAT_CAM_PRESETS_16_9

    for idx, sc in enumerate(raw_scenes):
        is_last = idx == count - 1
        start_sec = round(cursor, 3)
        if is_last:
            end_sec = round(duration_sec, 3)
        else:
            raw_end = float(sc.get("endSec", (idx + 1) * avg_len))
            min_gap = 3.5 if is_short else 5.0
            min_end = start_sec + max(min_gap, avg_len * 0.6)
            max_end = duration_sec - (count - idx - 1) * min_gap
            clamped = min(max(raw_end, min_end), max(min_end, max_end))
            end_sec = snap_to_peak(clamped, peaks, start_sec + min_gap - 0.5, duration_sec - min_gap)
        cursor = end_sec
        sc_dur = max(3.0, end_sec - start_sec)

        pal = PALETTES[idx % len(PALETTES)]
        bg_hex = sanitize_hex(sc.get("bgHex"), pal["bgHex"])
        accent_hex = sanitize_hex(sc.get("accentHex"), pal["accentHex"])

        # Force 3-4s micro-beats inside every chapter!
        raw_beats = sc.get("beats") if isinstance(sc.get("beats"), list) else []
        target_beats = max(2, min(4, int(round(sc_dur / 3.4))))
        if sc_dur < 5.5:
            target_beats = 2

        default_cams = cam_bank[idx % len(cam_bank)]
        clean_beats: List[Dict[str, Any]] = []
        b_cursor = start_sec
        b_step = sc_dur / target_beats

        for bi in range(target_beats):
            b_is_last = bi == target_beats - 1
            b_start = round(b_cursor, 3)
            if b_is_last:
                b_end = end_sec
            else:
                b_raw_end = start_sec + (bi + 1) * b_step
                b_end = snap_to_peak(b_raw_end, peaks, b_start + 2.4, end_sec - 2.3)
                if b_end <= b_start + 2.2:
                    b_end = round(min(end_sec - 2.0, b_start + b_step), 3)
            b_cursor = b_end

            rb = raw_beats[bi] if bi < len(raw_beats) and isinstance(raw_beats[bi], dict) else {}
            def_cam = default_cams[bi % len(default_cams)]
            off = rb.get("cameraOffset")
            look = rb.get("lookOffset")
            if not (isinstance(off, list) and len(off) == 3):
                off = def_cam["offset"]
            if not (isinstance(look, list) and len(look) == 3):
                look = def_cam["lookOffset"]

            callouts = normalize_callouts(rb.get("callouts"), is_short=is_short)
            if not callouts:
                concept_short = " ".join(str(sc.get("visualConcept") or "CORE HARDWARE").upper().split()[:3])
                callouts = [{"label": concept_short, "anchorPct": [52, 48], "boxPct": [72, 24]}]

            stat_counter = normalize_stat_counter(rb.get("statCounter"))
            # Attach any emphasis peak inside this beat for punchy counter trigger
            beat_peaks = [p for p in peaks if b_start <= p <= b_end]
            trigger_sec = beat_peaks[0] if beat_peaks else round(b_start + 0.18, 3)

            clean_beats.append(
                {
                    "id": f"b_{idx + 1:02d}_{bi + 1:02d}",
                    "startSec": b_start,
                    "endSec": round(b_end, 3),
                    "triggerSec": trigger_sec,
                    "cameraOffset": [round(min(8.5, max(-8.5, float(x))), 3) for x in off],
                    "lookOffset": [round(min(1.5, max(-1.5, float(x))), 3) for x in look],
                    "callouts": callouts,
                    "statCounter": stat_counter,
                }
            )

        world_pos = [
            round(idx * 28.0, 2),
            round(2.6 if idx % 2 == 1 else 0.0, 2),
            round(-idx * 20.0 + (3.0 if idx % 3 == 1 else 0.0), 2),
        ]

        scenes.append(
            {
                "id": f"scene_{idx + 1:02d}",
                "componentName": f"Scene_{idx + 1:02d}",
                "visualConcept": str(sc.get("visualConcept") or f"Hardware Assembly {idx + 1}")[:120],
                "visualSpec": str(sc.get("visualSpec") or "Multi-part CAD-edged cutaway hardware assembly.")[:500],
                "startSec": start_sec,
                "endSec": end_sec,
                "worldPos": world_pos,
                "bgHex": bg_hex,
                "accentHex": accent_hex,
                "beats": clean_beats,
            }
        )

    subtitle_chunks = build_subtitle_chunks(words, duration_sec)

    return {
        "channel": "InfraVerse",
        "fps": fps,
        "width": width,
        "height": height,
        "totalDurationSec": round(duration_sec, 3),
        "hasAudio": True,
        "bpm": bpm,
        "emphasisPeaksSec": peaks,
        "subtitleChunks": subtitle_chunks,
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
import {{ HudOverlay }} from "../components/HudOverlay";
import {{ SCENE_PLAN }} from "./ScenesData";

export const GENERATED_TOTAL_FRAMES = {total_frames};

export const GeneratedTimeline: React.FC = () => {{
  return (
    <AbsoluteFill>
      <Continuous3DWorld plan={{SCENE_PLAN}} />
      <HudOverlay plan={{SCENE_PLAN}} />
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
            print(f"[self_heal] Swapping stubborn {cname} to multi-part procedural fallback.")
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
    words = list(transcript.get("words") or [])

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
        "VERTICAL 9:16 SHORT (1080x1920): Keep X tight [-2.2 .. +2.2], build TALL vertical stacked hardware [-2.2 .. +2.8 Y]."
        if is_short
        else "WIDESCREEN 16:9 (1920x1080): Keep geometry spread within [-3.8 .. +3.8] X/Z and [-2.0 .. +2.5] Y."
    )

    storyboard_prompt = f"""
You are the Lead 3D Motion Director & Technical Illustrator (think Branch Education / Real Engineering meets crisp HUD callouts).

ASPECT:
{framing_note}

USER VISUAL DESCRIPTION:
{visuals_prompt if visuals_prompt else "(No visuals.txt uploaded — invent vivid multi-part engineering & infrastructure 3D scenes matching the voiceover!)"}

CUSTOM .GLB MODELS: {json.dumps(custom_models)}

VOICEOVER SEGMENTS ({duration_sec:.2f}s):
{json.dumps([{"start": s["start"], "end": s["end"], "text": s["text"]} for s in transcript.get("segments", [])], ensure_ascii=False)}

VOCAL EMPHASIS PEAKS (seconds):
{json.dumps(peaks[:120])}

HARD RULES:
1. Divide the {duration_sec:.2f}s narration into {min_sc} to {max_sc} unique 3D chapters (`scenes`), roughly 6–10 seconds each! NEVER make a chapter hold longer than 11 seconds.
2. ZERO REPETITION: Every chapter MUST depict a completely DIFFERENT multi-part hardware subject (`visualConcept` & `visualSpec`).
3. FORCED 3–4 SECOND BEATS: Inside EVERY chapter, define 2 or 3 distinct `beats` (each ~3–4 seconds long!). Each beat MUST change `cameraOffset` markedly (wide view -> close-up cutaway -> low tracking angle) AND include:
   - `callouts`: 1 or 2 crisp uppercase engineering labels (`"345 kV SUBSTATION"`, `"600 kW / RACK"`, `"CLOSED-LOOP CDU"`, etc.) with `anchorPct` [25..75, 28..68] pointing near the center subject and `boxPct` [18..78, 20..68] cleanly placed off to the side.
   - `statCounter`: optional animated number card when the narration hits a spec, dollar figure, wattage, or scale (e.g., `{{"label": "CAMPUS CAPEX", "fromVal": 0, "toVal": 100, "prefix": "$", "suffix": "B"}}` or `{{"label": "CHIP POWER", "fromVal": 300, "toVal": 1000, "suffix": " W"}}`).
4. READABLE SLATE STUDIO COLORS: Use deep rich slate/blueprint `bgHex` (#0E1729, #122038, #1D1319, #0F212B, #0E2420) and bright `accentHex`.

Return ONLY valid JSON:
{{
  "scenes": [
    {{
      "visualConcept": "Short unique hardware concept",
      "visualSpec": "Multi-part assembly: concrete/slate pad, HardwareRack rows, PipeConduit loops, FinnedHousing, cutaway RevealSlideGroup",
      "endSec": 8.0,
      "bgHex": "#0E1729",
      "accentHex": "#22D3EE",
      "beats": [
        {{
          "cameraOffset": [5.6, 3.0, 6.0],
          "lookOffset": [0.0, 0.2, 0.0],
          "callouts": [{{"label": "1,000 MW CAMPUS", "anchorPct": [52, 48], "boxPct": [74, 24]}}],
          "statCounter": {{"label": "TOTAL CAPEX", "fromVal": 0, "toVal": 100, "prefix": "$", "suffix": "B"}}
        }},
        {{
          "cameraOffset": [1.8, 1.5, 3.6],
          "lookOffset": [0.2, 0.1, 0.0],
          "callouts": [{{"label": "ROOF CUTAWAY", "anchorPct": [48, 44], "boxPct": [22, 32]}}]
        }}
      ]
    }}
  ]
}}
"""

    client = get_client()
    print(f"[generate_scenes] Planning storyboard from {input_dir.name}/ ({width}x{height} @ {fps}fps)...")
    raw_board = generate_with_fallback(client, storyboard_prompt, role="pro", json_mode=True)
    plan = normalize_storyboard(
        parse_json_strict(raw_board),
        duration_sec=duration_sec,
        bpm=bpm,
        peaks=peaks,
        words=words,
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
    print(f"[generate_scenes] Coding {len(scenes)} multi-part 3D scenes in batches of {batch_size}...")

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
You are an Expert Three.js / React Three Fiber CAD & Hardware 3D Animator.
{framing_note}
{STUDIO_KIT_API_DOC}

BATCH TO CODE (Each scene MUST use rich compound hardware like HardwareRack, FinnedHousing, PipeConduit, HeatSinkArray, GlassShell, and RevealSlideGroup cutaways with 8-18 mechanical sub-parts. NEVER output just 1 cylinder + floating dots!):
{json.dumps(batch_specs, indent=2)}

Return ONLY valid JSON where each key is the exact `componentName` (e.g. "Scene_01") and each value is the complete valid TSX file string starting with `import React from "react";`.
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
            print(f"[generate_scenes] Batch {b_start+1} API failed ({exc}); using multi-part fallbacks.")
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
                print(f"  ! {cname} sanitize issue ({exc}); writing multi-part fallback.")
                out_path.write_text(
                    build_safe_fallback_scene_tsx(num, sc["accentHex"], sc["visualConcept"]),
                    encoding="utf-8",
                )

        if b_start + batch_size < len(scenes):
            time.sleep(4)

    write_registry_and_timeline(plan)
    self_heal_scenes(client, plan)
    print(f"[generate_scenes] Complete: {len(scenes)} multi-part dynamic scenes + HUD verified!")


if __name__ == "__main__":
    main()

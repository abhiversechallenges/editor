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
  DataHallBuilding, CitySkylineBlock, PowerPylon, CoolingTower, BatteryContainer,
  SpinGroup, BobGroup, RevealSlideGroup, FlowStream, RisingParticles, OrbitRing, GlbModel
} from "../../components/StudioKit";
import type { DynamicSceneProps } from "../../types";

Props Reference (type V3 = [number, number, number]):
- DynamicSceneProps: { frame: number; localFrame: number; progress: number; accentHex: string }
- DataHallBuilding: { pos?: V3; size?: V3; accentHex?: string; progress: number; frame: number }
  (Concrete-walled data center hall with structural pilasters & sliding cutaway roof revealing server racks inside!)
- CitySkylineBlock: { pos?: V3; scale?: number; accentHex?: string; frame: number }
  (Cluster of 11 varied skyscrapers with lit glowing windows — use whenever city/grid power is mentioned!)
- PowerPylon: { pos?: V3; height?: number; accentHex?: string }
  (Tapered steel transmission lattice tower with cross-arms and HV insulators)
- CoolingTower: { pos?: V3; radius?: number; height?: number; accentHex?: string; cutaway?: boolean; frame: number }
  (Tapered hyperbolic concrete cooling tower with spinning intake fan, blue water basin & rising vapor!)
- BatteryContainer: { pos?: V3; size?: V3; accentHex?: string; frame: number }
  (Utility Megapack battery container with side vents, HVAC pod & animated emerald/cyan charge bar!)
- HardwareRack: { pos?: V3; rot?: V3; size?: V3; bays?: number; accentHex?: string; frame: number }
- FinnedHousing: { pos?: V3; rot?: V3; radius?: number; height?: number; finCount?: number; color?: string; accentHex?: string; cutaway?: boolean; frame: number }
- PipeConduit: { points: V3[]; tubeRadius?: number; pipeColor?: string; fluidColor?: string; flangeCount?: number; count?: number; speed?: number; frame: number }
- HeatSinkArray: { pos?: V3; rot?: V3; size?: V3; finCount?: number; color?: string; pipeColor?: string; glowColor?: string }
- GlassShell: { pos?: V3; rot?: V3; shape?: "box"|"cylinder"; size?: V3; radius?: number; height?: number; color?: string; edgeColor?: string; opacity?: number }
- MatteBox / MatteCylinder / MatteSphere / MatteTorus / MatteCone
- SpinGroup / BobGroup / RevealSlideGroup / FlowStream / RisingParticles / OrbitRing / GlbModel

STRICT HARDWARE & LITERAL VISUAL MATCHING RULES:
1. Export EXACTLY `export const Scene_XX: React.FC<DynamicSceneProps> = ({ frame, localFrame, progress, accentHex }) => { ... }`.
2. NEVER import `three`, `@react-three/fiber`, `remotion`, `useFrame`, `useState`, `useEffect`, or `<Text>` / `<Html>`.
3. LITERALLY MATCH SPOKEN NOUNS:
   - Concrete walls / data hall / roof cutaway -> use `DataHallBuilding`!
   - City / electricity powering a city -> use `CitySkylineBlock` + `PowerPylon` + `PipeConduit`!
   - Server racks / aisle -> use rows of `HardwareRack` + overhead `PipeConduit`!
   - Chips / cold plates / heatsinks -> use `HeatSinkArray` + `PipeConduit` + `GlassShell`!
   - Cooling towers / steam -> use `CoolingTower`!
   - Nuclear reactor / turbine -> use `FinnedHousing` (`cutaway={true}`) + `SpinGroup` rotors + `PipeConduit`!
   - Substations / batteries -> use `PowerPylon` + `BatteryContainer` + `PipeConduit`!
4. Keep hero geometry compact around `[0, 0, 0]` (`X/Z` within `[-3.2 .. +3.2]`, base resting cleanly at `Y = -1.2`) so close camera angles frame it huge (60-70% of screen).
"""

PALETTES = [
    {"bgHex": "#101B2E", "accentHex": "#22D3EE"},
    {"bgHex": "#13223A", "accentHex": "#38BDF8"},
    {"bgHex": "#20161F", "accentHex": "#F97316"},
    {"bgHex": "#102430", "accentHex": "#06B6D4"},
    {"bgHex": "#13253E", "accentHex": "#60A5FA"},
    {"bgHex": "#1F1912", "accentHex": "#F59E0B"},
    {"bgHex": "#102822", "accentHex": "#10B981"},
    {"bgHex": "#191732", "accentHex": "#818CF8"},
]

# Tighter, lower-pitch camera presets so 3D hardware fills 60-70% of the screen cleanly (zero top void!)
BEAT_CAM_PRESETS_16_9 = [
    [
        {"offset": [3.8, 2.0, 4.3], "lookOffset": [0.0, 0.35, 0.0]},
        {"offset": [1.6, 1.3, 3.0], "lookOffset": [0.15, 0.25, 0.0]},
        {"offset": [-2.7, 1.7, 3.4], "lookOffset": [-0.1, 0.2, 0.0]},
    ],
    [
        {"offset": [-3.6, 1.9, 4.1], "lookOffset": [0.0, 0.3, 0.0]},
        {"offset": [-1.0, 1.1, 2.8], "lookOffset": [0.0, 0.3, 0.0]},
        {"offset": [2.9, 1.6, 3.3], "lookOffset": [0.1, 0.2, 0.0]},
    ],
    [
        {"offset": [0.6, 2.9, 4.4], "lookOffset": [0.0, 0.2, 0.0]},
        {"offset": [2.8, 1.3, 2.9], "lookOffset": [0.0, 0.3, 0.0]},
        {"offset": [-1.9, 1.0, 2.8], "lookOffset": [0.0, 0.25, 0.0]},
    ],
]

BEAT_CAM_PRESETS_9_16 = [
    [
        {"offset": [3.7, 2.3, 4.9], "lookOffset": [0.0, 0.35, 0.0]},
        {"offset": [1.1, 1.4, 3.6], "lookOffset": [0.0, 0.3, 0.0]},
        {"offset": [-2.4, 1.8, 4.0], "lookOffset": [0.0, 0.2, 0.0]},
    ],
    [
        {"offset": [-3.5, 2.1, 4.8], "lookOffset": [0.0, 0.3, 0.0]},
        {"offset": [-0.8, 1.2, 3.5], "lookOffset": [0.0, 0.3, 0.0]},
        {"offset": [2.5, 1.7, 3.9], "lookOffset": [0.0, 0.2, 0.0]},
    ],
]

HIGHLIGHT_KEYWORDS = {
    "ai", "gpu", "gpus", "nvidia", "blackwell", "nvlink", "infiniband", "chip", "chips",
    "silicon", "die", "liquid", "cooling", "coolant", "copper", "water", "watts", "megawatts",
    "gigawatts", "mw", "kw", "gw", "kv", "nuclear", "reactor", "reactors", "smr", "uranium",
    "substation", "substations", "transformer", "transformers", "grid", "blackout", "battery",
    "batteries", "megapack", "fiber", "subsea", "cable", "cables", "heat", "thermal",
    "overheat", "overheats", "billion", "billions", "hundred", "thousand", "trillions", "data",
    "center", "supercluster", "power", "electricity", "towers", "manifolds", "turbine",
}

DANGLING_END_WORDS = {"a", "an", "the", "to", "of", "in", "on", "at", "for", "with", "and", "or", "by", "as", "from", "into"}

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


def infer_decimals(val: float) -> int:
    s = f"{val:.4f}".rstrip("0").rstrip(".")
    return len(s.split(".")[1]) if "." in s else 0


def clean_word_boundary_label(raw_label: str, max_chars: int = 34) -> str:
    words = raw_label.strip().upper().split()
    out: List[str] = []
    cur_len = 0
    for w in words:
        add_len = len(w) + (1 if out else 0)
        if cur_len + add_len <= max_chars:
            out.append(w)
            cur_len += add_len
        else:
            break
    if not out and words:
        return words[0][:max_chars]
    return " ".join(out)


def clean_whisper_tokens(raw_words: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Merge Whisper hyphen artifacts (e.g. 'high' + '-speed' -> 'high-speed', 'copper' + '-cold' -> 'copper cold')
    and fix common split compound typos ('over' + 'heats' -> 'overheats').
    """
    cleaned: List[Dict[str, Any]] = []
    for w in raw_words:
        txt = str(w.get("word", "")).strip()
        if not txt:
            continue
        start = float(w["start"])
        end = float(w["end"])
        low = txt.lower()

        if cleaned and txt.startswith("-"):
            prev_low = cleaned[-1]["word"].lower()
            if prev_low == "copper" and low == "-cold":
                cleaned[-1]["word"] = "copper"
                cleaned.append({"word": "cold", "start": start, "end": end})
            else:
                cleaned[-1]["word"] = cleaned[-1]["word"] + txt
                cleaned[-1]["end"] = max(cleaned[-1]["end"], end)
            continue

        if cleaned and cleaned[-1]["word"].lower() == "over" and low.startswith("heat"):
            cleaned[-1]["word"] = "over" + txt
            cleaned[-1]["end"] = max(cleaned[-1]["end"], end)
            continue

        cleaned.append({"word": txt, "start": start, "end": end})
    return cleaned


def build_subtitle_chunks(words: List[Dict[str, Any]], total_dur: float) -> List[Dict[str, Any]]:
    tokens = clean_whisper_tokens(words)
    chunks: List[Dict[str, Any]] = []
    if not tokens:
        return chunks

    buf: List[Dict[str, Any]] = []
    for idx, tok in enumerate(tokens):
        buf.append(tok)
        txt = tok["word"]
        low = re.sub(r"[^a-z]", "", txt.lower())
        ends_punct = txt.endswith((".", "!", "?", ","))
        next_gap = (tokens[idx + 1]["start"] - tok["end"]) if idx + 1 < len(tokens) else 1.0
        next_is_last = idx + 1 == len(tokens) - 1

        should_split = False
        if next_is_last and len(buf) >= 3:
            should_split = False
        elif ends_punct and len(buf) >= 2:
            should_split = True
        elif next_gap > 0.24 and len(buf) >= 2:
            should_split = True
        elif len(buf) >= 4 and low not in DANGLING_END_WORDS:
            should_split = True
        elif len(buf) >= 6:
            should_split = True

        if should_split:
            chunk_words = []
            for item in buf:
                clean_tok = re.sub(r"[^a-z0-9$%]", "", item["word"].lower())
                is_hi = bool(re.search(r"\d", clean_tok)) or clean_tok in HIGHLIGHT_KEYWORDS
                chunk_words.append({"text": item["word"], "highlight": is_hi})
            chunks.append(
                {
                    "startSec": round(buf[0]["start"], 3),
                    "endSec": round(min(total_dur, buf[-1]["end"] + 0.08), 3),
                    "words": chunk_words,
                }
            )
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
                "endSec": round(min(total_dur, buf[-1]["end"] + 0.15), 3),
                "words": chunk_words,
            }
        )

    # Guarantee strictly non-overlapping sequential subtitle chunks!
    for i in range(len(chunks) - 1):
        curr = chunks[i]
        nxt = chunks[i + 1]
        if curr["endSec"] >= nxt["startSec"] - 0.015:
            mid = round((curr["endSec"] + nxt["startSec"]) * 0.5, 3)
            curr["endSec"] = max(round(curr["startSec"] + 0.08, 3), round(nxt["startSec"] - 0.02, 3))
            if nxt["startSec"] <= curr["endSec"]:
                nxt["startSec"] = round(curr["endSec"] + 0.02, 3)
                if nxt["endSec"] <= nxt["startSec"]:
                    nxt["endSec"] = round(nxt["startSec"] + 0.15, 3)
        _ = mid if False else None

    return chunks


def build_safe_fallback_scene_tsx(scene_num: int, accent_hex: str, title: str) -> str:
    variant = scene_num % 4
    safe_comment = re.sub(r"[^A-Za-z0-9 ,.-]", "", title)[:60]
    if variant == 0:
        body = f"""
      <DataHallBuilding pos={{[-0.7, 0, 0]}} size={{[3.0, 1.5, 2.2]}} accentHex={{"{accent_hex}"}} progress={{progress}} frame={{frame}} />
      <CitySkylineBlock pos={{[2.1, -0.3, 0.2]}} scale={{0.85}} accentHex="#F59E0B" frame={{frame}} />
      <PipeConduit points={{[[-0.7, -0.8, 0.9], [0.8, -0.8, 0.6], [2.0, -0.8, 0.2]]}} fluidColor={{"{accent_hex}"}} flangeCount={{3}} speed={{0.85}} frame={{frame}} />"""
    elif variant == 1:
        body = f"""
      <MatteBox pos={{[0, -1.1, 0]}} size={{[4.8, 0.2, 3.6]}} color="#2D3E58" />
      <HardwareRack pos={{[-1.2, 0.0, 0]}} size={{[1.05, 2.0, 1.05]}} bays={{6}} accentHex={{"{accent_hex}"}} frame={{frame}} />
      <HardwareRack pos={{[1.2, 0.0, 0]}} size={{[1.05, 2.0, 1.05]}} bays={{6}} accentHex={{"{accent_hex}"}} frame={{frame}} />
      <PipeConduit points={{[[-1.2, 1.15, 0], [0, 1.35, 0], [1.2, 1.15, 0]]}} fluidColor={{"{accent_hex}"}} flangeCount={{3}} speed={{0.9}} frame={{frame}} />"""
    elif variant == 2:
        body = f"""
      <MatteBox pos={{[0, -1.1, 0]}} size={{[4.6, 0.2, 3.8]}} color="#2B3B52" />
      <CoolingTower pos={{[-1.15, 0.1, 0]}} radius={{0.95}} height={{2.2}} accentHex={{"{accent_hex}"}} cutaway={{true}} frame={{frame}} />
      <CoolingTower pos={{[1.25, 0.1, 0.2]}} radius={{0.85}} height={{2.0}} accentHex={{"{accent_hex}"}} cutaway={{false}} frame={{frame}} />
      <PipeConduit points={{[[-2.3, -0.7, 0.6], [-1.15, -0.7, 0.4], [1.25, -0.7, 0.4]]}} fluidColor="#06B6D4" flangeCount={{3}} speed={{0.8}} frame={{frame}} />"""
    else:
        body = f"""
      <MatteBox pos={{[0, -1.1, 0]}} size={{[5.2, 0.2, 3.4]}} color="#2D3E58" />
      <FinnedHousing pos={{[-1.4, -0.05, 0]}} radius={{0.78}} height={{1.8}} finCount={{8}} accentHex="#38BDF8" cutaway={{true}} frame={{frame}} />
      <PowerPylon pos={{[0.1, -0.05, -0.3]}} height={{2.2}} accentHex="#F59E0B" />
      <BatteryContainer pos={{[1.65, -0.25, 0.2]}} size={{[1.4, 1.3, 1.1]}} accentHex={{"{accent_hex}"}} frame={{frame}} />
      <PipeConduit points={{[[-1.4, 0.6, 0], [0.1, 0.75, -0.3], [1.65, 0.2, 0.2]]}} fluidColor={{"{accent_hex}"}} flangeCount={{3}} speed={{0.9}} frame={{frame}} />"""

    return f"""import React from "react";
import {{
  MatteBox, HardwareRack, FinnedHousing, PipeConduit,
  DataHallBuilding, CitySkylineBlock, PowerPylon, CoolingTower, BatteryContainer
}} from "../../components/StudioKit";
import type {{ DynamicSceneProps }} from "../../types";

// Fallback: {safe_comment}
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
        label = clean_word_boundary_label(str(item.get("label") or ""), max_chars=34)
        if not label:
            continue
        anc = item.get("anchorPct")
        box = item.get("boxPct")
        if not (isinstance(anc, list) and len(anc) == 2):
            anc = [50, 50] if ci == 0 else [45, 58]
        if not (isinstance(box, list) and len(box) == 2):
            box = [72, 22] if not is_short else [62, 24]
        ax = round(min(76.0, max(24.0, float(anc[0]))), 1)
        ay = round(min(72.0, max(26.0, float(anc[1]))), 1)
        bx = round(min(82.0, max(16.0, float(box[0]))), 1)
        by = round(min(68.0, max(18.0, float(box[1]))), 1)
        if bx < 38 and by < 32:
            bx = 70.0
        clean.append({"label": label, "anchorPct": [ax, ay], "boxPct": [bx, by]})
    return clean


def normalize_stat_counter(raw_stat: Any) -> Any:
    if not isinstance(raw_stat, dict):
        return None
    label = clean_word_boundary_label(str(raw_stat.get("label") or ""), max_chars=28)
    if not label:
        return None
    try:
        from_val = float(raw_stat.get("fromVal", 0))
        to_val = float(raw_stat.get("toVal", 100))
    except Exception:
        return None

    inferred_dec = max(infer_decimals(from_val), infer_decimals(to_val))
    raw_dec = raw_stat.get("decimals")
    if isinstance(raw_dec, (int, float)) and int(raw_dec) >= inferred_dec:
        decimals = min(3, int(raw_dec))
    else:
        decimals = min(3, inferred_dec)

    return {
        "label": label,
        "fromVal": from_val,
        "toVal": to_val,
        "prefix": str(raw_stat.get("prefix") or "")[:6],
        "suffix": str(raw_stat.get("suffix") or "")[:10],
        "decimals": decimals,
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

            # Keep cameras close & well-centered so 3D hardware fills ~65% of screen
            cam_x = round(min(6.2, max(-6.2, float(off[0]))), 3)
            cam_y = round(min(3.5, max(0.7, float(off[1]))), 3)
            cam_z = round(min(6.5, max(-6.5, float(off[2]))), 3)
            if abs(cam_x) + abs(cam_z) > 9.5:
                cam_x = round(cam_x * 0.78, 3)
                cam_z = round(cam_z * 0.78, 3)

            callouts = normalize_callouts(rb.get("callouts"), is_short=is_short)
            if not callouts:
                concept_short = clean_word_boundary_label(str(sc.get("visualConcept") or "CORE HARDWARE"), 24)
                callouts = [{"label": concept_short, "anchorPct": [50, 52], "boxPct": [72, 24]}]

            stat_counter = normalize_stat_counter(rb.get("statCounter"))
            if idx == 0 and bi == 0 and not stat_counter:
                stat_counter = {
                    "label": "TOTAL CAMPUS CAPEX",
                    "fromVal": 0.0,
                    "toVal": 100.0,
                    "prefix": "$",
                    "suffix": "B",
                    "decimals": 0,
                }

            beat_peaks = [p for p in peaks if b_start <= p <= b_end]
            trigger_sec = 0.0 if (idx == 0 and bi == 0) else (beat_peaks[0] if beat_peaks else round(b_start + 0.15, 3))

            clean_beats.append(
                {
                    "id": f"b_{idx + 1:02d}_{bi + 1:02d}",
                    "startSec": b_start,
                    "endSec": round(b_end, 3),
                    "triggerSec": trigger_sec,
                    "cameraOffset": [cam_x, cam_y, cam_z],
                    "lookOffset": [
                        round(min(0.8, max(-0.8, float(look[0]))), 3),
                        round(min(0.6, max(0.0, float(look[1]))), 3),
                        round(min(0.8, max(-0.8, float(look[2]))), 3),
                    ],
                    "callouts": callouts,
                    "statCounter": stat_counter,
                }
            )

        world_pos = [
            round(idx * 28.0, 2),
            round(2.4 if idx % 2 == 1 else 0.0, 2),
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
            print(f"[self_heal] Swapping stubborn {cname} to multi-part fallback.")
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
        "VERTICAL 9:16 SHORT (1080x1920): Keep X tight [-2.0 .. +2.0], build TALL vertical stacked hardware [-1.2 .. +2.4 Y]."
        if is_short
        else "WIDESCREEN 16:9 (1920x1080): Keep hero centered around [0, 0, 0] within [-3.2 .. +3.2] X/Z and base resting at Y = -1.1."
    )

    storyboard_prompt = f"""
You are the Lead 3D Motion Director & Technical Illustrator (Branch Education / Real Engineering style with crisp HUD callouts).

ASPECT & CLOSE CAMERA FRAMING:
{framing_note}
CRITICAL FRAMING RULE: Keep `cameraOffset` CLOSE so the 3D subject fills 60-70% of the screen (`X/Z` within 2.5..4.6, `Y` within 1.1..2.6, `lookOffset` Y around `0.25`). NEVER place the camera far away!

USER VISUAL DESCRIPTION:
{visuals_prompt if visuals_prompt else "(No visuals.txt uploaded — invent vivid multi-part engineering & infrastructure 3D scenes matching the voiceover!)"}

CUSTOM .GLB MODELS: {json.dumps(custom_models)}

VOICEOVER SEGMENTS ({duration_sec:.2f}s):
{json.dumps([{"start": s["start"], "end": s["end"], "text": s["text"]} for s in transcript.get("segments", [])], ensure_ascii=False)}

VOCAL EMPHASIS PEAKS (seconds):
{json.dumps(peaks[:120])}

HARD RULES:
1. Divide the {duration_sec:.2f}s narration into {min_sc} to {max_sc} unique 3D chapters (`scenes`), roughly 6-10s each!
2. LITERAL NOUN MATCHING: Whenever narration mentions concrete walls, warehouses, cities, power pylons, cooling towers, server racks, or batteries, specify those EXACT literal structures in `visualSpec` (DataHallBuilding, CitySkylineBlock, PowerPylon, CoolingTower, HardwareRack, BatteryContainer)!
3. FORCED 3-4 SECOND BEATS: Inside EVERY chapter, define 2 or 3 `beats` (~3-4s each) with noticeably different `cameraOffset` angles plus:
   - `callouts`: 1-2 short labels (MAX 3-4 words / <= 26 chars so nothing wraps awkwardly, e.g. `"4NM SILICON DIE"`, `"345 KV SUBSTATION"`, `"600 kW / RACK"`) with `anchorPct` [30..70, 32..66] and `boxPct` [18..78, 20..64].
   - `statCounter`: animated stat card (`label`, `fromVal`, `toVal`, `prefix`, `suffix`, `decimals`) whenever specs/numbers are mentioned. Set `decimals` properly (`1` for 3.2/4.5, `2` for 1.12, `3` for 99.999, `0` for whole numbers).
4. STUDIO COLORS: Rich readable slate/blueprint `bgHex` (#101B2E, #13223A, #20161F, #102430, #102822) + bright `accentHex`.

Return ONLY valid JSON:
{{
  "scenes": [
    {{
      "visualConcept": "Data Hall Campus & City Grid",
      "visualSpec": "DataHallBuilding concrete walls connected via PowerPylon and PipeConduit to CitySkylineBlock",
      "endSec": 8.0,
      "bgHex": "#101B2E",
      "accentHex": "#22D3EE",
      "beats": [
        {{
          "cameraOffset": [3.8, 2.0, 4.3],
          "lookOffset": [0.0, 0.35, 0.0],
          "callouts": [{{"label": "1,000 MW DATA HALL", "anchorPct": [46, 52], "boxPct": [74, 24]}}],
          "statCounter": {{"label": "TOTAL CAPEX", "fromVal": 0, "toVal": 100, "prefix": "$", "suffix": "B", "decimals": 0}}
        }},
        {{
          "cameraOffset": [1.5, 1.3, 3.0],
          "lookOffset": [0.15, 0.25, 0.0],
          "callouts": [{{"label": "CITY POWER DRAW", "anchorPct": [60, 56], "boxPct": [22, 34]}}]
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
    print(f"[generate_scenes] Coding {len(scenes)} literal multi-part 3D scenes in batches of {batch_size}...")

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
You are an Expert Three.js / React Three Fiber CAD & Infrastructure 3D Animator.
{framing_note}
{STUDIO_KIT_API_DOC}

BATCH TO CODE (Use literal architectural components like DataHallBuilding, CitySkylineBlock, PowerPylon, CoolingTower, BatteryContainer, HardwareRack, FinnedHousing, PipeConduit, HeatSinkArray, GlassShell! Keep models grounded around Y = -1.1 and X/Z within [-3.2..+3.2]):
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
    print(f"[generate_scenes] Complete: {len(scenes)} literal multi-part scenes + HUD verified!")


if __name__ == "__main__":
    main()

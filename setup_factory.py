#!/usr/bin/env python3
"""
InfraVerse Unlimited Dynamic 3D Factory (v3.1).
Fixes:
  1. Closer hero camera framing (~60-70% fill) + grounded 3D blueprint floor grid + Frame-0 HUD visibility
  2. Literal infrastructure prefabs (DataHallBuilding, CitySkylineBlock, PowerPylon, CoolingTower, BatteryContainer)
  3. Zero callout truncation, automatic decimal precision inference, non-overlapping subtitle chunks, Whisper typo cleanup
  4. Smarter phrase chunking + larger, better-positioned bottom HUD captions
"""

import subprocess
import sys
from pathlib import Path
from typing import Dict

ROOT = Path(__file__).resolve().parent
FILES: Dict[str, str] = {}

FILES[".gitignore"] = r'''
node_modules/
build_bundle/
chunks/
work/*
!work/.gitkeep
out/*
!out/.gitkeep
public/audio/*.mp3
public/audio/sfx/*.mp3
!public/audio/.gitkeep
!public/audio/sfx/.gitkeep
__pycache__/
*.pyc
.env
.DS_Store
'''

FILES[".gitattributes"] = r'''
* text=auto eol=lf
'''

FILES["package.json"] = r'''
{
  "name": "infraverse-dynamic-3d-factory",
  "version": "3.1.0",
  "private": true,
  "description": "High-contrast CAD 3D + 2D Remotion HUD engineering documentary factory",
  "scripts": {
    "dev": "remotion studio src/index.ts",
    "build": "remotion bundle src/index.ts --public-dir public --out-dir build_bundle",
    "typecheck": "tsc --noEmit"
  },
  "dependencies": {
    "@react-three/drei": "9.120.4",
    "@react-three/fiber": "8.17.10",
    "@remotion/cli": "4.0.543",
    "@remotion/google-fonts": "4.0.543",
    "@remotion/three": "4.0.543",
    "react": "18.3.1",
    "react-dom": "18.3.1",
    "remotion": "4.0.543",
    "three": "0.170.0"
  },
  "devDependencies": {
    "@types/node": "22.13.0",
    "@types/react": "18.3.12",
    "@types/react-dom": "18.3.1",
    "@types/three": "0.170.0",
    "typescript": "5.6.3"
  }
}
'''

FILES["requirements.txt"] = r'''
google-genai>=2.30.0
faster-whisper>=1.1.0
librosa>=0.10.2
soundfile>=0.12.1
numpy>=1.26.4,<2.2.0
scipy>=1.13.0
'''

FILES["tsconfig.json"] = r'''
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ES2022",
    "moduleResolution": "bundler",
    "jsx": "react-jsx",
    "strict": true,
    "esModuleInterop": true,
    "resolveJsonModule": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "noEmit": true,
    "types": ["node"]
  },
  "include": ["src/**/*", "remotion.config.ts"]
}
'''

FILES["remotion.config.ts"] = r'''
import { Config } from "@remotion/cli/config";

Config.setVideoImageFormat("jpeg");
Config.setJpegQuality(90);
Config.setOffthreadVideoCacheSizeInBytes(1024 * 1024 * 1024);
Config.setCodec("h264");
Config.setPixelFormat("yuv420p");
'''

FILES["input/visuals_EXAMPLE.txt"] = r'''
# Upload your long voiceover.mp3 + visuals.txt inside input/ for a 16:9 (1920x1080) video!
'''

FILES["input_short/visuals_EXAMPLE.txt"] = r'''
# Upload your X-second Short voiceover.mp3 + visuals.txt inside input_short/ for a 9:16 (1080x1920) Short!
'''

for gitkeep_rel in (
    "input/.gitkeep",
    "input_short/.gitkeep",
    "out/.gitkeep",
    "work/.gitkeep",
    "public/audio/.gitkeep",
    "public/audio/sfx/.gitkeep",
    "public/models/.gitkeep",
):
    FILES[gitkeep_rel] = ""

FILES["scripts/gemini_helper.py"] = r'''
import json
import os
import re
import time
from typing import Any, Optional

from google import genai
from google.genai import types
from google.genai.errors import APIError

PRO_LADDER = [
    ("gemini-4-hydrogen", "high", 65536, True),
    ("gemini-3.8-flash", "low", 32768, True),
    ("gemini-3.6-flash", None, 32768, True),
    ("gemini-3.5-flash-lite", None, 32768, True),
    ("gemini-3.1-flash-lite", None, 32768, True),
    ("gemma-4-31b-it", None, 8192, False),
]

FLASH_LADDER = [
    ("gemini-3.6-flash", None, 32768, True),
    ("gemini-4-hydrogen", "high", 65536, True),
    ("gemini-3.5-flash-lite", None, 32768, True),
    ("gemini-3.1-flash-lite", None, 32768, True),
    ("gemini-3.8-flash", "low", 32768, True),
    ("gemma-4-31b-it", None, 8192, False),
]

_COOLDOWN_UNTIL: dict[str, float] = {}


def get_client() -> genai.Client:
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError(
            "Missing GEMINI_API_KEY secret. Add it in GitHub Repo -> Settings -> Secrets -> Actions."
        )
    return genai.Client(
        api_key=api_key,
        http_options=types.HttpOptions(timeout=600_000),
    )


def clean_json_text(raw: str) -> str:
    text = (raw or "").strip()
    fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if fence_match:
        text = fence_match.group(1).strip()
    return text


def clean_tsx_text(raw: str) -> str:
    text = (raw or "").strip()
    fence_match = re.search(r"```(?:tsx|typescript|ts|jsx)?\s*([\s\S]*?)```", text)
    if fence_match:
        text = fence_match.group(1).strip()
    return text


def generate_with_fallback(
    client: genai.Client,
    contents: Any,
    role: str = "flash",
    json_mode: bool = False,
    max_output_tokens: int = 65536,
    temperature: float = 0.4,
) -> str:
    ladder = PRO_LADDER if role == "pro" else FLASH_LADDER
    dead_models: set[str] = set()
    last_error: Optional[Exception] = None

    for pass_num in range(1, 3):
        now = time.time()
        for model_name, thinking_lvl, cap, supports_json in ladder:
            key = f"{model_name}:{thinking_lvl}"
            if key in dead_models:
                continue
            if pass_num == 1 and _COOLDOWN_UNTIL.get(model_name, 0) > now:
                continue

            config_kwargs: dict[str, Any] = {
                "max_output_tokens": min(cap, max_output_tokens) if cap < 65536 else cap,
            }
            if thinking_lvl:
                config_kwargs["thinking_config"] = types.ThinkingConfig(thinking_level=thinking_lvl)
            if json_mode and supports_json:
                config_kwargs["response_mime_type"] = "application/json"

            final_contents = contents
            if json_mode and not supports_json and isinstance(contents, str):
                final_contents = contents + "\n\nCRITICAL: Return ONLY valid raw JSON with no markdown fences."

            config = types.GenerateContentConfig(**config_kwargs)

            try:
                print(
                    f"[gemini_helper] Pass {pass_num} -> {model_name} (thinking={thinking_lvl or 'off'})...",
                    flush=True,
                )
                response = client.models.generate_content(
                    model=model_name,
                    contents=final_contents,
                    config=config,
                )
                text = response.text or ""
                if not text.strip():
                    raise RuntimeError(f"Empty response from {model_name}")
                print(f"[gemini_helper] Success with {model_name} ({len(text)} chars).", flush=True)
                return clean_json_text(text) if json_mode else text
            except APIError as exc:
                last_error = exc
                msg = str(exc).lower()
                if any(
                    k in msg
                    for k in ("404", "403", "not found", "permission", "restricted", "limit: 0", "unsupported")
                ):
                    print(f"[gemini_helper] {model_name} unavailable; skipping.", flush=True)
                    dead_models.add(key)
                    continue
                if "503" in msg or "unavailable" in msg:
                    _COOLDOWN_UNTIL[model_name] = time.time() + 90.0
                print(f"[gemini_helper] {model_name} busy ({exc}); switching...", flush=True)
                time.sleep(5)
            except Exception as exc:
                last_error = exc
                print(f"[gemini_helper] {model_name} error ({exc}); waiting 4s...", flush=True)
                time.sleep(4)

        if pass_num == 1:
            _COOLDOWN_UNTIL.clear()
            print("[gemini_helper] Pass 1 exhausted; cooling 18s before Pass 2...", flush=True)
            time.sleep(18)

    raise RuntimeError(f"All Gemini/Gemma models failed. Last error: {last_error}")


def parse_json_strict(raw: str) -> Any:
    return json.loads(clean_json_text(raw))
'''

FILES["scripts/analyze_audio.py"] = r'''
import json
import os
import subprocess
from pathlib import Path
from typing import Any, Dict, List

import librosa
import numpy as np
from faster_whisper import WhisperModel
from scipy.signal import find_peaks

ROOT = Path(__file__).resolve().parent.parent
WORK_DIR = ROOT / "work"

AUDIO_EXTS = {".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg"}
VIDEO_EXTS = {".mp4", ".mov", ".mkv", ".webm"}


def get_input_dir() -> Path:
    folder = os.environ.get("INPUT_FOLDER", "input").strip() or "input"
    return ROOT / folder


def git_commit_timestamp(path: Path) -> int:
    try:
        res = subprocess.run(
            ["git", "log", "-n", "1", "--format=%ct", "--", str(path.relative_to(ROOT))],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            check=False,
        )
        val = (res.stdout or "").strip()
        if val.isdigit():
            return int(val)
    except Exception:
        pass
    return int(path.stat().st_mtime)


def find_latest_input(input_dir: Path) -> Path:
    if not input_dir.exists():
        raise FileNotFoundError(f"{input_dir.name}/ directory does not exist.")
    candidates = [
        p
        for p in input_dir.iterdir()
        if p.is_file()
        and p.name != ".gitkeep"
        and p.suffix.lower() in (AUDIO_EXTS | VIDEO_EXTS)
    ]
    if not candidates:
        raise FileNotFoundError(f"No audio (.mp3/.wav) or video (.mp4) found inside {input_dir.name}/.")
    return max(candidates, key=lambda p: (git_commit_timestamp(p), p.stat().st_mtime, p.name))


def run_ffmpeg(args: List[str]) -> None:
    subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error"] + args, check=True)


def clean_and_normalize_audio(src_path: Path, trim_silence: bool, preview_sec: float, out_wav: Path) -> None:
    WORK_DIR.mkdir(parents=True, exist_ok=True)
    filters = ["highpass=f=80", "afftdn=nf=-25"]
    if trim_silence:
        filters.append("silenceremove=stop_periods=-1:stop_duration=0.65:stop_threshold=-42dB")
    filters.append("loudnorm=I=-14:TP=-1.5:LRA=11")

    ff_args = ["-i", str(src_path)]
    if preview_sec > 0:
        ff_args += ["-t", f"{preview_sec:.2f}"]
    ff_args += [
        "-vn",
        "-af",
        ",".join(filters),
        "-ar",
        "48000",
        "-ac",
        "1",
        "-c:a",
        "pcm_s16le",
        str(out_wav),
    ]
    run_ffmpeg(ff_args)


def transcribe_audio(wav_path: Path) -> Dict[str, Any]:
    model_size = os.environ.get("WHISPER_MODEL", "small")
    print(f"[analyze_audio] Transcribing with faster-whisper ({model_size}, CPU int8)...")
    model = WhisperModel(model_size, device="cpu", compute_type="int8")

    segments_iter, info = model.transcribe(
        str(wav_path),
        beam_size=5,
        word_timestamps=True,
        vad_filter=True,
        vad_parameters={"min_silence_duration_ms": 400},
        initial_prompt=(
            "AI supercluster, Nvidia GPU, NVLink, InfiniBand, liquid cooling, cold plates, "
            "overheats, data center, nuclear SMR, small modular reactor, substation, transformer, "
            "345 kV, 600 kW, 1,000 MW, CDU, subsea fiber optic cable, battery farm, blackout."
        ),
    )

    segments: List[Dict[str, Any]] = []
    words: List[Dict[str, Any]] = []
    for seg in segments_iter:
        seg_words: List[Dict[str, Any]] = []
        if seg.words:
            for w in seg.words:
                w_item = {
                    "word": w.word.strip(),
                    "start": round(float(w.start), 3),
                    "end": round(float(w.end), 3),
                }
                if w_item["word"]:
                    words.append(w_item)
                    seg_words.append(w_item)
        segments.append(
            {
                "id": seg.id,
                "start": round(float(seg.start), 3),
                "end": round(float(seg.end), 3),
                "text": seg.text.strip(),
                "words": seg_words,
            }
        )

    return {
        "language": info.language,
        "duration_sec": round(float(info.duration), 3),
        "segments": segments,
        "words": words,
        "full_text": " ".join(s["text"] for s in segments),
    }


def analyze_beats(wav_path: Path) -> Dict[str, Any]:
    print("[analyze_audio] Detecting vocal emphasis peaks & tempo...")
    y, sr = librosa.load(str(wav_path), sr=22050, mono=True)
    duration_sec = float(librosa.get_duration(y=y, sr=sr))

    hop_length = 512
    rms = librosa.feature.rms(y=y, frame_length=2048, hop_length=hop_length)[0]
    onset_env = librosa.onset.onset_strength(y=y, sr=sr, hop_length=hop_length)

    rms_norm = rms / (np.max(rms) + 1e-8)
    onset_norm = onset_env / (np.max(onset_env) + 1e-8)
    combined = 0.65 * rms_norm + 0.35 * onset_norm

    min_distance = int((2.0 * sr) / hop_length)
    peaks, _ = find_peaks(
        combined,
        height=float(np.percentile(combined, 68)),
        distance=max(1, min_distance),
        prominence=0.09,
    )
    peak_times = [round(float(librosa.frames_to_time(p, sr=sr, hop_length=hop_length)), 3) for p in peaks]

    tempo, _ = librosa.beat.beat_track(onset_envelope=onset_env, sr=sr, hop_length=hop_length)
    bpm_val = float(np.atleast_1d(tempo)[0]) if np.size(tempo) > 0 else 102.0
    if bpm_val < 70 or bpm_val > 135:
        bpm_val = 102.0

    return {
        "duration_sec": round(duration_sec, 3),
        "bpm": round(bpm_val, 1),
        "emphasis_peaks": peak_times,
    }


def main() -> None:
    input_dir = get_input_dir()
    src = find_latest_input(input_dir)
    trim_silence = os.environ.get("TRIM_SILENCE", "false").lower() == "true"
    preview_sec = float(os.environ.get("PREVIEW_SECONDS", "0") or "0")

    print(f"[analyze_audio] Selected input from {input_dir.name}/: {src.name}")
    clean_wav = WORK_DIR / "clean_voiceover.wav"
    clean_and_normalize_audio(src, trim_silence=trim_silence, preview_sec=preview_sec, out_wav=clean_wav)

    transcript = transcribe_audio(clean_wav)
    beats = analyze_beats(clean_wav)
    transcript["duration_sec"] = beats["duration_sec"]

    (WORK_DIR / "input_meta.json").write_text(
        json.dumps(
            {
                "input_folder": input_dir.name,
                "source_file": str(src.relative_to(ROOT)),
                "duration_sec": beats["duration_sec"],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (WORK_DIR / "transcript.json").write_text(
        json.dumps(transcript, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    (WORK_DIR / "beats.json").write_text(json.dumps(beats, indent=2), encoding="utf-8")
    print(f"[analyze_audio] Done: {beats['duration_sec']:.2f}s, {len(transcript['words'])} words.")


if __name__ == "__main__":
    main()
'''

FILES["scripts/generate_scenes.py"] = r'''
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
'''

FILES["scripts/validate_scenes.py"] = r'''
import json
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parent.parent
PLAN_PATH = ROOT / "work" / "scene_plan.json"
SCENES_DIR = ROOT / "src" / "generated" / "scenes"
TIMELINE_PATH = ROOT / "src" / "generated" / "GeneratedTimeline.tsx"

FORBIDDEN_3D_TOKENS = ("<Text", "<Html", "<Sequence")


def audit_plan(plan: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    scenes = plan.get("scenes") or []
    if not scenes:
        return ["scene_plan.json has 0 scenes."]

    seen_concepts: set[str] = set()
    for idx, sc in enumerate(scenes):
        concept = sc.get("visualConcept", "").strip().lower()
        if concept in seen_concepts:
            errors.append(f"Duplicate visualConcept detected: {concept}")
        seen_concepts.add(concept)

        if idx > 0 and abs(float(sc["startSec"]) - float(scenes[idx - 1]["endSec"])) > 0.01:
            errors.append(f"Timeline discontinuity between {scenes[idx-1]['id']} and {sc['id']}.")

        beats = sc.get("beats") or []
        if len(beats) < 2:
            errors.append(f"{sc['id']} has fewer than 2 micro-beats (visual hold too static).")

        for b in beats:
            b_dur = float(b["endSec"]) - float(b["startSec"])
            if b_dur > 5.5:
                errors.append(f"{b['id']} hold duration {b_dur:.2f}s exceeds 5.5s max beat pace.")

        cname = sc.get("componentName")
        if not (SCENES_DIR / f"{cname}.tsx").exists():
            errors.append(f"Missing generated scene component: {cname}.tsx")

    subtitles = plan.get("subtitleChunks") or []
    for i in range(len(subtitles) - 1):
        if float(subtitles[i]["endSec"]) > float(subtitles[i + 1]["startSec"]):
            errors.append(f"Overlapping subtitleChunks at index {i} ({subtitles[i]['endSec']} > {subtitles[i+1]['startSec']}).")

    return errors


def audit_3d_files() -> List[str]:
    errors: List[str] = []
    files = list(SCENES_DIR.glob("Scene_*.tsx")) + [TIMELINE_PATH]
    for f in files:
        if not f.exists():
            continue
        txt = f.read_text(encoding="utf-8")
        for m in FORBIDDEN_3D_TOKENS:
            if m in txt:
                errors.append(f"Forbidden token '{m}' found inside {f.name}")
    return errors


def main() -> None:
    if not PLAN_PATH.exists():
        raise SystemExit("Missing work/scene_plan.json")
    plan = json.loads(PLAN_PATH.read_text(encoding="utf-8"))
    errs = audit_plan(plan) + audit_3d_files()
    if errs:
        raise SystemExit("[validate_scenes] FAILED:\n - " + "\n - ".join(errs))
    total_beats = sum(len(s.get("beats", [])) for s in plan["scenes"])
    print(f"[validate_scenes] PASSED: {len(plan['scenes'])} scenes, {total_beats} visual beats, zero overlaps.")


if __name__ == "__main__":
    main()
'''

FILES["scripts/mix_audio.py"] = r'''
import json
import subprocess
from pathlib import Path

import numpy as np
import soundfile as sf
from scipy.signal import butter, sosfilt

ROOT = Path(__file__).resolve().parent.parent
WORK_DIR = ROOT / "work"
SAMPLE_RATE = 48000


def lowpass(signal: np.ndarray, cutoff_hz: float, order: int = 4) -> np.ndarray:
    sos = butter(order, cutoff_hz, btype="low", fs=SAMPLE_RATE, output="sos")
    return sosfilt(sos, signal)


def bandpass(signal: np.ndarray, low_hz: float, high_hz: float, order: int = 3) -> np.ndarray:
    sos = butter(order, [low_hz, high_hz], btype="band", fs=SAMPLE_RATE, output="sos")
    return sosfilt(sos, signal)


def synthesize_documentary_bgm(n_samples: int, bpm: float) -> np.ndarray:
    t = np.arange(n_samples, dtype=np.float64) / SAMPLE_RATE
    bar_sec = (60.0 / max(75.0, min(125.0, bpm))) * 4.0
    chords = [
        [130.81, 196.00, 233.08, 293.66],
        [103.83, 155.56, 196.00, 261.63],
        [87.31, 174.61, 207.65, 261.63],
        [98.00, 146.83, 196.00, 233.08],
    ]
    bar_idx = (t / bar_sec).astype(int) % len(chords)
    bar_phase = (t % bar_sec) / bar_sec
    env = np.sin(np.pi * np.clip(bar_phase, 0.0, 1.0)) ** 0.4

    left = np.zeros(n_samples, dtype=np.float64)
    right = np.zeros(n_samples, dtype=np.float64)
    for c_i, freqs in enumerate(chords):
        mask = (bar_idx == c_i).astype(np.float64)
        sig_l = np.zeros(n_samples, dtype=np.float64)
        sig_r = np.zeros(n_samples, dtype=np.float64)
        for v_i, freq in enumerate(freqs):
            detune = 1.0025 if v_i % 2 == 0 else 0.9975
            sig_l += 0.22 * np.sin(2.0 * np.pi * freq * t)
            sig_r += 0.22 * np.sin(2.0 * np.pi * freq * detune * t + 0.5)
        sub = 0.28 * np.sin(2.0 * np.pi * (freqs[0] * 0.5) * t)
        left += mask * env * (sig_l + sub)
        right += mask * env * (sig_r + sub)

    pulse_period = 60.0 / bpm
    pulse_env = np.exp(-((t % pulse_period) / pulse_period) * 6.5)
    pulse = np.sin(2.0 * np.pi * 65.0 * t) * pulse_env * 0.16

    left = lowpass(left + pulse, 920.0)
    right = lowpass(right + pulse, 920.0)
    stereo = np.column_stack([left, right])
    stereo = stereo / (float(np.max(np.abs(stereo))) + 1e-9)

    fade_in = min(n_samples, int(1.5 * SAMPLE_RATE))
    fade_out = min(n_samples, int(2.0 * SAMPLE_RATE))
    if fade_in > 0:
        stereo[:fade_in] *= np.linspace(0.0, 1.0, fade_in)[:, None]
    if fade_out > 0:
        stereo[-fade_out:] *= np.linspace(1.0, 0.0, fade_out)[:, None]
    return stereo


def synthesize_glide_swell() -> np.ndarray:
    rng = np.random.default_rng(11)
    n = int(1.05 * SAMPLE_RATE)
    t = np.arange(n) / SAMPLE_RATE
    env = np.sin(np.pi * t / 1.05) ** 1.8
    air = bandpass(rng.normal(0.0, 1.0, n), 160.0, 950.0) * env
    sub = np.sin(2.0 * np.pi * (54.0 - 16.0 * (t / 1.05)) * t) * env * 0.35
    sig = air * 0.65 + sub
    stereo = np.column_stack([sig, sig * 0.96])
    return stereo / (float(np.max(np.abs(stereo))) + 1e-9)


def synthesize_hud_tick() -> np.ndarray:
    n = int(0.08 * SAMPLE_RATE)
    t = np.arange(n) / SAMPLE_RATE
    sig = np.sin(2.0 * np.pi * 1480.0 * t) * np.exp(-t * 60.0) * 0.6
    stereo = np.column_stack([sig, sig])
    return stereo / (float(np.max(np.abs(stereo))) + 1e-9)


def main() -> None:
    plan = json.loads((WORK_DIR / "scene_plan.json").read_text(encoding="utf-8"))
    vo_data, sr = sf.read(str(WORK_DIR / "clean_voiceover.wav"), dtype="float64")
    if sr != SAMPLE_RATE:
        raise RuntimeError(f"Expected 48000 Hz clean_voiceover.wav, got {sr}")
    vo_mono = np.mean(vo_data, axis=1) if vo_data.ndim > 1 else vo_data

    n_samples = len(vo_mono)
    vo_stereo = np.column_stack([vo_mono, vo_mono])

    abs_vo = np.abs(vo_mono)
    smooth_env = lowpass(abs_vo, 3.0)
    speech_active = np.clip(smooth_env / (np.percentile(smooth_env, 90) + 1e-6), 0.0, 1.0)
    duck_gain = 0.09 - 0.045 * speech_active

    bgm_stereo = synthesize_documentary_bgm(n_samples, float(plan.get("bpm", 102.0)))
    mix = vo_stereo * 0.92 + bgm_stereo * duck_gain[:, None]

    swell = synthesize_glide_swell() * 0.14
    hud_tick = synthesize_hud_tick() * 0.09

    for sc_idx, sc in enumerate(plan["scenes"]):
        if sc_idx > 0:
            s_idx = max(0, int((float(sc["startSec"]) - 0.5) * SAMPLE_RATE))
            e_idx = min(n_samples, s_idx + len(swell))
            if e_idx > s_idx:
                mix[s_idx:e_idx] += swell[: e_idx - s_idx]

        for b in sc.get("beats", []):
            t_idx = max(0, int(float(b["startSec"]) * SAMPLE_RATE))
            te_idx = min(n_samples, t_idx + len(hud_tick))
            if te_idx > t_idx:
                mix[t_idx:te_idx] += hud_tick[: te_idx - t_idx]

    mix = np.tanh(mix * 0.95)
    master_wav = WORK_DIR / "master_audio.wav"
    master_m4a = WORK_DIR / "master_audio.m4a"
    sf.write(str(master_wav), mix, SAMPLE_RATE, subtype="PCM_16")
    subprocess.run(
        [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-i", str(master_wav),
            "-c:a", "aac", "-b:a", "192k", "-ar", str(SAMPLE_RATE),
            str(master_m4a),
        ],
        check=True,
    )
    master_wav.unlink(missing_ok=True)
    print(f"[mix_audio] Built master_audio.m4a ({n_samples / SAMPLE_RATE:.2f}s).")


if __name__ == "__main__":
    main()
'''

FILES["scripts/plan_chunks.py"] = r'''
import json
import math
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLAN_PATH = ROOT / "work" / "scene_plan.json"


def main() -> None:
    plan = json.loads(PLAN_PATH.read_text(encoding="utf-8"))
    fps = int(plan["fps"])
    total_frames = max(60, int(round(float(plan["totalDurationSec"]) * fps)))

    force = os.environ.get("FORCE_WORKERS", "auto").strip().lower()
    if force in {"1", "4", "6"}:
        workers = int(force)
    else:
        if total_frames <= 2700:
            workers = 1
        elif total_frames <= 9000:
            workers = 4
        else:
            workers = 6

    workers = min(workers, total_frames)
    chunk_size = math.ceil(total_frames / workers)

    chunks = []
    for idx in range(workers):
        start_f = idx * chunk_size
        end_f = min(total_frames - 1, (idx + 1) * chunk_size - 1)
        if start_f <= end_f:
            chunks.append({"idx": idx, "start": start_f, "end": end_f})

    chunks_json = json.dumps(chunks)
    print(f"[plan_chunks] total_frames={total_frames}, workers={len(chunks)}")

    gh_out = os.environ.get("GITHUB_OUTPUT")
    if gh_out:
        with open(gh_out, "a", encoding="utf-8") as f:
            f.write(f"total_frames={total_frames}\n")
            f.write(f"worker_count={len(chunks)}\n")
            f.write(f"chunks_json={chunks_json}\n")


if __name__ == "__main__":
    main()
'''

FILES["scripts/stitch_chunks.py"] = r'''
import os
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHUNKS_DIR = ROOT / "chunks"
WORK_DIR = ROOT / "work"
OUT_DIR = ROOT / "out"


def chunk_index(p: Path) -> int:
    m = re.search(r"chunk_(\d+)\.mp4$", p.name)
    return int(m.group(1)) if m else 999999


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    chunk_files = sorted(CHUNKS_DIR.rglob("chunk_*.mp4"), key=chunk_index)
    if not chunk_files:
        raise FileNotFoundError("No rendered chunk_*.mp4 files found in chunks/.")

    list_file = WORK_DIR / "chunks.txt"
    with open(list_file, "w", encoding="utf-8") as f:
        for cf in chunk_files:
            f.write(f"file '{cf.resolve().as_posix()}'\n")

    video_format = os.environ.get("VIDEO_FORMAT", "long_16_9").strip()
    out_name = "final_short.mp4" if video_format == "short_9_16" else "final_video.mp4"

    master_audio = WORK_DIR / "master_audio.m4a"
    final_mp4 = OUT_DIR / out_name

    print(f"[stitch_chunks] Joining {len(chunk_files)} chunk(s) + master_audio.m4a -> {final_mp4}")
    subprocess.run(
        [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "warning",
            "-f", "concat", "-safe", "0", "-i", str(list_file),
            "-i", str(master_audio),
            "-map", "0:v:0", "-map", "1:a:0",
            "-c:v", "copy", "-c:a", "copy",
            "-movflags", "+faststart",
            "-shortest",
            str(final_mp4),
        ],
        check=True,
    )
    print(f"[stitch_chunks] SUCCESS! Exported {final_mp4} ({final_mp4.stat().st_size / (1024*1024):.1f} MB)")


if __name__ == "__main__":
    main()
'''

FILES["src/types.ts"] = r'''
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
'''

FILES["src/components/StudioKit.tsx"] = r'''
import React, { Component, Suspense, useEffect, useMemo } from "react";
import { useGLTF } from "@react-three/drei";
import { staticFile } from "remotion";
import * as THREE from "three";
import type { V3 } from "../types";

const safeVec = (v?: V3, fallback: V3 = [0, 0, 0]): V3 =>
  Array.isArray(v) && v.length === 3 ? [Number(v[0]) || 0, Number(v[1]) || 0, Number(v[2]) || 0] : fallback;

const safeHex = (c?: string, fallback = "#3B4E6B"): string =>
  typeof c === "string" && c.trim() ? c.trim() : fallback;

const liftStructuralHex = (hex: string): string => {
  try {
    const c = new THREE.Color(hex);
    const lum = 0.299 * c.r + 0.587 * c.g + 0.114 * c.b;
    if (lum < 0.08) {
      c.lerp(new THREE.Color("#364A66"), 0.72);
      return "#" + c.getHexString();
    }
    if (lum < 0.14) {
      c.lerp(new THREE.Color("#425878"), 0.45);
      return "#" + c.getHexString();
    }
    return hex;
  } catch {
    return "#364A66";
  }
};

export const MatteBox: React.FC<{
  pos?: V3;
  rot?: V3;
  size?: V3;
  color?: string;
  emissive?: string;
  emissiveIntensity?: number;
  roughness?: number;
  metalness?: number;
  opacity?: number;
  edges?: boolean;
  edgeColor?: string;
}> = ({
  pos,
  rot,
  size = [1, 1, 1],
  color = "#3B4E6B",
  emissive,
  emissiveIntensity = 1.4,
  roughness = 0.42,
  metalness = 0.32,
  opacity = 1,
  edges = true,
  edgeColor = "#7DD3FC",
}) => {
  const s = safeVec(size, [1, 1, 1]);
  const sx = Math.max(0.01, s[0]);
  const sy = Math.max(0.01, s[1]);
  const sz = Math.max(0.01, s[2]);

  const { geo, edgeGeo } = useMemo(() => {
    const g = new THREE.BoxGeometry(sx, sy, sz);
    const e = new THREE.EdgesGeometry(g, 20);
    return { geo: g, edgeGeo: e };
  }, [sx, sy, sz]);

  useEffect(() => () => {
    geo.dispose();
    edgeGeo.dispose();
  }, [geo, edgeGeo]);

  const finalColor = emissive ? safeHex(color) : liftStructuralHex(safeHex(color));

  return (
    <group position={safeVec(pos)} rotation={safeVec(rot)}>
      <mesh geometry={geo}>
        <meshStandardMaterial
          color={finalColor}
          emissive={emissive ? safeHex(emissive) : "#000000"}
          emissiveIntensity={emissive ? emissiveIntensity : 0}
          roughness={roughness}
          metalness={metalness}
          transparent={opacity < 1}
          opacity={opacity}
        />
      </mesh>
      {edges && !emissive && (
        <lineSegments geometry={edgeGeo}>
          <lineBasicMaterial color={safeHex(edgeColor)} transparent opacity={0.44} />
        </lineSegments>
      )}
    </group>
  );
};

export const MatteCylinder: React.FC<{
  pos?: V3;
  rot?: V3;
  radiusTop?: number;
  radiusBottom?: number;
  height?: number;
  segments?: number;
  openEnded?: boolean;
  thetaStart?: number;
  thetaLength?: number;
  doubleSide?: boolean;
  color?: string;
  emissive?: string;
  emissiveIntensity?: number;
  roughness?: number;
  metalness?: number;
  edges?: boolean;
  edgeColor?: string;
}> = ({
  pos,
  rot,
  radiusTop = 0.5,
  radiusBottom = 0.5,
  height = 1,
  segments = 24,
  openEnded = false,
  thetaStart = 0,
  thetaLength = Math.PI * 2,
  doubleSide = false,
  color = "#475569",
  emissive,
  emissiveIntensity = 1.4,
  roughness = 0.36,
  metalness = 0.4,
  edges = true,
  edgeColor = "#93C5FD",
}) => {
  const { geo, edgeGeo } = useMemo(() => {
    const g = new THREE.CylinderGeometry(
      radiusTop,
      radiusBottom,
      height,
      segments,
      1,
      openEnded,
      thetaStart,
      thetaLength
    );
    const e = new THREE.EdgesGeometry(g, 24);
    return { geo: g, edgeGeo: e };
  }, [radiusTop, radiusBottom, height, segments, openEnded, thetaStart, thetaLength]);

  useEffect(() => () => {
    geo.dispose();
    edgeGeo.dispose();
  }, [geo, edgeGeo]);

  const finalColor = emissive ? safeHex(color) : liftStructuralHex(safeHex(color));

  return (
    <group position={safeVec(pos)} rotation={safeVec(rot)}>
      <mesh geometry={geo}>
        <meshStandardMaterial
          color={finalColor}
          emissive={emissive ? safeHex(emissive) : "#000000"}
          emissiveIntensity={emissive ? emissiveIntensity : 0}
          roughness={roughness}
          metalness={metalness}
          side={doubleSide ? THREE.DoubleSide : THREE.FrontSide}
        />
      </mesh>
      {edges && !emissive && (
        <lineSegments geometry={edgeGeo}>
          <lineBasicMaterial color={safeHex(edgeColor)} transparent opacity={0.44} />
        </lineSegments>
      )}
    </group>
  );
};

export const MatteSphere: React.FC<{
  pos?: V3;
  scale?: V3;
  radius?: number;
  color?: string;
  emissive?: string;
  emissiveIntensity?: number;
  roughness?: number;
  metalness?: number;
}> = ({
  pos,
  scale,
  radius = 0.5,
  color = "#64748B",
  emissive,
  emissiveIntensity = 1.5,
  roughness = 0.35,
  metalness = 0.3,
}) => (
  <mesh position={safeVec(pos)} scale={safeVec(scale, [1, 1, 1])}>
    <sphereGeometry args={[radius, 18, 16]} />
    <meshStandardMaterial
      color={emissive ? safeHex(color) : liftStructuralHex(safeHex(color))}
      emissive={emissive ? safeHex(emissive) : "#000000"}
      emissiveIntensity={emissive ? emissiveIntensity : 0}
      roughness={roughness}
      metalness={metalness}
    />
  </mesh>
);

export const MatteTorus: React.FC<{
  pos?: V3;
  rot?: V3;
  radius?: number;
  tube?: number;
  arc?: number;
  color?: string;
  emissive?: string;
  emissiveIntensity?: number;
}> = ({
  pos,
  rot,
  radius = 1,
  tube = 0.12,
  arc = Math.PI * 2,
  color = "#475569",
  emissive,
  emissiveIntensity = 1.5,
}) => (
  <mesh position={safeVec(pos)} rotation={safeVec(rot)}>
    <torusGeometry args={[radius, tube, 12, 28, arc]} />
    <meshStandardMaterial
      color={emissive ? safeHex(color) : liftStructuralHex(safeHex(color))}
      emissive={emissive ? safeHex(emissive) : "#000000"}
      emissiveIntensity={emissive ? emissiveIntensity : 0}
      roughness={0.35}
      metalness={0.45}
    />
  </mesh>
);

export const MatteCone: React.FC<{
  pos?: V3;
  rot?: V3;
  radius?: number;
  height?: number;
  segments?: number;
  color?: string;
  emissive?: string;
  emissiveIntensity?: number;
  edges?: boolean;
  edgeColor?: string;
}> = ({
  pos,
  rot,
  radius = 0.5,
  height = 1,
  segments = 20,
  color = "#475569",
  emissive,
  emissiveIntensity = 1.4,
  edges = true,
  edgeColor = "#93C5FD",
}) => {
  const { geo, edgeGeo } = useMemo(() => {
    const g = new THREE.ConeGeometry(radius, height, segments);
    const e = new THREE.EdgesGeometry(g, 24);
    return { geo: g, edgeGeo: e };
  }, [radius, height, segments]);

  useEffect(() => () => {
    geo.dispose();
    edgeGeo.dispose();
  }, [geo, edgeGeo]);

  return (
    <group position={safeVec(pos)} rotation={safeVec(rot)}>
      <mesh geometry={geo}>
        <meshStandardMaterial
          color={emissive ? safeHex(color) : liftStructuralHex(safeHex(color))}
          emissive={emissive ? safeHex(emissive) : "#000000"}
          emissiveIntensity={emissive ? emissiveIntensity : 0}
          roughness={0.4}
          metalness={0.35}
        />
      </mesh>
      {edges && !emissive && (
        <lineSegments geometry={edgeGeo}>
          <lineBasicMaterial color={safeHex(edgeColor)} transparent opacity={0.44} />
        </lineSegments>
      )}
    </group>
  );
};

export const GlassShell: React.FC<{
  pos?: V3;
  rot?: V3;
  shape?: "box" | "cylinder";
  size?: V3;
  radius?: number;
  height?: number;
  color?: string;
  edgeColor?: string;
  opacity?: number;
}> = ({
  pos,
  rot,
  shape = "box",
  size = [2, 2, 2],
  radius = 1,
  height = 2,
  color = "#38BDF8",
  edgeColor = "#7DD3FC",
  opacity = 0.22,
}) => {
  const s = safeVec(size, [2, 2, 2]);
  const { geo, edgeGeo } = useMemo(() => {
    const g =
      shape === "cylinder"
        ? new THREE.CylinderGeometry(radius, radius, height, 24)
        : new THREE.BoxGeometry(s[0], s[1], s[2]);
    const e = new THREE.EdgesGeometry(g, 24);
    return { geo: g, edgeGeo: e };
  }, [shape, radius, height, s[0], s[1], s[2]]);

  useEffect(() => () => {
    geo.dispose();
    edgeGeo.dispose();
  }, [geo, edgeGeo]);

  return (
    <group position={safeVec(pos)} rotation={safeVec(rot)}>
      <mesh geometry={geo}>
        <meshStandardMaterial
          color={safeHex(color)}
          transparent
          opacity={opacity}
          roughness={0.15}
          metalness={0.15}
          depthWrite={false}
        />
      </mesh>
      <lineSegments geometry={edgeGeo}>
        <lineBasicMaterial color={safeHex(edgeColor)} transparent opacity={0.7} />
      </lineSegments>
    </group>
  );
};

export const HardwareRack: React.FC<{
  pos?: V3;
  rot?: V3;
  size?: V3;
  bays?: number;
  accentHex?: string;
  frame: number;
}> = ({ pos, rot, size = [1.0, 2.2, 1.0], bays = 6, accentHex = "#22D3EE", frame }) => {
  const [w, h, d] = safeVec(size, [1.0, 2.2, 1.0]);
  const safeBays = Math.max(3, Math.min(10, Math.round(bays)));
  const bayStep = (h * 0.78) / safeBays;

  return (
    <group position={safeVec(pos)} rotation={safeVec(rot)}>
      <MatteBox pos={[0, 0, 0]} size={[w, h, d]} color="#2F4059" edgeColor={accentHex} />
      <MatteBox pos={[0, 0, d * 0.04]} size={[w * 0.86, h * 0.88, d * 0.94]} color="#1E293B" edges={false} />
      {[-w * 0.44, w * 0.44].map((rx, ri) => (
        <MatteBox key={ri} pos={[rx, 0, d * 0.48]} size={[w * 0.08, h * 0.96, 0.05]} color="#64748B" />
      ))}
      {Array.from({ length: safeBays }).map((_, bi) => {
        const by = -h * 0.36 + bi * bayStep;
        const pulse = 0.7 + 0.9 * Math.max(0, Math.sin((frame / 30) * 4.5 - bi * 0.6));
        return (
          <group key={bi} position={[0, by, d * 0.47]}>
            <MatteBox size={[w * 0.78, bayStep * 0.68, 0.08]} color="#475569" edgeColor="#94A3B8" />
            <MatteBox
              pos={[-w * 0.25, 0, 0.05]}
              size={[w * 0.22, bayStep * 0.22, 0.02]}
              color={accentHex}
              emissive={accentHex}
              emissiveIntensity={pulse}
              edges={false}
            />
          </group>
        );
      })}
      <MatteBox pos={[0, h * 0.52, 0]} size={[w * 0.84, 0.08, d * 0.84]} color="#64748B" edgeColor={accentHex} />
    </group>
  );
};

export const DataHallBuilding: React.FC<{
  pos?: V3;
  size?: V3;
  accentHex?: string;
  progress: number;
  frame: number;
}> = ({ pos, size = [3.2, 1.5, 2.2], accentHex = "#22D3EE", progress, frame }) => {
  const [w, h, d] = safeVec(size, [3.2, 1.5, 2.2]);
  const span = 0.45;
  const raw = Math.max(0, Math.min(1, (progress - 0.18) / span));
  const lift = raw * raw * (3 - 2 * raw) * 1.15;

  return (
    <group position={safeVec(pos)}>
      {/* Concrete Slab Base */}
      <MatteBox pos={[0, -h * 0.52, 0]} size={[w * 1.12, 0.16, d * 1.15]} color="#334155" edgeColor={accentHex} />
      {/* 4 Ribbed Concrete Walls (Open Top for Roof Cutaway) */}
      <MatteBox pos={[0, 0, -d * 0.48]} size={[w, h, 0.14]} color="#475569" edgeColor={accentHex} />
      <MatteBox pos={[0, 0, d * 0.48]} size={[w, h, 0.14]} color="#3B4E6B" edgeColor={accentHex} />
      <MatteBox pos={[-w * 0.48, 0, 0]} size={[0.14, h, d]} color="#475569" edgeColor={accentHex} />
      <MatteBox pos={[w * 0.48, 0, 0]} size={[0.14, h, d]} color="#475569" edgeColor={accentHex} />
      {/* Vertical Concrete Pilaster Buttresses */}
      {[-w * 0.3, 0, w * 0.3].map((px, i) => (
        <MatteBox key={i} pos={[px, 0, d * 0.53]} size={[0.18, h * 1.02, 0.1]} color="#64748B" edgeColor={accentHex} />
      ))}
      {/* Glowing Internal Racks Revealed Inside */}
      {[-w * 0.25, 0, w * 0.25].map((rx, ri) => (
        <HardwareRack key={ri} pos={[rx, -0.05, 0]} size={[w * 0.2, h * 0.82, d * 0.65]} bays={4} accentHex={accentHex} frame={frame} />
      ))}
      {/* Lifting Cutaway Roof Slab + Rooftop Chillers */}
      <group position={[0, h * 0.54 + lift, 0]}>
        <MatteBox size={[w * 1.04, 0.14, d * 1.04]} color="#64748B" edgeColor={accentHex} />
        {[-w * 0.28, 0, w * 0.28].map((cx, ci) => (
          <MatteBox key={ci} pos={[cx, 0.16, 0]} size={[0.45, 0.2, d * 0.55]} color="#3B4E6B" edgeColor={accentHex} />
        ))}
      </group>
    </group>
  );
};

export const CitySkylineBlock: React.FC<{
  pos?: V3;
  scale?: number;
  accentHex?: string;
  frame: number;
}> = ({ pos, scale = 1, accentHex = "#F59E0B", frame }) => {
  const towers: { x: number; z: number; w: number; h: number; d: number }[] = [
    { x: -0.9, z: -0.4, w: 0.42, h: 1.5, d: 0.42 },
    { x: -0.35, z: 0.1, w: 0.5, h: 2.2, d: 0.5 },
    { x: 0.25, z: -0.25, w: 0.46, h: 1.85, d: 0.46 },
    { x: 0.85, z: 0.2, w: 0.4, h: 1.3, d: 0.4 },
    { x: -0.55, z: 0.65, w: 0.36, h: 1.1, d: 0.36 },
    { x: 0.45, z: 0.65, w: 0.44, h: 1.6, d: 0.44 },
  ];

  return (
    <group position={safeVec(pos)} scale={[scale, scale, scale]}>
      <MatteBox pos={[0, -0.82, 0]} size={[2.7, 0.14, 2.0]} color="#2F4059" edgeColor={accentHex} />
      {towers.map((t, i) => {
        const flicker = 1.0 + 0.45 * Math.sin((frame / 30) * 3.0 + i * 1.1);
        return (
          <group key={i} position={[t.x, -0.75 + t.h * 0.5, t.z]}>
            <MatteBox size={[t.w, t.h, t.d]} color="#3B4E6B" edgeColor="#7DD3FC" />
            {[0.25, 0, -0.25].map((wy, wi) => (
              <MatteBox
                key={wi}
                pos={[0, wy * t.h, t.d * 0.51]}
                size={[t.w * 0.72, 0.09, 0.02]}
                color={accentHex}
                emissive={accentHex}
                emissiveIntensity={flicker}
                edges={false}
              />
            ))}
          </group>
        );
      })}
    </group>
  );
};

export const PowerPylon: React.FC<{
  pos?: V3;
  height?: number;
  accentHex?: string;
}> = ({ pos, height = 2.4, accentHex = "#F59E0B" }) => (
  <group position={safeVec(pos)}>
    <MatteBox pos={[0, -height * 0.48, 0]} size={[0.9, 0.14, 0.9]} color="#334155" edgeColor={accentHex} />
    <MatteCylinder
      pos={[0, 0, 0]}
      radiusTop={0.14}
      radiusBottom={0.44}
      height={height}
      segments={4}
      color="#64748B"
      edgeColor={accentHex}
    />
    {[height * 0.2, height * 0.38].map((cy, ci) => {
      const span = ci === 0 ? 1.55 : 1.15;
      return (
        <group key={ci} position={[0, cy, 0]}>
          <MatteBox size={[span, 0.08, 0.14]} color="#94A3B8" edgeColor={accentHex} />
          {[-span * 0.45, span * 0.45].map((ix, ii) => (
            <MatteCylinder
              key={ii}
              pos={[ix, -0.14, 0]}
              radiusTop={0.05}
              radiusBottom={0.07}
              height={0.22}
              color={accentHex}
              emissive={accentHex}
              emissiveIntensity={1.6}
              edges={false}
            />
          ))}
        </group>
      );
    })}
  </group>
);

export const CoolingTower: React.FC<{
  pos?: V3;
  radius?: number;
  height?: number;
  accentHex?: string;
  cutaway?: boolean;
  frame: number;
}> = ({ pos, radius = 0.95, height = 2.2, accentHex = "#38BDF8", cutaway = true, frame }) => {
  const segH = height / 3;
  const spin = (frame / 30) * 5.0;

  return (
    <group position={safeVec(pos)}>
      <MatteCylinder pos={[0, -height * 0.48, 0]} radiusTop={radius * 1.15} radiusBottom={radius * 1.18} height={0.14} color="#334155" edgeColor={accentHex} />
      {[
        { y: -segH, rTop: radius * 0.85, rBot: radius * 1.08 },
        { y: 0, rTop: radius * 0.72, rBot: radius * 0.85 },
        { y: segH, rTop: radius * 0.8, rBot: radius * 0.72 },
      ].map((seg, i) => (
        <MatteCylinder
          key={i}
          pos={[0, seg.y, 0]}
          radiusTop={seg.rTop}
          radiusBottom={seg.rBot}
          height={segH + 0.02}
          openEnded={true}
          thetaStart={cutaway ? 0.55 : 0}
          thetaLength={cutaway ? Math.PI * 1.38 : Math.PI * 2}
          doubleSide={true}
          color="#475569"
          edgeColor={accentHex}
        />
      ))}
      <MatteCylinder pos={[0, -height * 0.4, 0]} radiusTop={radius * 0.96} radiusBottom={radius * 0.96} height={0.14} color={accentHex} emissive={accentHex} emissiveIntensity={1.4} edges={false} />
      <group position={[0, -height * 0.12, 0]} rotation={[0, spin, 0]}>
        <MatteBox size={[radius * 1.25, 0.06, 0.16]} color="#CBD5E1" edgeColor={accentHex} />
        <MatteBox size={[0.16, 0.06, radius * 1.25]} color="#CBD5E1" edgeColor={accentHex} />
      </group>
      <RisingParticles origin={[0, height * 0.45, 0]} spread={radius * 0.55} height={1.4} count={8} size={0.16} color="#E2E8F0" speed={0.45} frame={frame} />
    </group>
  );
};

export const BatteryContainer: React.FC<{
  pos?: V3;
  size?: V3;
  accentHex?: string;
  frame: number;
}> = ({ pos, size = [1.5, 1.3, 1.1], accentHex = "#10B981", frame }) => {
  const [w, h, d] = safeVec(size, [1.5, 1.3, 1.1]);
  const charge = 0.35 + 0.65 * (0.5 + 0.5 * Math.sin((frame / 30) * 2.2));
  return (
    <group position={safeVec(pos)}>
      <MatteBox size={[w, h, d]} color="#475569" edgeColor={accentHex} />
      <MatteBox pos={[0, h * 0.55, 0]} size={[w * 0.72, 0.14, d * 0.72]} color="#64748B" edgeColor={accentHex} />
      {[-w * 0.25, 0, w * 0.25].map((vx, i) => (
        <MatteBox key={i} pos={[vx, 0.05, d * 0.51]} size={[w * 0.14, h * 0.65, 0.03]} color="#2B3B52" />
      ))}
      <MatteBox
        pos={[w * 0.38, -h * 0.38 + charge * h * 0.38, d * 0.52]}
        size={[0.14, Math.max(0.14, charge * h * 0.75), 0.04]}
        color={accentHex}
        emissive={accentHex}
        emissiveIntensity={1.9}
        edges={false}
      />
    </group>
  );
};

export const FinnedHousing: React.FC<{
  pos?: V3;
  rot?: V3;
  radius?: number;
  height?: number;
  finCount?: number;
  color?: string;
  accentHex?: string;
  cutaway?: boolean;
  frame: number;
}> = ({
  pos,
  rot,
  radius = 0.9,
  height = 1.8,
  finCount = 8,
  color = "#3B4E6B",
  accentHex = "#22D3EE",
  cutaway = false,
  frame,
}) => {
  const safeFins = Math.max(4, Math.min(12, Math.round(finCount)));
  const pulse = 1.2 + Math.sin((frame / 30) * 3.5) * 0.35;

  return (
    <group position={safeVec(pos)} rotation={safeVec(rot)}>
      <MatteCylinder pos={[0, height * 0.48, 0]} radiusTop={radius * 1.18} radiusBottom={radius * 1.18} height={0.14} color="#64748B" edgeColor={accentHex} />
      <MatteCylinder pos={[0, -height * 0.48, 0]} radiusTop={radius * 1.18} radiusBottom={radius * 1.18} height={0.14} color="#64748B" edgeColor={accentHex} />
      {cutaway ? (
        <>
          <MatteCylinder pos={[0, 0, 0]} radiusTop={radius} radiusBottom={radius} height={height * 0.9} thetaStart={0.5} thetaLength={Math.PI * 1.35} doubleSide={true} color={color} edgeColor={accentHex} />
          <GlassShell pos={[0, 0, 0]} shape="cylinder" radius={radius * 0.96} height={height * 0.88} color={accentHex} edgeColor={accentHex} opacity={0.18} />
        </>
      ) : (
        <MatteCylinder pos={[0, 0, 0]} radiusTop={radius} radiusBottom={radius} height={height * 0.9} color={color} edgeColor={accentHex} />
      )}
      <MatteCylinder pos={[0, 0, 0]} radiusTop={radius * 0.45} radiusBottom={radius * 0.45} height={height * 0.78} color={accentHex} emissive={accentHex} emissiveIntensity={pulse} edges={false} />
      {Array.from({ length: safeFins }).map((_, fi) => {
        const a = (fi / safeFins) * Math.PI * 2;
        if (cutaway && a > 4.6 && a < 6.1) return null;
        return (
          <MatteBox
            key={fi}
            pos={[Math.cos(a) * radius * 1.02, 0, Math.sin(a) * radius * 1.02]}
            rot={[0, -a, 0]}
            size={[0.24, height * 0.82, 0.05]}
            color="#475569"
            edgeColor="#94A3B8"
          />
        );
      })}
    </group>
  );
};

export const PipeConduit: React.FC<{
  points: V3[];
  tubeRadius?: number;
  pipeColor?: string;
  fluidColor?: string;
  flangeCount?: number;
  count?: number;
  speed?: number;
  frame: number;
}> = ({
  points,
  tubeRadius = 0.11,
  pipeColor = "#475569",
  fluidColor = "#22D3EE",
  flangeCount = 4,
  count = 6,
  speed = 0.75,
  frame,
}) => {
  const safePts = useMemo(() => {
    const valid = Array.isArray(points) && points.length >= 2 ? points : [[-2, 0, 0] as V3, [2, 0, 0] as V3];
    return valid.map((p) => {
      const sv = safeVec(p);
      return new THREE.Vector3(sv[0], sv[1], sv[2]);
    });
  }, [points]);

  const curve = useMemo(() => new THREE.CatmullRomCurve3(safePts), [safePts]);

  const flanges = useMemo(() => {
    const fCount = Math.max(2, Math.min(8, Math.round(flangeCount)));
    const up = new THREE.Vector3(0, 1, 0);
    return Array.from({ length: fCount }).map((_, idx) => {
      const u = (idx + 0.5) / fCount;
      const pt = curve.getPoint(u);
      const tangent = curve.getTangent(u).normalize();
      const quat = new THREE.Quaternion().setFromUnitVectors(up, tangent);
      const euler = new THREE.Euler().setFromQuaternion(quat);
      return {
        pos: [pt.x, pt.y, pt.z] as V3,
        rot: [euler.x, euler.y, euler.z] as V3,
      };
    });
  }, [curve, flangeCount]);

  const t = (frame / 30) * speed;
  const safeCount = Math.max(2, Math.min(18, Math.round(count)));

  return (
    <group>
      <mesh>
        <tubeGeometry args={[curve, 40, tubeRadius, 12, false]} />
        <meshStandardMaterial color={safeHex(pipeColor)} transparent opacity={0.34} roughness={0.22} metalness={0.4} depthWrite={false} />
      </mesh>
      <mesh>
        <tubeGeometry args={[curve, 40, tubeRadius * 0.28, 8, false]} />
        <meshStandardMaterial color={safeHex(fluidColor)} emissive={safeHex(fluidColor)} emissiveIntensity={0.65} />
      </mesh>
      {flanges.map((fl, fi) => (
        <MatteCylinder key={fi} pos={fl.pos} rot={fl.rot} radiusTop={tubeRadius * 1.45} radiusBottom={tubeRadius * 1.45} height={0.07} color="#64748B" edgeColor={fluidColor} />
      ))}
      {Array.from({ length: safeCount }).map((_, idx) => {
        const u = ((t + idx / safeCount) % 1 + 1) % 1;
        const pt = curve.getPoint(u);
        return (
          <mesh key={idx} position={[pt.x, pt.y, pt.z]}>
            <sphereGeometry args={[tubeRadius * 0.68, 10, 10]} />
            <meshStandardMaterial color={safeHex(fluidColor)} emissive={safeHex(fluidColor)} emissiveIntensity={2.1} />
          </mesh>
        );
      })}
    </group>
  );
};

export const HeatSinkArray: React.FC<{
  pos?: V3;
  rot?: V3;
  size?: V3;
  finCount?: number;
  color?: string;
  pipeColor?: string;
  glowColor?: string;
}> = ({
  pos,
  rot,
  size = [1.8, 0.7, 1.4],
  finCount = 8,
  color = "#64748B",
  pipeColor = "#D97706",
  glowColor = "#22D3EE",
}) => {
  const [w, h, d] = safeVec(size, [1.8, 0.7, 1.4]);
  const safeFins = Math.max(4, Math.min(14, Math.round(finCount)));
  const step = w / safeFins;

  return (
    <group position={safeVec(pos)} rotation={safeVec(rot)}>
      <MatteBox pos={[0, -h * 0.36, 0]} size={[w, h * 0.24, d]} color={pipeColor} edgeColor="#FBBF24" />
      {Array.from({ length: safeFins }).map((_, fi) => {
        const fx = -w * 0.45 + fi * step;
        return (
          <MatteBox key={fi} pos={[fx, h * 0.08, 0]} size={[step * 0.35, h * 0.72, d * 0.94]} color={color} edgeColor={glowColor} />
        );
      })}
      {[-d * 0.25, d * 0.25].map((pz, pi) => (
        <MatteCylinder key={pi} pos={[0, h * 0.04, pz]} rot={[0, 0, Math.PI / 2]} radiusTop={0.07} radiusBottom={0.07} height={w * 1.12} color={pipeColor} edgeColor="#FDE68A" />
      ))}
    </group>
  );
};

export const SpinGroup: React.FC<{
  pos?: V3;
  rot?: V3;
  axis?: "x" | "y" | "z";
  speed?: number;
  frame: number;
  children?: React.ReactNode;
}> = ({ pos, rot, axis = "y", speed = 1, frame, children }) => {
  const base = safeVec(rot);
  const delta = (frame / 30) * speed;
  const finalRot: V3 = [
    base[0] + (axis === "x" ? delta : 0),
    base[1] + (axis === "y" ? delta : 0),
    base[2] + (axis === "z" ? delta : 0),
  ];
  return (
    <group position={safeVec(pos)} rotation={finalRot}>
      {children}
    </group>
  );
};

export const BobGroup: React.FC<{
  pos?: V3;
  rot?: V3;
  axis?: "x" | "y" | "z";
  amp?: number;
  speed?: number;
  phase?: number;
  frame: number;
  children?: React.ReactNode;
}> = ({ pos, rot, axis = "y", amp = 0.15, speed = 1.5, phase = 0, frame, children }) => {
  const base = safeVec(pos);
  const delta = Math.sin((frame / 30) * speed + phase) * amp;
  const finalPos: V3 = [
    base[0] + (axis === "x" ? delta : 0),
    base[1] + (axis === "y" ? delta : 0),
    base[2] + (axis === "z" ? delta : 0),
  ];
  return (
    <group position={finalPos} rotation={safeVec(rot)}>
      {children}
    </group>
  );
};

export const RevealSlideGroup: React.FC<{
  startPos?: V3;
  endPos?: V3;
  startScale?: number;
  endScale?: number;
  progress: number;
  startAt?: number;
  endAt?: number;
  children?: React.ReactNode;
}> = ({
  startPos = [0, 0, 0],
  endPos = [0, 1.5, 0],
  startScale = 1,
  endScale = 1,
  progress,
  startAt = 0.15,
  endAt = 0.65,
  children,
}) => {
  const span = Math.max(0.01, endAt - startAt);
  const raw = Math.max(0, Math.min(1, (progress - startAt) / span));
  const t = raw * raw * (3 - 2 * raw);
  const s = safeVec(startPos);
  const e = safeVec(endPos, [0, 1.5, 0]);
  const sc = startScale + (endScale - startScale) * t;
  return (
    <group
      position={[s[0] + (e[0] - s[0]) * t, s[1] + (e[1] - s[1]) * t, s[2] + (e[2] - s[2]) * t]}
      scale={[sc, sc, sc]}
    >
      {children}
    </group>
  );
};

export const FlowStream: React.FC<{
  points: V3[];
  tubeRadius?: number;
  tubeColor?: string;
  particleColor?: string;
  particleSize?: number;
  count?: number;
  speed?: number;
  frame: number;
}> = ({
  points,
  tubeRadius = 0.08,
  tubeColor = "#3B4E6B",
  particleColor = "#22D3EE",
  particleSize = 0.09,
  count = 6,
  speed = 0.7,
  frame,
}) => (
  <PipeConduit
    points={points}
    tubeRadius={Math.max(tubeRadius, particleSize * 1.15)}
    pipeColor={tubeColor}
    fluidColor={particleColor}
    flangeCount={3}
    count={count}
    speed={speed}
    frame={frame}
  />
);

export const RisingParticles: React.FC<{
  origin?: V3;
  spread?: number;
  height?: number;
  count?: number;
  size?: number;
  color?: string;
  speed?: number;
  frame: number;
}> = ({
  origin = [0, 0, 0],
  spread = 0.75,
  height = 2.0,
  count = 8,
  size = 0.1,
  color = "#F97316",
  speed = 0.45,
  frame,
}) => {
  const o = safeVec(origin);
  const t = (frame / 30) * speed;
  const safeCount = Math.max(1, Math.min(16, Math.round(count)));

  return (
    <group>
      {Array.from({ length: safeCount }).map((_, i) => {
        const life = ((t + i / safeCount) % 1 + 1) % 1;
        const angle = i * 2.3 + t * 0.8;
        const r = 0.12 + life * spread;
        const s = Math.max(0.25, 1.0 - life * 0.65);
        return (
          <mesh
            key={i}
            position={[o[0] + Math.cos(angle) * r, o[1] + life * height, o[2] + Math.sin(angle) * r]}
            scale={[s, s, s]}
          >
            <sphereGeometry args={[size, 10, 10]} />
            <meshStandardMaterial
              color={safeHex(color)}
              emissive={safeHex(color)}
              emissiveIntensity={1.6 * (1 - life * 0.5)}
            />
          </mesh>
        );
      })}
    </group>
  );
};

export const OrbitRing: React.FC<{
  center?: V3;
  radius?: number;
  count?: number;
  size?: number;
  color?: string;
  speed?: number;
  tilt?: V3;
  frame: number;
}> = ({
  center = [0, 0, 0],
  radius = 1.6,
  count = 8,
  size = 0.09,
  color = "#22D3EE",
  speed = 0.8,
  tilt = [0, 0, 0],
  frame,
}) => {
  const t = (frame / 30) * speed;
  const safeCount = Math.max(1, Math.min(18, Math.round(count)));
  return (
    <group position={safeVec(center)} rotation={safeVec(tilt)}>
      <MatteTorus pos={[0, 0, 0]} rot={[Math.PI / 2, 0, 0]} radius={radius} tube={0.03} color="#475569" />
      {Array.from({ length: safeCount }).map((_, i) => {
        const a = t + (i / safeCount) * Math.PI * 2;
        return (
          <mesh key={i} position={[Math.cos(a) * radius, 0, Math.sin(a) * radius]}>
            <sphereGeometry args={[size, 10, 10]} />
            <meshStandardMaterial color={safeHex(color)} emissive={safeHex(color)} emissiveIntensity={1.9} />
          </mesh>
        );
      })}
    </group>
  );
};

class GlbErrorBoundary extends Component<{ children: React.ReactNode }, { err: boolean }> {
  constructor(props: { children: React.ReactNode }) {
    super(props);
    this.state = { err: false };
  }
  static getDerivedStateFromError() {
    return { err: true };
  }
  render() {
    return this.state.err ? null : this.props.children;
  }
}

const GlbInner: React.FC<{ file: string; pos?: V3; rot?: V3; scale?: number; spinSpeed?: number; frame: number }> = ({
  file,
  pos,
  rot,
  scale = 1,
  spinSpeed = 0.35,
  frame,
}) => {
  const { scene } = useGLTF(staticFile(`models/${file}`));
  const cloned = useMemo(() => scene.clone(), [scene]);
  const r = safeVec(rot);
  return (
    <group position={safeVec(pos)} rotation={[r[0], r[1] + (frame / 30) * spinSpeed, r[2]]} scale={[scale, scale, scale]}>
      <primitive object={cloned} />
    </group>
  );
};

export const GlbModel: React.FC<{
  file: string;
  pos?: V3;
  rot?: V3;
  scale?: number;
  spinSpeed?: number;
  frame: number;
}> = (props) => (
  <GlbErrorBoundary>
    <Suspense fallback={null}>
      <GlbInner {...props} />
    </Suspense>
  </GlbErrorBoundary>
);
'''

FILES["src/components/Continuous3DWorld.tsx"] = r'''
import React, { useLayoutEffect, useMemo } from "react";
import { ThreeCanvas } from "@remotion/three";
import { useThree } from "@react-three/fiber";
import { interpolateColors, useCurrentFrame, useVideoConfig } from "remotion";
import { SCENE_REGISTRY } from "../generated/SceneRegistry";
import type { DocumentaryPlan, DocumentaryScene } from "../types";

function smoothstep(edge0: number, edge1: number, x: number): number {
  const t = Math.max(0, Math.min(1, (x - edge0) / Math.max(1e-6, edge1 - edge0)));
  return t * t * (3 - 2 * t);
}

function lerp(a: number, b: number, t: number): number {
  return a + (b - a) * t;
}

function sampleSceneCamera(
  scene: DocumentaryScene,
  tSec: number,
  frame: number,
  isVertical: boolean
): { pos: [number, number, number]; look: [number, number, number] } {
  const beats = scene.beats;
  if (!beats || beats.length === 0) {
    return {
      pos: [scene.worldPos[0] + 3.8, scene.worldPos[1] + 2.0, scene.worldPos[2] + 4.3],
      look: [scene.worldPos[0], scene.worldPos[1] + 0.3, scene.worldPos[2]],
    };
  }

  let bIdx = beats.findIndex((b) => tSec >= b.startSec && tSec <= b.endSec);
  if (bIdx === -1) bIdx = beats.length - 1;

  const currBeat = beats[bIdx];
  const nextBeat = beats[Math.min(beats.length - 1, bIdx + 1)];
  const bDur = Math.max(0.1, currBeat.endSec - currBeat.startSec);
  const localU = Math.max(0, Math.min(1, (tSec - currBeat.startSec) / bDur));
  const glideU = smoothstep(0.15, 0.95, localU);

  const driftX = Math.sin(frame * 0.02) * 0.11;
  const driftY = Math.cos(frame * 0.016) * 0.07;
  const pull = isVertical ? 1.15 : 1.0;

  return {
    pos: [
      scene.worldPos[0] + lerp(currBeat.cameraOffset[0], nextBeat.cameraOffset[0], glideU) * pull + driftX,
      scene.worldPos[1] + lerp(currBeat.cameraOffset[1], nextBeat.cameraOffset[1], glideU) + driftY,
      scene.worldPos[2] + lerp(currBeat.cameraOffset[2], nextBeat.cameraOffset[2], glideU) * pull,
    ],
    look: [
      scene.worldPos[0] + lerp(currBeat.lookOffset[0], nextBeat.lookOffset[0], glideU),
      scene.worldPos[1] + lerp(currBeat.lookOffset[1], nextBeat.lookOffset[1], glideU),
      scene.worldPos[2] + lerp(currBeat.lookOffset[2], nextBeat.lookOffset[2], glideU),
    ],
  };
}

interface CameraState {
  camPos: [number, number, number];
  lookAt: [number, number, number];
  bgHex: string;
  accentHex: string;
}

function computeContinuousCamera(
  plan: DocumentaryPlan,
  tSec: number,
  frame: number,
  isVertical: boolean
): CameraState {
  const scenes = plan.scenes;
  if (scenes.length === 0) {
    return { camPos: [0, 2, 5], lookAt: [0, 0.25, 0], bgHex: "#101B2E", accentHex: "#22D3EE" };
  }

  let activeIdx = scenes.findIndex((s) => tSec >= s.startSec && tSec <= s.endSec);
  if (activeIdx === -1) activeIdx = scenes.length - 1;

  const current = scenes[activeIdx];
  const currSample = sampleSceneCamera(current, tSec, frame, isVertical);
  const halfWin = isVertical ? 0.75 : 0.9;

  if (activeIdx < scenes.length - 1) {
    const distToEnd = current.endSec - tSec;
    if (distToEnd <= halfWin) {
      const next = scenes[activeIdx + 1];
      const nextSample = sampleSceneCamera(next, tSec, frame, isVertical);
      const blend = smoothstep(0, 1, (halfWin - distToEnd) / (halfWin * 2));
      return {
        camPos: [
          lerp(currSample.pos[0], nextSample.pos[0], blend),
          lerp(currSample.pos[1], nextSample.pos[1], blend),
          lerp(currSample.pos[2], nextSample.pos[2], blend),
        ],
        lookAt: [
          lerp(currSample.look[0], nextSample.look[0], blend),
          lerp(currSample.look[1], nextSample.look[1], blend),
          lerp(currSample.look[2], nextSample.look[2], blend),
        ],
        bgHex: interpolateColors(blend, [0, 1], [current.bgHex, next.bgHex]),
        accentHex: interpolateColors(blend, [0, 1], [current.accentHex, next.accentHex]),
      };
    }
  }

  if (activeIdx > 0) {
    const distFromStart = tSec - current.startSec;
    if (distFromStart < halfWin) {
      const prev = scenes[activeIdx - 1];
      const prevSample = sampleSceneCamera(prev, tSec, frame, isVertical);
      const blend = smoothstep(0, 1, 0.5 + distFromStart / (halfWin * 2));
      return {
        camPos: [
          lerp(prevSample.pos[0], currSample.pos[0], blend),
          lerp(prevSample.pos[1], currSample.pos[1], blend),
          lerp(prevSample.pos[2], currSample.pos[2], blend),
        ],
        lookAt: [
          lerp(prevSample.look[0], currSample.look[0], blend),
          lerp(prevSample.look[1], currSample.look[1], blend),
          lerp(prevSample.look[2], currSample.look[2], blend),
        ],
        bgHex: interpolateColors(blend, [0, 1], [prev.bgHex, current.bgHex]),
        accentHex: interpolateColors(blend, [0, 1], [prev.accentHex, current.accentHex]),
      };
    }
  }

  return {
    camPos: currSample.pos,
    lookAt: currSample.look,
    bgHex: current.bgHex,
    accentHex: current.accentHex,
  };
}

const CameraController: React.FC<{ camPos: [number, number, number]; lookAt: [number, number, number] }> = ({
  camPos,
  lookAt,
}) => {
  const camera = useThree((state) => state.camera);
  camera.position.set(camPos[0], camPos[1], camPos[2]);
  camera.lookAt(lookAt[0], lookAt[1], lookAt[2]);
  camera.updateMatrixWorld();

  useLayoutEffect(() => {
    camera.position.set(camPos[0], camPos[1], camPos[2]);
    camera.lookAt(lookAt[0], lookAt[1], lookAt[2]);
    camera.updateMatrixWorld();
  }, [camera, camPos, lookAt]);

  return null;
};

export const Continuous3DWorld: React.FC<{ plan: DocumentaryPlan }> = ({ plan }) => {
  const frame = useCurrentFrame();
  const { width, height, fps } = useVideoConfig();
  const tSec = frame / fps;
  const isVertical = height > width;

  const camState = computeContinuousCamera(plan, tSec, frame, isVertical);
  const visibleScenes = plan.scenes.filter(
    (s) => tSec >= s.startSec - 2.2 && tSec <= s.endSec + 2.2
  );

  // World-locked blueprint grid snapping every 1.0 unit so floor lines never slide during camera flight
  const gridX = Math.round(camState.lookAt[0]);
  const gridY = Math.round(camState.lookAt[1] - 1.35);
  const gridZ = Math.round(camState.lookAt[2]);

  return (
    <ThreeCanvas
      width={width}
      height={height}
      camera={{ fov: isVertical ? 50 : 38, near: 0.1, far: 45, position: camState.camPos }}
      gl={{ antialias: true, powerPreference: "high-performance" }}
    >
      <color attach="background" args={[camState.bgHex]} />
      <fog attach="fog" args={[camState.bgHex, 9.0, 20.5]} />

      <CameraController camPos={camState.camPos} lookAt={camState.lookAt} />

      {/* Grounded Technical CAD Blueprint Floor Grid */}
      <gridHelper args={[56, 56, "#1E4B68", "#1C2D46"]} position={[gridX, gridY, gridZ]} />

      {/* 3-Point Studio + Hemisphere Lighting */}
      <hemisphereLight args={["#E2E8F0", "#263750", 1.25]} />
      <directionalLight
        position={[camState.camPos[0] + 8, camState.camPos[1] + 12, camState.camPos[2] + 7]}
        intensity={2.2}
        color="#FFFFFF"
      />
      <directionalLight
        position={[camState.camPos[0] - 9, camState.camPos[1] + 5, camState.camPos[2] - 8]}
        intensity={1.5}
        color="#7DD3FC"
      />
      <pointLight
        position={[camState.lookAt[0] - 3.5, camState.lookAt[1] + 3, camState.lookAt[2] + 3]}
        intensity={1.7}
        color={camState.accentHex}
      />

      {visibleScenes.map((scene) => {
        const Comp = SCENE_REGISTRY[scene.id];
        if (!Comp) return null;
        const dur = Math.max(0.1, scene.endSec - scene.startSec);
        const progress = Math.max(0, Math.min(1, (tSec - scene.startSec) / dur));
        const localFrame = Math.max(0, frame - Math.round(scene.startSec * fps));
        return (
          <group key={scene.id} position={scene.worldPos}>
            <Comp
              frame={frame}
              localFrame={localFrame}
              progress={progress}
              accentHex={scene.accentHex}
            />
          </group>
        );
      })}
    </ThreeCanvas>
  );
};
'''

FILES["src/components/HudOverlay.tsx"] = r'''
import React from "react";
import { loadFont as loadSpaceGrotesk } from "@remotion/google-fonts/SpaceGrotesk";
import { loadFont as loadJetBrainsMono } from "@remotion/google-fonts/JetBrainsMono";
import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import type { DocumentaryPlan, HudCallout, StatCounter, SubtitleChunk } from "../types";

const { fontFamily: DISPLAY_FONT } = loadSpaceGrotesk("normal", {
  weights: ["700"],
  subsets: ["latin"],
});

const { fontFamily: MONO_FONT } = loadJetBrainsMono("normal", {
  weights: ["600", "700"],
  subsets: ["latin"],
});

function formatCounterValue(val: number, decimals = 0, prefix = "", suffix = ""): string {
  const fixed = decimals > 0 ? Number(val.toFixed(decimals)) : Math.round(val);
  const formatted = fixed.toLocaleString("en-US", {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
  return `${prefix}${formatted}${suffix}`;
}

const CalloutLayer: React.FC<{
  callouts: HudCallout[];
  accentHex: string;
  localBeatFrame: number;
  beatDurFrames: number;
  isFirstBeat: boolean;
  fps: number;
  width: number;
  height: number;
}> = ({ callouts, accentHex, localBeatFrame, beatDurFrames, isFirstBeat, fps, width, height }) => {
  const enter = spring({
    frame: localBeatFrame + (isFirstBeat ? 10 : 0),
    fps,
    config: { damping: 18, stiffness: 170, mass: 0.8 },
  });
  const exitOpacity = interpolate(
    localBeatFrame,
    [Math.max(0, beatDurFrames - 10), beatDurFrames],
    [1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  return (
    <AbsoluteFill style={{ pointerEvents: "none", opacity: exitOpacity }}>
      <svg width={width} height={height} style={{ position: "absolute", inset: 0 }}>
        {callouts.map((c, idx) => {
          const ax = (c.anchorPct[0] / 100) * width;
          const ay = (c.anchorPct[1] / 100) * height;
          const bx = (c.boxPct[0] / 100) * width;
          const by = (c.boxPct[1] / 100) * height;
          const ex = bx + (ax - bx) * 0.45;
          const ey = by;
          const pathLen = Math.hypot(ex - bx, ey - by) + Math.hypot(ax - ex, ay - ey);
          const dashOffset = pathLen * (1 - enter);

          return (
            <g key={idx}>
              <path
                d={`M ${bx} ${by} L ${ex} ${ey} L ${ax} ${ay}`}
                fill="none"
                stroke={accentHex}
                strokeWidth={2.5}
                strokeDasharray={pathLen}
                strokeDashoffset={dashOffset}
                strokeLinecap="round"
              />
              <circle cx={ax} cy={ay} r={6 * enter} fill={accentHex} />
              <circle cx={ax} cy={ay} r={14 * enter} fill="none" stroke={accentHex} strokeWidth={1.5} opacity={0.55} />
            </g>
          );
        })}
      </svg>

      {callouts.map((c, idx) => {
        const bx = (c.boxPct[0] / 100) * width;
        const by = (c.boxPct[1] / 100) * height;
        const alignRight = c.boxPct[0] > 55;
        return (
          <div
            key={idx}
            style={{
              position: "absolute",
              left: alignRight ? undefined : bx,
              right: alignRight ? width - bx : undefined,
              top: by - 22,
              transform: `scale(${0.9 + 0.1 * enter})`,
              opacity: enter,
              padding: "9px 18px",
              borderRadius: 8,
              backgroundColor: "rgba(15, 23, 42, 0.90)",
              border: `1.5px solid ${accentHex}`,
              boxShadow: "0 10px 26px rgba(0, 0, 0, 0.5)",
              fontFamily: MONO_FONT,
              fontSize: width < height ? 21 : 22,
              fontWeight: 700,
              letterSpacing: "0.06em",
              color: "#F8FAFC",
              whiteSpace: "nowrap",
            }}
          >
            {c.label}
          </div>
        );
      })}
    </AbsoluteFill>
  );
};

const StatCounterCard: React.FC<{
  stat: StatCounter;
  accentHex: string;
  frame: number;
  triggerFrame: number;
  beatEndFrame: number;
  isFirstBeat: boolean;
  fps: number;
  isVertical: boolean;
}> = ({ stat, accentHex, frame, triggerFrame, beatEndFrame, isFirstBeat, fps, isVertical }) => {
  const animFrame = Math.max(0, frame - triggerFrame + (isFirstBeat ? 4 : 0));
  const progress = spring({
    frame: animFrame,
    fps,
    config: { damping: 20, stiffness: 120, mass: 0.9 },
  });
  const fadeOut = interpolate(frame, [Math.max(0, beatEndFrame - 10), beatEndFrame], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const opacity = (isFirstBeat ? 1 : Math.min(1, animFrame / 4)) * fadeOut;

  const currentVal = stat.fromVal + (stat.toVal - stat.fromVal) * progress;
  const formatted = formatCounterValue(currentVal, stat.decimals ?? 0, stat.prefix ?? "", stat.suffix ?? "");

  return (
    <div
      style={{
        position: "absolute",
        left: isVertical ? 48 : 64,
        top: isVertical ? 96 : 52,
        opacity,
        transform: `translateY(${isFirstBeat ? 0 : (1 - progress) * 18}px)`,
        padding: "16px 28px",
        borderRadius: 14,
        backgroundColor: "rgba(15, 23, 42, 0.90)",
        border: `1.5px solid ${accentHex}`,
        boxShadow: "0 18px 42px rgba(0, 0, 0, 0.6)",
      }}
    >
      <div
        style={{
          fontFamily: MONO_FONT,
          fontSize: isVertical ? 18 : 17,
          fontWeight: 700,
          letterSpacing: "0.1em",
          color: "#CBD5E1",
          marginBottom: 6,
        }}
      >
        {stat.label}
      </div>
      <div
        style={{
          fontFamily: MONO_FONT,
          fontSize: isVertical ? 54 : 60,
          fontWeight: 700,
          fontVariantNumeric: "tabular-nums",
          lineHeight: 1.0,
          color: accentHex,
        }}
      >
        {formatted}
      </div>
    </div>
  );
};

const SubtitleBanner: React.FC<{
  chunk: SubtitleChunk;
  accentHex: string;
  isVertical: boolean;
}> = ({ chunk, accentHex, isVertical }) => (
  <div
    style={{
      position: "absolute",
      left: "50%",
      bottom: isVertical ? 200 : 78,
      transform: "translateX(-50%)",
      maxWidth: isVertical ? "88%" : "76%",
      padding: "12px 28px",
      borderRadius: 14,
      backgroundColor: "rgba(10, 16, 30, 0.84)",
      border: `1.5px solid ${accentHex}55`,
      boxShadow: "0 12px 30px rgba(0, 0, 0, 0.55)",
      textAlign: "center",
      lineHeight: 1.24,
    }}
  >
    <span
      style={{
        fontFamily: DISPLAY_FONT,
        fontSize: isVertical ? 44 : 48,
        fontWeight: 700,
        letterSpacing: "-0.015em",
      }}
    >
      {chunk.words.map((w, wi) => (
        <span
          key={wi}
          style={{
            color: w.highlight ? accentHex : "#F8FAFC",
            marginRight: wi === chunk.words.length - 1 ? 0 : 12,
            textShadow: "0 3px 14px rgba(0,0,0,0.9)",
          }}
        >
          {w.text}
        </span>
      ))}
    </span>
  </div>
);

export const HudOverlay: React.FC<{ plan: DocumentaryPlan }> = ({ plan }) => {
  const frame = useCurrentFrame();
  const { width, height, fps } = useVideoConfig();
  const tSec = frame / fps;
  const isVertical = height > width;

  const activeSceneIdx = plan.scenes.findIndex((s) => tSec >= s.startSec && tSec <= s.endSec);
  const resolvedSceneIdx = activeSceneIdx === -1 ? plan.scenes.length - 1 : activeSceneIdx;
  const activeScene = plan.scenes[resolvedSceneIdx];

  const activeBeatIdx = activeScene?.beats.findIndex((b) => tSec >= b.startSec && tSec <= b.endSec) ?? -1;
  const resolvedBeatIdx = activeBeatIdx === -1 ? Math.max(0, (activeScene?.beats.length ?? 1) - 1) : activeBeatIdx;
  const activeBeat = activeScene?.beats[resolvedBeatIdx];

  const activeSubtitle = plan.subtitleChunks.find((c) => tSec >= c.startSec && tSec <= c.endSec);

  if (!activeScene || !activeBeat) return null;

  const isFirstBeat = resolvedSceneIdx === 0 && resolvedBeatIdx === 0;
  const beatStartFrame = Math.round(activeBeat.startSec * fps);
  const beatEndFrame = Math.round(activeBeat.endSec * fps);
  const localBeatFrame = Math.max(0, frame - beatStartFrame);
  const beatDurFrames = Math.max(15, beatEndFrame - beatStartFrame);

  const rawTrigFrame = Math.round(activeBeat.triggerSec * fps);
  const triggerFrame = isFirstBeat
    ? 0
    : Math.min(rawTrigFrame, beatStartFrame + Math.round(beatDurFrames * 0.35));

  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      {activeBeat.callouts?.length > 0 && (
        <CalloutLayer
          callouts={activeBeat.callouts}
          accentHex={activeScene.accentHex}
          localBeatFrame={localBeatFrame}
          beatDurFrames={beatDurFrames}
          isFirstBeat={isFirstBeat}
          fps={fps}
          width={width}
          height={height}
        />
      )}

      {activeBeat.statCounter && (
        <StatCounterCard
          stat={activeBeat.statCounter}
          accentHex={activeScene.accentHex}
          frame={frame}
          triggerFrame={triggerFrame}
          beatEndFrame={beatEndFrame}
          isFirstBeat={isFirstBeat}
          fps={fps}
          isVertical={isVertical}
        />
      )}

      {activeSubtitle && (
        <SubtitleBanner chunk={activeSubtitle} accentHex={activeScene.accentHex} isVertical={isVertical} />
      )}
    </AbsoluteFill>
  );
};
'''

FILES["src/generated/scenes/Scene_01.tsx"] = r'''
import React from "react";
import {
  DataHallBuilding,
  CitySkylineBlock,
  PowerPylon,
  PipeConduit,
} from "../../components/StudioKit";
import type { DynamicSceneProps } from "../../types";

export const Scene_01: React.FC<DynamicSceneProps> = ({ frame, progress, accentHex }) => {
  return (
    <group>
      <DataHallBuilding pos={[-0.9, -0.2, 0]} size={[3.0, 1.5, 2.2]} accentHex={accentHex} progress={progress} frame={frame} />
      <PowerPylon pos={[0.95, 0.0, -0.6]} height={2.3} accentHex="#F59E0B" />
      <CitySkylineBlock pos={[2.1, -0.25, 0.4]} scale={0.85} accentHex="#F59E0B" frame={frame} />
      <PipeConduit
        points={[[-0.9, -0.8, 0.9], [0.95, 0.4, -0.6], [2.1, -0.6, 0.4]]}
        fluidColor={accentHex}
        flangeCount={3}
        speed={0.85}
        frame={frame}
      />
    </group>
  );
};
'''

FILES["src/generated/SceneRegistry.ts"] = r'''
import type React from "react";
import type { DynamicSceneProps } from "../types";
import { Scene_01 } from "./scenes/Scene_01";

export const SCENE_REGISTRY: Record<string, React.FC<DynamicSceneProps>> = {
  scene_01: Scene_01,
};
'''

FILES["src/generated/ScenesData.ts"] = r'''
import type { DocumentaryPlan } from "../types";

export const SCENE_PLAN: DocumentaryPlan = {
  channel: "InfraVerse",
  fps: 30,
  width: 1920,
  height: 1080,
  totalDurationSec: 8,
  hasAudio: false,
  bpm: 102,
  emphasisPeaksSec: [0.2, 4.5],
  subtitleChunks: [],
  scenes: [
    {
      id: "scene_01",
      componentName: "Scene_01",
      visualConcept: "Data Hall Campus & City Grid",
      visualSpec: "DataHallBuilding + PowerPylon + CitySkylineBlock",
      startSec: 0,
      endSec: 8,
      worldPos: [0, 0, 0],
      bgHex: "#101B2E",
      accentHex: "#22D3EE",
      beats: [
        {
          id: "b_01_01",
          startSec: 0,
          endSec: 4,
          triggerSec: 0.0,
          cameraOffset: [3.8, 2.0, 4.3],
          lookOffset: [0, 0.3, 0],
          callouts: [{ label: "1,000 MW DATA HALL", anchorPct: [44, 52], boxPct: [74, 24] }],
          statCounter: { label: "TOTAL CAMPUS CAPEX", fromVal: 0, toVal: 100, prefix: "$", suffix: "B", decimals: 0 },
        },
        {
          id: "b_01_02",
          startSec: 4,
          endSec: 8,
          triggerSec: 4.2,
          cameraOffset: [1.5, 1.3, 3.0],
          lookOffset: [0.15, 0.25, 0],
          callouts: [{ label: "CITY POWER DRAW", anchorPct: [60, 56], boxPct: [22, 34] }],
          statCounter: null,
        },
      ],
    },
  ],
};
'''

FILES["src/generated/GeneratedTimeline.tsx"] = r'''
import React from "react";
import { AbsoluteFill } from "remotion";
import { Continuous3DWorld } from "../components/Continuous3DWorld";
import { HudOverlay } from "../components/HudOverlay";
import { SCENE_PLAN } from "./ScenesData";

export const GENERATED_TOTAL_FRAMES = 240;

export const GeneratedTimeline: React.FC = () => {
  return (
    <AbsoluteFill>
      <Continuous3DWorld plan={SCENE_PLAN} />
      <HudOverlay plan={SCENE_PLAN} />
    </AbsoluteFill>
  );
};
'''

FILES["src/Main.tsx"] = r'''
import React from "react";
import { AbsoluteFill } from "remotion";
import { GeneratedTimeline } from "./generated/GeneratedTimeline";

export const Main: React.FC = () => {
  return (
    <AbsoluteFill style={{ backgroundColor: "#101B2E" }}>
      <GeneratedTimeline />
    </AbsoluteFill>
  );
};
'''

FILES["src/Root.tsx"] = r'''
import React from "react";
import { Composition } from "remotion";
import { Main } from "./Main";
import { GENERATED_TOTAL_FRAMES } from "./generated/GeneratedTimeline";
import { SCENE_PLAN } from "./generated/ScenesData";

export const RemotionRoot: React.FC = () => {
  const totalFrames = Math.max(
    60,
    GENERATED_TOTAL_FRAMES || Math.round(SCENE_PLAN.totalDurationSec * SCENE_PLAN.fps)
  );

  return (
    <Composition
      id="Main"
      component={Main}
      durationInFrames={totalFrames}
      fps={SCENE_PLAN.fps || 30}
      width={SCENE_PLAN.width || 1920}
      height={SCENE_PLAN.height || 1080}
    />
  );
};
'''

FILES["src/index.ts"] = r'''
import { registerRoot } from "remotion";
import { RemotionRoot } from "./Root";

registerRoot(RemotionRoot);
'''

FILES[".github/workflows/render_video.yml"] = r'''
name: Long Video Factory (16:9)

on:
  push:
    paths:
      - "input/**"
  workflow_dispatch:
    inputs:
      preview_seconds:
        description: "0 = Full video, or 20 / 45 for quick test preview"
        required: false
        default: "0"
        type: choice
        options:
          - "0"
          - "20"
          - "45"
      quality_preset:
        description: "1080p_30fps (YouTube HD) or 720p_24fps (Fast Draft)"
        required: false
        default: "1080p_30fps"
        type: choice
        options:
          - "1080p_30fps"
          - "720p_24fps"
      force_workers:
        description: "Parallel workers (auto = 1 for <90s, 4 for 2-5m, 6 for 6m+)"
        required: false
        default: "auto"
        type: choice
        options:
          - "auto"
          - "1"
          - "4"
          - "6"
      trim_silence:
        description: "Trim long pauses (>0.65s) in voiceover?"
        required: false
        default: "false"
        type: choice
        options:
          - "false"
          - "true"
      whisper_model:
        description: "Whisper speech model size"
        required: false
        default: "small"
        type: choice
        options:
          - "tiny"
          - "base"
          - "small"

jobs:
  plan_and_prepare:
    runs-on: ubuntu-latest
    timeout-minutes: 25
    outputs:
      has_input: ${{ steps.check_input.outputs.has_input }}
      chunks_json: ${{ steps.chunk_plan.outputs.chunks_json }}

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Check for uploaded audio inside input/
        id: check_input
        run: |
          shopt -s nullglob nocaseglob
          files=(input/*.mp3 input/*.wav input/*.m4a input/*.aac input/*.flac input/*.ogg input/*.mp4 input/*.mov input/*.mkv input/*.webm)
          if [ ${#files[@]} -eq 0 ]; then
            echo "has_input=false" >> $GITHUB_OUTPUT
          else
            echo "has_input=true" >> $GITHUB_OUTPUT
            echo "Found 16:9 media input: ${files[*]}"
          fi

      - name: Set up Python 3.11
        if: steps.check_input.outputs.has_input == 'true'
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          cache: "pip"

      - name: Set up Node.js 22
        if: steps.check_input.outputs.has_input == 'true'
        uses: actions/setup-node@v4
        with:
          node-version: "22"

      - name: Install FFmpeg & Headless Chrome libraries
        if: steps.check_input.outputs.has_input == 'true'
        run: |
          sudo apt-get update
          sudo apt-get install -y \
            ffmpeg \
            libnss3 libdbus-1-3 libatk1.0-0 libgbm1 libxrandr2 \
            libxkbcommon0 libxfixes3 libxcomposite1 libxdamage1 \
            libatk-bridge2.0-0 libpango-1.0-0 libcairo2 libcups2 \
            libasound2t64 || sudo apt-get install -y libasound2

      - name: Install Python dependencies
        if: steps.check_input.outputs.has_input == 'true'
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      - name: Install Node dependencies & Remotion Headless Chrome
        if: steps.check_input.outputs.has_input == 'true'
        run: |
          npm install --no-audit --no-fund
          npx remotion browser ensure

      - name: Step 1 - Audio Clean & Word-Level Whisper Timestamps
        if: steps.check_input.outputs.has_input == 'true'
        env:
          INPUT_FOLDER: "input"
          TRIM_SILENCE: ${{ github.event.inputs.trim_silence || 'false' }}
          WHISPER_MODEL: ${{ github.event.inputs.whisper_model || 'small' }}
          PREVIEW_SECONDS: ${{ github.event.inputs.preview_seconds || '0' }}
        run: |
          python scripts/analyze_audio.py

      - name: Step 2 - Gemini Multi-Part 3D & HUD Scene Coder
        if: steps.check_input.outputs.has_input == 'true'
        env:
          INPUT_FOLDER: "input"
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
          QUALITY_PRESET: ${{ github.event.inputs.quality_preset || '1080p_30fps' }}
          VIDEO_FORMAT: "long_16_9"
        run: |
          python scripts/generate_scenes.py

      - name: Step 3 - Validate Uniqueness, Beats & Zero Overlaps
        if: steps.check_input.outputs.has_input == 'true'
        run: |
          python scripts/validate_scenes.py

      - name: Step 4 - Synthesize & Duck Master Documentary Audio
        if: steps.check_input.outputs.has_input == 'true'
        run: |
          python scripts/mix_audio.py

      - name: Step 5 - Frame 0 Smoke Test & Bundle Project Once
        if: steps.check_input.outputs.has_input == 'true'
        run: |
          npx remotion still src/index.ts Main work/frame0_smoke.png --frame=0 --gl=swangle
          npx remotion bundle src/index.ts --public-dir public --out-dir build_bundle

      - name: Step 6 - Plan Adaptive Parallel Workers (1 / 4 / 6)
        id: chunk_plan
        if: steps.check_input.outputs.has_input == 'true'
        env:
          FORCE_WORKERS: ${{ github.event.inputs.force_workers || 'auto' }}
        run: |
          python scripts/plan_chunks.py

      - name: Upload Prepared Bundle & Master Audio
        if: steps.check_input.outputs.has_input == 'true'
        uses: actions/upload-artifact@v4
        with:
          name: prepared-long
          path: |
            build_bundle/
            work/master_audio.m4a
            work/scene_plan.json
            work/transcript.json
            work/frame0_smoke.png
          retention-days: 2

  render_workers:
    needs: plan_and_prepare
    if: needs.plan_and_prepare.outputs.has_input == 'true'
    runs-on: ubuntu-latest
    timeout-minutes: 90
    strategy:
      fail-fast: false
      matrix:
        chunk: ${{ fromJson(needs.plan_and_prepare.outputs.chunks_json) }}

    steps:
      - name: Checkout repository config
        uses: actions/checkout@v4

      - name: Download Prepared Remotion Bundle
        uses: actions/download-artifact@v4
        with:
          name: prepared-long

      - name: Set up Node.js 22
        uses: actions/setup-node@v4
        with:
          node-version: "22"

      - name: Install Headless Chrome OS libraries
        run: |
          sudo apt-get update
          sudo apt-get install -y \
            ffmpeg \
            libnss3 libdbus-1-3 libatk1.0-0 libgbm1 libxrandr2 \
            libxkbcommon0 libxfixes3 libxcomposite1 libxdamage1 \
            libatk-bridge2.0-0 libpango-1.0-0 libcairo2 libcups2 \
            libasound2t64 || sudo apt-get install -y libasound2

      - name: Install Node packages & Remotion Chrome
        run: |
          npm install --no-audit --no-fund
          npx remotion browser ensure

      - name: Render Silent 3D + HUD Chunk ${{ matrix.chunk.idx }}
        run: |
          mkdir -p out
          npx remotion render build_bundle Main out/chunk_${{ matrix.chunk.idx }}.mp4 \
            --frames=${{ matrix.chunk.start }}-${{ matrix.chunk.end }} \
            --muted \
            --concurrency=3 \
            --codec=h264 \
            --pixel-format=yuv420p \
            --crf=22 \
            --x264-preset=veryfast \
            --image-format=jpeg \
            --jpeg-quality=90 \
            --gl=swangle

      - name: Upload Rendered Chunk ${{ matrix.chunk.idx }}
        uses: actions/upload-artifact@v4
        with:
          name: long-chunk-${{ matrix.chunk.idx }}
          path: out/chunk_${{ matrix.chunk.idx }}.mp4
          retention-days: 2

  stitch_final_video:
    needs: [plan_and_prepare, render_workers]
    if: needs.plan_and_prepare.outputs.has_input == 'true'
    runs-on: ubuntu-latest
    timeout-minutes: 15

    steps:
      - name: Checkout Stitcher Script
        uses: actions/checkout@v4

      - name: Download Prepared Audio & Metadata
        uses: actions/download-artifact@v4
        with:
          name: prepared-long

      - name: Download All Video Chunks
        uses: actions/download-artifact@v4
        with:
          pattern: long-chunk-*
          path: chunks
          merge-multiple: true

      - name: Set up Python & FFmpeg
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install FFmpeg
        run: |
          sudo apt-get update
          sudo apt-get install -y ffmpeg

      - name: Seamlessly Join Video Chunks + Master Audio
        env:
          VIDEO_FORMAT: "long_16_9"
        run: |
          python scripts/stitch_chunks.py

      - name: Upload Final 16:9 Video
        uses: actions/upload-artifact@v4
        with:
          name: InfraVerse-Long-16-9
          path: |
            out/final_video.mp4
            work/frame0_smoke.png
            work/scene_plan.json
            work/transcript.json
          retention-days: 7
'''

FILES[".github/workflows/render_short.yml"] = r'''
name: Shorts Factory (9:16 Vertical)

on:
  push:
    paths:
      - "input_short/**"
  workflow_dispatch:
    inputs:
      trim_silence:
        description: "Trim long pauses (>0.65s) in Short voiceover?"
        required: false
        default: "false"
        type: choice
        options:
          - "false"
          - "true"
      whisper_model:
        description: "Whisper speech model size"
        required: false
        default: "small"
        type: choice
        options:
          - "tiny"
          - "base"
          - "small"

jobs:
  plan_and_prepare:
    runs-on: ubuntu-latest
    timeout-minutes: 20
    outputs:
      has_input: ${{ steps.check_input.outputs.has_input }}
      chunks_json: ${{ steps.chunk_plan.outputs.chunks_json }}

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Check for uploaded audio inside input_short/
        id: check_input
        run: |
          shopt -s nullglob nocaseglob
          files=(input_short/*.mp3 input_short/*.wav input_short/*.m4a input_short/*.aac input_short/*.flac input_short/*.ogg input_short/*.mp4 input_short/*.mov input_short/*.mkv input_short/*.webm)
          if [ ${#files[@]} -eq 0 ]; then
            echo "has_input=false" >> $GITHUB_OUTPUT
          else
            echo "has_input=true" >> $GITHUB_OUTPUT
            echo "Found 9:16 Short audio: ${files[*]}"
          fi

      - name: Set up Python 3.11
        if: steps.check_input.outputs.has_input == 'true'
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          cache: "pip"

      - name: Set up Node.js 22
        if: steps.check_input.outputs.has_input == 'true'
        uses: actions/setup-node@v4
        with:
          node-version: "22"

      - name: Install FFmpeg & Headless Chrome libraries
        if: steps.check_input.outputs.has_input == 'true'
        run: |
          sudo apt-get update
          sudo apt-get install -y \
            ffmpeg \
            libnss3 libdbus-1-3 libatk1.0-0 libgbm1 libxrandr2 \
            libxkbcommon0 libxfixes3 libxcomposite1 libxdamage1 \
            libatk-bridge2.0-0 libpango-1.0-0 libcairo2 libcups2 \
            libasound2t64 || sudo apt-get install -y libasound2

      - name: Install Python dependencies
        if: steps.check_input.outputs.has_input == 'true'
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      - name: Install Node dependencies & Remotion Headless Chrome
        if: steps.check_input.outputs.has_input == 'true'
        run: |
          npm install --no-audit --no-fund
          npx remotion browser ensure

      - name: Step 1 - Clean Short Audio & Word Timestamps
        if: steps.check_input.outputs.has_input == 'true'
        env:
          INPUT_FOLDER: "input_short"
          TRIM_SILENCE: ${{ github.event.inputs.trim_silence || 'false' }}
          WHISPER_MODEL: ${{ github.event.inputs.whisper_model || 'small' }}
          PREVIEW_SECONDS: "0"
        run: |
          python scripts/analyze_audio.py

      - name: Step 2 - Gemini Vertical 9:16 Multi-Part 3D & HUD Coder
        if: steps.check_input.outputs.has_input == 'true'
        env:
          INPUT_FOLDER: "input_short"
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
          VIDEO_FORMAT: "short_9_16"
        run: |
          python scripts/generate_scenes.py

      - name: Step 3 - Validate Uniqueness, Beats & Zero Overlaps
        if: steps.check_input.outputs.has_input == 'true'
        run: |
          python scripts/validate_scenes.py

      - name: Step 4 - Synthesize & Duck Master Short Audio
        if: steps.check_input.outputs.has_input == 'true'
        run: |
          python scripts/mix_audio.py

      - name: Step 5 - Frame 0 Smoke Test & Bundle Project Once
        if: steps.check_input.outputs.has_input == 'true'
        run: |
          npx remotion still src/index.ts Main work/frame0_smoke.png --frame=0 --gl=swangle
          npx remotion bundle src/index.ts --public-dir public --out-dir build_bundle

      - name: Step 6 - Plan Workers
        id: chunk_plan
        if: steps.check_input.outputs.has_input == 'true'
        env:
          FORCE_WORKERS: "auto"
        run: |
          python scripts/plan_chunks.py

      - name: Upload Prepared Short Bundle
        if: steps.check_input.outputs.has_input == 'true'
        uses: actions/upload-artifact@v4
        with:
          name: prepared-short
          path: |
            build_bundle/
            work/master_audio.m4a
            work/scene_plan.json
            work/transcript.json
            work/frame0_smoke.png
          retention-days: 2

  render_workers:
    needs: plan_and_prepare
    if: needs.plan_and_prepare.outputs.has_input == 'true'
    runs-on: ubuntu-latest
    timeout-minutes: 45
    strategy:
      fail-fast: false
      matrix:
        chunk: ${{ fromJson(needs.plan_and_prepare.outputs.chunks_json) }}

    steps:
      - name: Checkout repository config
        uses: actions/checkout@v4

      - name: Download Prepared Remotion Bundle
        uses: actions/download-artifact@v4
        with:
          name: prepared-short

      - name: Set up Node.js 22
        uses: actions/setup-node@v4
        with:
          node-version: "22"

      - name: Install Headless Chrome OS libraries
        run: |
          sudo apt-get update
          sudo apt-get install -y \
            ffmpeg \
            libnss3 libdbus-1-3 libatk1.0-0 libgbm1 libxrandr2 \
            libxkbcommon0 libxfixes3 libxcomposite1 libxdamage1 \
            libatk-bridge2.0-0 libpango-1.0-0 libcairo2 libcups2 \
            libasound2t64 || sudo apt-get install -y libasound2

      - name: Install Node packages & Remotion Chrome
        run: |
          npm install --no-audit --no-fund
          npx remotion browser ensure

      - name: Render Vertical 9:16 + HUD Chunk ${{ matrix.chunk.idx }}
        run: |
          mkdir -p out
          npx remotion render build_bundle Main out/chunk_${{ matrix.chunk.idx }}.mp4 \
            --frames=${{ matrix.chunk.start }}-${{ matrix.chunk.end }} \
            --muted \
            --concurrency=3 \
            --codec=h264 \
            --pixel-format=yuv420p \
            --crf=22 \
            --x264-preset=veryfast \
            --image-format=jpeg \
            --jpeg-quality=90 \
            --gl=swangle

      - name: Upload Short Chunk ${{ matrix.chunk.idx }}
        uses: actions/upload-artifact@v4
        with:
          name: short-chunk-${{ matrix.chunk.idx }}
          path: out/chunk_${{ matrix.chunk.idx }}.mp4
          retention-days: 2

  stitch_final_short:
    needs: [plan_and_prepare, render_workers]
    if: needs.plan_and_prepare.outputs.has_input == 'true'
    runs-on: ubuntu-latest
    timeout-minutes: 10

    steps:
      - name: Checkout Stitcher Script
        uses: actions/checkout@v4

      - name: Download Prepared Audio & Metadata
        uses: actions/download-artifact@v4
        with:
          name: prepared-short

      - name: Download All Short Chunks
        uses: actions/download-artifact@v4
        with:
          pattern: short-chunk-*
          path: chunks
          merge-multiple: true

      - name: Set up Python & FFmpeg
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install FFmpeg
        run: |
          sudo apt-get update
          sudo apt-get install -y ffmpeg

      - name: Seamlessly Join Short Video + Master Audio
        env:
          VIDEO_FORMAT: "short_9_16"
        run: |
          python scripts/stitch_chunks.py

      - name: Upload Final 9:16 Short
        uses: actions/upload-artifact@v4
        with:
          name: InfraVerse-Short-9-16
          path: |
            out/final_short.mp4
            work/frame0_smoke.png
            work/scene_plan.json
            work/transcript.json
          retention-days: 7
'''


def write_all_files() -> None:
    print(f"[setup_factory] Building {len(FILES)} files in: {ROOT}")
    for rel_path, content in FILES.items():
        target = ROOT / rel_path
        target.parent.mkdir(parents=True, exist_ok=True)
        clean = content.lstrip("\n")
        if clean and not clean.endswith("\n"):
            clean += "\n"
        with open(target, "w", encoding="utf-8", newline="\n") as f:
            f.write(clean)
        print(f"  + {rel_path}")


def run_git_push() -> None:
    def git(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
        return subprocess.run(["git", *args], cwd=str(ROOT), text=True, check=check)

    if git("rev-parse", "--is-inside-work-tree", check=False).returncode != 0:
        print("\n[setup_factory] Not inside a git repo yet. Push manually after git init.")
        return

    git("add", ".")
    if git("diff", "--cached", "--quiet", check=False).returncode != 0:
        git("commit", "-m", "Upgrade to v3.1: Closer Camera, Blueprint Grid, Literal Prefabs & Fixed HUD/Subtitles")
    if git("push", check=False).returncode != 0:
        git("push", "-u", "origin", "HEAD")
    print("\n[setup_factory] SUCCESS! v3.1 Factory is live on GitHub.")


if __name__ == "__main__":
    write_all_files()
    try:
        run_git_push()
    except subprocess.CalledProcessError as exc:
        print(f"\n[setup_factory] Git error ({exc}).")
        sys.exit(exc.returncode)

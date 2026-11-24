#!/usr/bin/env python3
"""
InfraVerse 2D Illustrated Documentary & Shorts Factory (v4.0).
Modeled on Video 1's hand-inked 2D vector cartoon style:
  - 11 switchable backdrop worlds controlled by visuals.txt while keeping unified 2D ink style
  - Reusable CartoonCharacter2D rig (blinking, expressions, poses, sweat drops, hats/glasses)
  - Video-1 mechanics: SplitScreen3Panel, TitleCard2D, LineChart2D, BalanceScale2D,
    ConveyorBelt2D, WorldMapArc2D, QuoteHighlight2D, CalendarFlip2D, Stopwatch2D, InkCallout2D
  - Built-in ReactorVessel2D, CoolingTower2D, ServerRack2D, Microchip2D, PowerPylon2D, BatteryBank2D + custom Gemini SVGs
  - Tight word-level audio sync, zero visual repetition, continuous camera motion & human-style transitions
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
  "name": "infraverse-2d-cartoon-factory",
  "version": "4.0.0",
  "private": true,
  "description": "Video-1 style 2D vector cartoon & motion graphics documentary factory",
  "scripts": {
    "dev": "remotion studio src/index.ts",
    "build": "remotion bundle src/index.ts --public-dir public --out-dir build_bundle",
    "typecheck": "tsc --noEmit"
  },
  "dependencies": {
    "@remotion/cli": "4.0.543",
    "@remotion/google-fonts": "4.0.543",
    "react": "18.3.1",
    "react-dom": "18.3.1",
    "remotion": "4.0.543"
  },
  "devDependencies": {
    "@types/node": "22.13.0",
    "@types/react": "18.3.12",
    "@types/react-dom": "18.3.1",
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
Config.setJpegQuality(92);
Config.setOffthreadVideoCacheSizeInBytes(1024 * 1024 * 1024);
Config.setCodec("h264");
Config.setPixelFormat("yuv420p");
'''

FILES["input/visuals_EXAMPLE.txt"] = r'''
# Control environments & visuals in plain English while keeping the unified 2D cartoon look!
# Available environment moods:
# night_mountains, sunset_horizon, daylight_city, graph_paper, notebook_lined,
# world_map, warm_office, steel_vault, dark_industrial, news_document, split_3panel, black_title_card

Example for Week 1 ($100B AI Data Center):
- Start on night_mountains: Cartoon CEO sweating while holding up a huge glowing cracking AI chip, handwritten "$100B" callout.
- Quick black_title_card: "Nobody noticed."
- Cut to split_3panel daylight comic: Bank building, Power substation, City street with skyline.
- Cut to graph_paper: Rising red power demand line chart going from 100 MW to 1,000 MW with city skyline below.
- Cut to dark_industrial: Server corridor with blinking racks and conveyor belt stamping 2024 -> 2025 -> 2026 chips.
- Cut to warm_office: Engineering report quote with yellow highlighter sweeping "LIQUID COOLING REQUIRED" and red circle.
- Cut to steel_vault / sunset_horizon: Nuclear SMR reactor vessel + cooling towers + battery containers powering the grid.
'''

FILES["input_short/visuals_EXAMPLE.txt"] = r'''
# Upload your X-second 9:16 Short voiceover.mp3 + visuals.txt inside input_short/!
# Same 2D cartoon environments & characters, framed cleanly for vertical 1080x1920!
'''

for gitkeep_rel in (
    "input/.gitkeep",
    "input_short/.gitkeep",
    "out/.gitkeep",
    "work/.gitkeep",
    "public/audio/.gitkeep",
    "public/audio/sfx/.gitkeep",
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
    print("[analyze_audio] Detecting vocal emphasis peaks & pauses...")
    y, sr = librosa.load(str(wav_path), sr=22050, mono=True)
    duration_sec = float(librosa.get_duration(y=y, sr=sr))

    hop_length = 512
    rms = librosa.feature.rms(y=y, frame_length=2048, hop_length=hop_length)[0]
    onset_env = librosa.onset.onset_strength(y=y, sr=sr, hop_length=hop_length)

    rms_norm = rms / (np.max(rms) + 1e-8)
    onset_norm = onset_env / (np.max(onset_env) + 1e-8)
    combined = 0.65 * rms_norm + 0.35 * onset_norm

    min_distance = int((1.8 * sr) / hop_length)
    peaks, _ = find_peaks(
        combined,
        height=float(np.percentile(combined, 68)),
        distance=max(1, min_distance),
        prominence=0.09,
    )
    peak_times = [round(float(librosa.frames_to_time(p, sr=sr, hop_length=hop_length)), 3) for p in peaks]

    tempo, _ = librosa.beat.beat_track(onset_envelope=onset_env, sr=sr, hop_length=hop_length)
    bpm_val = float(np.atleast_1d(tempo)[0]) if np.size(tempo) > 0 else 104.0
    if bpm_val < 70 or bpm_val > 135:
        bpm_val = 104.0

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
'''

FILES["scripts/validate_scenes.py"] = r'''
import json
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parent.parent
PLAN_PATH = ROOT / "work" / "scene_plan.json"
SCENES_DIR = ROOT / "src" / "generated" / "scenes"
TIMELINE_PATH = ROOT / "src" / "generated" / "GeneratedTimeline.tsx"

FORBIDDEN_TOKENS = ("<div", "<span", "useFrame", "useEffect", "useState", "from 'three'", 'from "three"')


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

        if idx > 0:
            prev = scenes[idx - 1]
            if abs(float(sc["startSec"]) - float(prev["endSec"])) > 0.01:
                errors.append(f"Timeline gap between {prev['id']} and {sc['id']}.")
            if sc["backdropTheme"] == prev["backdropTheme"] and sc["backdropTheme"] != "black_title_card":
                errors.append(f"Consecutive identical backdropTheme '{sc['backdropTheme']}' at {sc['id']}.")

        dur = float(sc["endSec"]) - float(sc["startSec"])
        if dur > 9.5:
            errors.append(f"{sc['id']} duration {dur:.2f}s exceeds 9.5s max hold.")

        cname = sc.get("componentName")
        if not (SCENES_DIR / f"{cname}.tsx").exists():
            errors.append(f"Missing generated scene component: {cname}.tsx")

    return errors


def audit_source_files() -> List[str]:
    errors: List[str] = []
    for f in list(SCENES_DIR.glob("Scene_*.tsx")):
        txt = f.read_text(encoding="utf-8")
        for tok in FORBIDDEN_TOKENS:
            if tok in txt:
                errors.append(f"Forbidden token '{tok}' inside {f.name}")
    return errors


def main() -> None:
    if not PLAN_PATH.exists():
        raise SystemExit("Missing work/scene_plan.json")
    plan = json.loads(PLAN_PATH.read_text(encoding="utf-8"))
    errs = audit_plan(plan) + audit_source_files()
    if errs:
        raise SystemExit("[validate_scenes] FAILED:\n - " + "\n - ".join(errs))
    print(f"[validate_scenes] PASSED: {len(plan['scenes'])} unique continuous 2D cartoon scenes.")


if __name__ == "__main__":
    main()
'''

FILES["scripts/mix_audio.py"] = r'''
import json
import os
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


def synthesize_underscore_bgm(n_samples: int, bpm: float) -> np.ndarray:
    t = np.arange(n_samples, dtype=np.float64) / SAMPLE_RATE
    bar_sec = (60.0 / max(75.0, min(125.0, bpm))) * 4.0
    chords = [
        [146.83, 220.00, 261.63, 329.63],
        [116.54, 174.61, 220.00, 293.66],
        [130.81, 196.00, 246.94, 293.66],
        [110.00, 164.81, 220.00, 261.63],
    ]
    bar_idx = (t / bar_sec).astype(int) % len(chords)
    bar_phase = (t % bar_sec) / bar_sec
    env = np.sin(np.pi * np.clip(bar_phase, 0.0, 1.0)) ** 0.45

    left = np.zeros(n_samples, dtype=np.float64)
    right = np.zeros(n_samples, dtype=np.float64)
    for c_i, freqs in enumerate(chords):
        mask = (bar_idx == c_i).astype(np.float64)
        sig_l = np.zeros(n_samples, dtype=np.float64)
        sig_r = np.zeros(n_samples, dtype=np.float64)
        for v_i, freq in enumerate(freqs):
            detune = 1.002 if v_i % 2 == 0 else 0.998
            sig_l += 0.22 * np.sin(2.0 * np.pi * freq * t)
            sig_r += 0.22 * np.sin(2.0 * np.pi * freq * detune * t + 0.4)
        left += mask * env * sig_l
        right += mask * env * sig_r

    beat_period = 60.0 / bpm
    pulse = np.sin(2.0 * np.pi * 196.0 * t) * np.exp(-((t % beat_period) / beat_period) * 12.0) * 0.14
    left = lowpass(left + pulse, 1050.0)
    right = lowpass(right + pulse, 1050.0)
    stereo = np.column_stack([left, right])
    stereo = stereo / (float(np.max(np.abs(stereo))) + 1e-9)

    fade_in = min(n_samples, int(1.5 * SAMPLE_RATE))
    fade_out = min(n_samples, int(2.0 * SAMPLE_RATE))
    if fade_in > 0:
        stereo[:fade_in] *= np.linspace(0.0, 1.0, fade_in)[:, None]
    if fade_out > 0:
        stereo[-fade_out:] *= np.linspace(1.0, 0.0, fade_out)[:, None]
    return stereo


def make_sfx_bank() -> dict[str, np.ndarray]:
    rng = np.random.default_rng(17)

    # 1. Smooth slide whoosh
    nw = int(0.32 * SAMPLE_RATE)
    tw = np.arange(nw) / SAMPLE_RATE
    w = bandpass(rng.normal(0.0, 1.0, nw), 320.0, 2400.0) * (np.sin(np.pi * tw / 0.32) ** 1.5)
    whoosh = np.column_stack([w, w * 0.94]) / (float(np.max(np.abs(w))) + 1e-9)

    # 2. Cartoon pop snap
    npop = int(0.11 * SAMPLE_RATE)
    tp = np.arange(npop) / SAMPLE_RATE
    fp = 360.0 + 480.0 * (1.0 - np.exp(-tp * 38.0))
    p = np.sin(2.0 * np.pi * np.cumsum(fp) / SAMPLE_RATE) * np.exp(-tp * 32.0)
    pop_snap = np.column_stack([p, p]) / (float(np.max(np.abs(p))) + 1e-9)

    # 3. Marker / highlighter swipe
    nm = int(0.28 * SAMPLE_RATE)
    tm = np.arange(nm) / SAMPLE_RATE
    m = bandpass(rng.normal(0.0, 1.0, nm), 1200.0, 4200.0) * (np.sin(np.pi * tm / 0.28) ** 1.2)
    marker_swipe = np.column_stack([m, m]) / (float(np.max(np.abs(m))) + 1e-9)

    # 4. Dramatic sub impact
    ns = int(0.45 * SAMPLE_RATE)
    ts = np.arange(ns) / SAMPLE_RATE
    fs = 105.0 * np.exp(-ts * 4.5) + 40.0
    s = np.sin(2.0 * np.pi * np.cumsum(fs) / SAMPLE_RATE) * np.exp(-ts * 5.5) * np.minimum(1.0, ts / 0.012)
    sub_impact = np.column_stack([s, s]) / (float(np.max(np.abs(s))) + 1e-9)

    # 5. Crisp tick
    nt = int(0.07 * SAMPLE_RATE)
    tt = np.arange(nt) / SAMPLE_RATE
    tk = np.sin(2.0 * np.pi * 1600.0 * tt) * np.exp(-tt * 70.0)
    tick = np.column_stack([tk, tk]) / (float(np.max(np.abs(tk))) + 1e-9)

    return {
        "whoosh": whoosh * 0.14,
        "pop_snap": pop_snap * 0.16,
        "marker_swipe": marker_swipe * 0.12,
        "sub_impact": sub_impact * 0.20,
        "tick": tick * 0.11,
    }


def main() -> None:
    plan = json.loads((WORK_DIR / "scene_plan.json").read_text(encoding="utf-8"))
    vo_data, sr = sf.read(str(WORK_DIR / "clean_voiceover.wav"), dtype="float64")
    if sr != SAMPLE_RATE:
        raise RuntimeError(f"Expected 48000 Hz clean_voiceover.wav, got {sr}")
    vo_mono = np.mean(vo_data, axis=1) if vo_data.ndim > 1 else vo_data

    n_samples = len(vo_mono)
    vo_stereo = np.column_stack([vo_mono, vo_mono])

    include_bgm = os.environ.get("INCLUDE_BGM", "true").lower() == "true"
    if include_bgm:
        abs_vo = np.abs(vo_mono)
        smooth_env = lowpass(abs_vo, 3.0)
        speech_active = np.clip(smooth_env / (np.percentile(smooth_env, 90) + 1e-6), 0.0, 1.0)
        duck_gain = 0.085 - 0.042 * speech_active
        bgm_stereo = synthesize_underscore_bgm(n_samples, float(plan.get("bpm", 104.0)))
        mix = vo_stereo * 0.92 + bgm_stereo * duck_gain[:, None]
    else:
        mix = vo_stereo * 0.94

    sfx_bank = make_sfx_bank()
    for sc in plan["scenes"]:
        cue = sc.get("sfx", "pop_snap")
        snd = sfx_bank.get(cue, sfx_bank["pop_snap"])
        start_idx = max(0, int(float(sc["startSec"]) * SAMPLE_RATE))
        end_idx = min(n_samples, start_idx + len(snd))
        if end_idx > start_idx:
            mix[start_idx:end_idx] += snd[: end_idx - start_idx]

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
    print(f"[mix_audio] Built master_audio.m4a ({n_samples / SAMPLE_RATE:.2f}s, include_bgm={include_bgm}).")


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
export type BackdropTheme =
  | "night_mountains"
  | "sunset_horizon"
  | "daylight_city"
  | "graph_paper"
  | "notebook_lined"
  | "world_map"
  | "warm_office"
  | "steel_vault"
  | "dark_industrial"
  | "news_document"
  | "split_3panel"
  | "black_title_card";

export type CameraMove2D =
  | "push_in"
  | "pull_out"
  | "pan_right"
  | "pan_left"
  | "pan_up"
  | "shake_hit";

export type Transition2D =
  | "slide_left"
  | "slide_up"
  | "wipe_right"
  | "zoom_dissolve"
  | "flash_cut";

export interface Scene2DProps {
  frame: number;
  localFrame: number;
  localTime: number;
  durationSec: number;
  progress: number;
  peakTimes: number[];
  accentHex: string;
  backdropTheme: BackdropTheme;
  cameraMove: CameraMove2D;
  isVertical: boolean;
}

export interface CartoonScene {
  id: string;
  componentName: string;
  visualConcept: string;
  visualSpec: string;
  titleText: string;
  backdropTheme: BackdropTheme;
  cameraMove: CameraMove2D;
  transition: Transition2D;
  sfx: string;
  accentHex: string;
  startSec: number;
  endSec: number;
  localPeakTimes: number[];
}

export interface CartoonPlan {
  channel: string;
  fps: number;
  width: number;
  height: number;
  totalDurationSec: number;
  hasAudio: boolean;
  bpm: number;
  emphasisPeaksSec: number[];
  scenes: CartoonScene[];
}
'''

FILES["src/components/CartoonKit2D.tsx"] = r'''
import React, { useId } from "react";
import { loadFont as loadCaveat } from "@remotion/google-fonts/Caveat";
import { loadFont as loadPermanentMarker } from "@remotion/google-fonts/PermanentMarker";
import { loadFont as loadSpaceGrotesk } from "@remotion/google-fonts/SpaceGrotesk";
import { interpolate, spring, useVideoConfig } from "remotion";
import type { BackdropTheme, CameraMove2D } from "../types";

const { fontFamily: HAND_FONT } = loadCaveat("normal", { weights: ["700"], subsets: ["latin"] });
const { fontFamily: MARKER_FONT } = loadPermanentMarker("normal", { weights: ["400"], subsets: ["latin"] });
const { fontFamily: UI_FONT } = loadSpaceGrotesk("normal", { weights: ["600", "700"], subsets: ["latin"] });

const INK = "#111827";

export const SceneBackdrop2D: React.FC<{
  theme: BackdropTheme;
  frame: number;
  accentHex?: string;
}> = ({ theme, frame, accentHex = "#22C55E" }) => {
  const uid = useId().replace(/:/g, "");
  const gradId = `bg_${uid}`;
  const cloudDrift = (frame * 0.45) % 2100;

  if (theme === "black_title_card") {
    return <rect x={-100} y={-100} width={2200} height={2200} fill="#05070B" />;
  }

  if (theme === "night_mountains") {
    return (
      <g>
        <defs>
          <linearGradient id={gradId} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#09111E" />
            <stop offset="68%" stopColor="#142A3E" />
            <stop offset="100%" stopColor="#1D3E4D" />
          </linearGradient>
        </defs>
        <rect x={-100} y={-100} width={2200} height={2200} fill={`url(#${gradId})`} />
        {[
          [180, 140], [420, 90], [690, 200], [980, 110], [1340, 160], [1680, 100], [1810, 240], [310, 320], [1510, 290],
        ].map(([sx, sy], i) => {
          const tw = 0.35 + 0.65 * Math.abs(Math.sin(frame * 0.05 + i));
          return <circle key={i} cx={sx} cy={sy} r={3 + (i % 2)} fill="#E2E8F0" opacity={tw} />;
        })}
        <polygon points="-50,920 260,640 540,860 890,560 1240,840 1580,620 1980,900 1980,2000 -50,2000" fill="#0F1F2E" stroke={INK} strokeWidth={4} />
        <rect x={-50} y={840} width={2050} height={1200} fill="#182538" stroke={INK} strokeWidth={4} />
      </g>
    );
  }

  if (theme === "sunset_horizon") {
    return (
      <g>
        <defs>
          <linearGradient id={gradId} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#D97762" />
            <stop offset="55%" stopColor="#F4B27A" />
            <stop offset="100%" stopColor="#FDE2A6" />
          </linearGradient>
        </defs>
        <rect x={-100} y={-100} width={2200} height={2200} fill={`url(#${gradId})`} />
        <circle cx={340} cy={310} r={115} fill="#FEF3C7" stroke="#F59E0B" strokeWidth={5} />
        <ellipse cx={(200 + cloudDrift) % 2100 - 100} cy={220} rx={120} ry={34} fill="#FFEAD5" opacity={0.85} />
        <ellipse cx={(1100 + cloudDrift * 0.7) % 2100 - 100} cy={170} rx={150} ry={38} fill="#FFEAD5" opacity={0.75} />
        <polygon points="-40,860 360,560 720,780 1120,520 1540,790 1980,580 1980,2000 -40,2000" fill="#B57B6B" stroke={INK} strokeWidth={4} />
        <rect x={-50} y={820} width={2050} height={1200} fill="#C69262" stroke={INK} strokeWidth={4} />
      </g>
    );
  }

  if (theme === "daylight_city" || theme === "split_3panel") {
    return (
      <g>
        <rect x={-100} y={-100} width={2200} height={2200} fill="#CBE4F5" />
        <ellipse cx={(300 + cloudDrift) % 2100 - 100} cy={180} rx={130} ry={40} fill="#FFFFFF" opacity={0.9} />
        <ellipse cx={(1250 + cloudDrift * 0.6) % 2100 - 100} cy={130} rx={160} ry={44} fill="#FFFFFF" opacity={0.85} />
        <rect x={-50} y={820} width={2050} height={1200} fill="#9CA3AF" stroke={INK} strokeWidth={4} />
      </g>
    );
  }

  if (theme === "graph_paper") {
    return (
      <g>
        <rect x={-100} y={-100} width={2200} height={2200} fill="#EAE6DC" />
        {Array.from({ length: 28 }).map((_, i) => (
          <line key={`v${i}`} x1={i * 80} y1={-50} x2={i * 80} y2={2000} stroke="#D4CFC2" strokeWidth={2} />
        ))}
        {Array.from({ length: 26 }).map((_, i) => (
          <line key={`h${i}`} x1={-50} y1={i * 80} x2={2000} y2={i * 80} stroke="#D4CFC2" strokeWidth={2} />
        ))}
      </g>
    );
  }

  if (theme === "notebook_lined") {
    return (
      <g>
        <rect x={-100} y={-100} width={2200} height={2200} fill="#F7F3E9" />
        <line x1={210} y1={-50} x2={210} y2={2000} stroke="#EF4444" strokeWidth={4} opacity={0.55} />
        {Array.from({ length: 28 }).map((_, i) => (
          <line key={i} x1={-50} y1={120 + i * 68} x2={2000} y2={120 + i * 68} stroke="#93C5FD" strokeWidth={2} opacity={0.65} />
        ))}
      </g>
    );
  }

  if (theme === "world_map") {
    return (
      <g>
        <rect x={-100} y={-100} width={2200} height={2200} fill="#8FB5C9" />
        {Array.from({ length: 14 }).map((_, i) => (
          <line key={`g${i}`} x1={i * 160} y1={-50} x2={i * 160} y2={2000} stroke="#7CA3B8" strokeWidth={2} strokeDasharray="8 8" />
        ))}
      </g>
    );
  }

  if (theme === "warm_office") {
    return (
      <g>
        <rect x={-100} y={-100} width={2200} height={2200} fill="#C9B99F" />
        <rect x={120} y={90} width={380} height={280} fill="#BAE6FD" stroke={INK} strokeWidth={5} />
        <line x1={310} y1={90} x2={310} y2={370} stroke={INK} strokeWidth={4} />
        <rect x={-50} y={760} width={2050} height={1200} fill="#6F4E37" stroke={INK} strokeWidth={5} />
      </g>
    );
  }

  if (theme === "steel_vault") {
    return (
      <g>
        <rect x={-100} y={-100} width={2200} height={2200} fill="#374151" />
        <polygon points="960,-40 240,1200 1680,1200" fill="#FDE68A" opacity={0.14} />
        <rect x={-50} y={840} width={2050} height={1200} fill="#1F2937" stroke={INK} strokeWidth={5} />
      </g>
    );
  }

  if (theme === "news_document") {
    return (
      <g>
        <rect x={-100} y={-100} width={2200} height={2200} fill="#CBD5E1" />
        <rect x={140} y={100} width={1640} height={880} rx={14} fill="#F8FAFC" stroke={INK} strokeWidth={5} />
      </g>
    );
  }

  // dark_industrial default
  return (
    <g>
      <rect x={-100} y={-100} width={2200} height={2200} fill="#1E293B" />
      {[280, 680, 1240, 1640].map((lx, i) => (
        <rect key={i} x={lx - 80} y={40} width={160} height={24} rx={8} fill={accentHex} opacity={0.85} stroke={INK} strokeWidth={3} />
      ))}
      <rect x={-50} y={840} width={2050} height={1200} fill="#334155" stroke={INK} strokeWidth={5} />
      <rect x={-50} y={840} width={2050} height={26} fill="#F59E0B" stroke={INK} strokeWidth={3} />
    </g>
  );
};

export const Camera2D: React.FC<{
  move: CameraMove2D;
  progress: number;
  frame: number;
  peakTimes?: number[];
  localTime: number;
  children?: React.ReactNode;
}> = ({ move, progress, frame, peakTimes = [], localTime, children }) => {
  const ease = progress * progress * (3 - 2 * progress);
  let scale = 1;
  let tx = 0;
  let ty = 0;

  if (move === "push_in") {
    scale = 1 + ease * 0.08;
  } else if (move === "pull_out") {
    scale = 1.09 - ease * 0.09;
  } else if (move === "pan_right") {
    scale = 1.05;
    tx = 32 - ease * 64;
  } else if (move === "pan_left") {
    scale = 1.05;
    tx = -32 + ease * 64;
  } else if (move === "pan_up") {
    scale = 1.05;
    ty = 26 - ease * 52;
  } else if (move === "shake_hit") {
    scale = 1.04;
  }

  // Punchy human-edited camera impact jolt on vocal emphasis peaks
  let shakeX = 0;
  let shakeY = 0;
  for (const pt of peakTimes) {
    const dt = localTime - pt;
    if (dt >= 0 && dt < 0.28) {
      const decay = 1 - dt / 0.28;
      shakeX += Math.sin(frame * 2.7) * 9 * decay;
      shakeY += Math.cos(frame * 3.1) * 7 * decay;
    }
  }

  const cx = 960;
  const cy = 540;
  const xform = `translate(${cx + tx + shakeX} ${cy + ty + shakeY}) scale(${scale}) translate(${-cx} ${-cy})`;

  return <g transform={xform}>{children}</g>;
};

export const CartoonCharacter2D: React.FC<{
  x: number;
  y: number;
  scale?: number;
  variant?: "ceo" | "engineer" | "worker" | "suit" | "operator";
  mood?: "neutral" | "shocked" | "worried" | "happy" | "smug" | "angry";
  pose?: "stand" | "point_right" | "point_up" | "hold_up" | "hands_head" | "celebrate";
  glasses?: boolean;
  hardHat?: boolean;
  sweatDrop?: boolean;
  flip?: boolean;
  frame: number;
}> = ({
  x,
  y,
  scale = 1,
  variant = "engineer",
  mood = "neutral",
  pose = "stand",
  glasses = false,
  hardHat = false,
  sweatDrop = false,
  flip = false,
  frame,
}) => {
  const bob = Math.sin(frame * 0.1) * 4;
  const blink = frame % 95 >= 91;
  const wave = Math.sin(frame * 0.16) * 8;
  const dir = flip ? -1 : 1;

  const outfitMap: Record<string, string> = {
    ceo: "#1F2937",
    engineer: "#2563EB",
    worker: "#EA580C",
    suit: "#334155",
    operator: "#059669",
  };
  const bodyColor = outfitMap[variant] || "#2563EB";
  const hairColor = variant === "ceo" ? "#CBD5E1" : "#374151";
  const skinColor = "#F3C69F";
  const sweatY = ((frame * 2.4) % 34);

  return (
    <g transform={`translate(${x} ${y + bob}) scale(${scale * dir} ${scale})`}>
      {/* Ground Shadow */}
      <ellipse cx={0} cy={175} rx={58} ry={14} fill="#000000" opacity={0.28} />
      {/* Stick Legs */}
      <line x1={-18} y1={105} x2={-22} y2={170} stroke={INK} strokeWidth={7} strokeLinecap="round" />
      <line x1={18} y1={105} x2={22} y2={170} stroke={INK} strokeWidth={7} strokeLinecap="round" />
      {/* Torso */}
      <rect x={-46} y={-22} width={92} height={132} rx={44} fill={bodyColor} stroke={INK} strokeWidth={5} />
      {variant === "suit" || variant === "ceo" ? (
        <polygon points="-14,-20 14,-20 6,42 -6,42" fill="#E11D48" stroke={INK} strokeWidth={3} />
      ) : null}

      {/* Stick Arms by Pose */}
      {pose === "point_right" ? (
        <>
          <line x1={-44} y1={18} x2={-78} y2={62} stroke={INK} strokeWidth={6} strokeLinecap="round" />
          <line x1={44} y1={16} x2={115} y2={-6 + wave * 0.5} stroke={INK} strokeWidth={6} strokeLinecap="round" />
        </>
      ) : pose === "point_up" || pose === "hold_up" ? (
        <>
          <line x1={-44} y1={18} x2={-72} y2={-68 + wave * 0.4} stroke={INK} strokeWidth={6} strokeLinecap="round" />
          <line x1={44} y1={18} x2={72} y2={-68 + wave * 0.4} stroke={INK} strokeWidth={6} strokeLinecap="round" />
        </>
      ) : pose === "hands_head" ? (
        <>
          <path d="M -44 16 Q -90 -30 -56 -80" fill="none" stroke={INK} strokeWidth={6} strokeLinecap="round" />
          <path d="M 44 16 Q 90 -30 56 -80" fill="none" stroke={INK} strokeWidth={6} strokeLinecap="round" />
        </>
      ) : pose === "celebrate" ? (
        <>
          <line x1={-44} y1={18} x2={-86} y2={-52 + wave} stroke={INK} strokeWidth={6} strokeLinecap="round" />
          <line x1={44} y1={18} x2={86} y2={-52 - wave} stroke={INK} strokeWidth={6} strokeLinecap="round" />
        </>
      ) : (
        <>
          <line x1={-44} y1={18} x2={-72} y2={68 + wave * 0.3} stroke={INK} strokeWidth={6} strokeLinecap="round" />
          <line x1={44} y1={18} x2={72} y2={68 - wave * 0.3} stroke={INK} strokeWidth={6} strokeLinecap="round" />
        </>
      )}

      {/* Oval Cartoon Head */}
      <circle cx={0} cy={-78} r={54} fill={skinColor} stroke={INK} strokeWidth={5} />
      {/* Hair */}
      <path d="M -52 -88 Q -42 -142 0 -138 Q 42 -142 52 -88 Q 22 -106 0 -100 Q -22 -106 -52 -88 Z" fill={hairColor} stroke={INK} strokeWidth={4} />

      {/* Hard Hat */}
      {hardHat && (
        <g>
          <path d="M -54 -96 Q -48 -150 0 -150 Q 48 -150 54 -96 Z" fill="#FACC15" stroke={INK} strokeWidth={5} />
          <rect x={-64} y={-98} width={128} height={14} rx={7} fill="#EAB308" stroke={INK} strokeWidth={4} />
        </g>
      )}

      {/* Eyes (with automatic blink) */}
      {blink ? (
        <>
          <line x1={-24} y1={-80} x2={-10} y2={-80} stroke={INK} strokeWidth={4} strokeLinecap="round" />
          <line x1={10} y1={-80} x2={24} y2={-80} stroke={INK} strokeWidth={4} strokeLinecap="round" />
        </>
      ) : (
        <>
          <circle cx={-16} cy={-80} r={mood === "shocked" ? 8 : 5.5} fill={INK} />
          <circle cx={16} cy={-80} r={mood === "shocked" ? 8 : 5.5} fill={INK} />
        </>
      )}

      {/* Glasses */}
      {glasses && (
        <g>
          <rect x={-32} y={-92} width={28} height={22} rx={5} fill="none" stroke={INK} strokeWidth={3.5} />
          <rect x={4} y={-92} width={28} height={22} rx={5} fill="none" stroke={INK} strokeWidth={3.5} />
          <line x1={-4} y1={-81} x2={4} y2={-81} stroke={INK} strokeWidth={3.5} />
        </g>
      )}

      {/* Eyebrows + Mouth by Mood */}
      {mood === "shocked" ? (
        <ellipse cx={0} cy={-50} rx={11} ry={14} fill="#7F1D1D" stroke={INK} strokeWidth={3.5} />
      ) : mood === "worried" || mood === "angry" ? (
        <>
          <line x1={-28} y1={-96} x2={-8} y2={-91} stroke={INK} strokeWidth={4} strokeLinecap="round" />
          <line x1={8} y1={-91} x2={28} y2={-96} stroke={INK} strokeWidth={4} strokeLinecap="round" />
          <path d="M -16 -46 Q 0 -60 16 -46" fill="none" stroke={INK} strokeWidth={4.5} strokeLinecap="round" />
        </>
      ) : mood === "happy" || mood === "smug" ? (
        <path d="M -18 -56 Q 0 -38 18 -56" fill="#FFFFFF" stroke={INK} strokeWidth={4} strokeLinecap="round" />
      ) : (
        <line x1={-14} y1={-52} x2={14} y2={-52} stroke={INK} strokeWidth={4.5} strokeLinecap="round" />
      )}

      {/* Animated Sweat Drop */}
      {sweatDrop && (
        <path
          d={`M ${-48} ${-108 + sweatY} Q ${-56} ${-92 + sweatY} ${-48} ${-86 + sweatY} Q ${-40} ${-92 + sweatY} ${-48} ${-108 + sweatY} Z`}
          fill="#38BDF8"
          stroke={INK}
          strokeWidth={2.5}
          opacity={1 - sweatY / 38}
        />
      )}
    </g>
  );
};

export const TitleCard2D: React.FC<{
  text: string;
  progress: number;
  accentHex?: string;
}> = ({ text, progress, accentHex = "#22C55E" }) => {
  const words = text.split(" ");
  const shownCount = Math.max(1, Math.ceil(Math.min(1, progress * 1.65) * words.length));
  const shownText = words.slice(0, shownCount).join(" ");
  const s = 0.94 + Math.min(1, progress * 2.5) * 0.06;

  return (
    <g transform={`translate(960 540) scale(${s}) translate(-960 -540)`}>
      <text
        x={960}
        y={555}
        textAnchor="middle"
        fill="#FFFFFF"
        fontFamily={HAND_FONT}
        fontSize={106}
        fontWeight={700}
      >
        {shownText}
      </text>
      <line
        x1={720}
        y1={592}
        x2={720 + 480 * Math.min(1, progress * 1.5)}
        y2={592}
        stroke={accentHex}
        strokeWidth={7}
        strokeLinecap="round"
      />
    </g>
  );
};

export const InkCallout2D: React.FC<{
  x: number;
  y: number;
  text: string;
  color?: string;
  fontSize?: number;
  delaySec?: number;
  localTime: number;
  rotateDeg?: number;
  arrowTo?: [number, number];
}> = ({
  x,
  y,
  text,
  color = "#FFFFFF",
  fontSize = 68,
  delaySec = 0,
  localTime,
  rotateDeg = -3,
  arrowTo,
}) => {
  const { fps } = useVideoConfig();
  const f = Math.max(0, Math.round((localTime - delaySec) * fps));
  const pop = spring({ frame: f, fps, config: { damping: 14, stiffness: 180, mass: 0.75 } });
  if (localTime < delaySec) return null;

  return (
    <g>
      {arrowTo && (
        <line
          x1={x}
          y1={y + 18}
          x2={x + (arrowTo[0] - x) * pop}
          y2={y + 18 + (arrowTo[1] - (y + 18)) * pop}
          stroke={color}
          strokeWidth={6}
          strokeDasharray="12 10"
          strokeLinecap="round"
        />
      )}
      <g transform={`translate(${x} ${y}) rotate(${rotateDeg}) scale(${0.5 + 0.5 * pop})`}>
        <text
          x={0}
          y={0}
          textAnchor="middle"
          fill={INK}
          stroke={INK}
          strokeWidth={12}
          strokeLinejoin="round"
          fontFamily={MARKER_FONT}
          fontSize={fontSize}
        >
          {text}
        </text>
        <text
          x={0}
          y={0}
          textAnchor="middle"
          fill={color}
          fontFamily={MARKER_FONT}
          fontSize={fontSize}
        >
          {text}
        </text>
      </g>
    </g>
  );
};

export const LineChart2D: React.FC<{
  x: number;
  y: number;
  w?: number;
  h?: number;
  label?: string;
  startVal?: number;
  endVal?: number;
  prefix?: string;
  suffix?: string;
  decimals?: number;
  color?: string;
  points?: number[];
  progress: number;
}> = ({
  x,
  y,
  w = 1000,
  h = 460,
  label = "METRIC",
  startVal = 0,
  endVal = 100,
  prefix = "",
  suffix = "",
  decimals = 0,
  color = "#EF4444",
  points = [0.15, 0.22, 0.34, 0.42, 0.65, 0.85, 0.96],
  progress,
}) => {
  const drawProg = Math.min(1, progress * 1.4);
  const pathPts = points.map((p, idx) => {
    const px = x + (idx / Math.max(1, points.length - 1)) * w;
    const py = y + h - p * h * 0.82 - 30;
    return `${idx === 0 ? "M" : "L"} ${px.toFixed(1)} ${py.toFixed(1)}`;
  });
  const d = pathPts.join(" ");
  const totalLen = w * 1.6;
  const val = startVal + (endVal - startVal) * drawProg;
  const formatted = `${prefix}${Number(val.toFixed(decimals)).toLocaleString("en-US", {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  })}${suffix}`;

  return (
    <g>
      <rect x={x - 30} y={y - 30} width={w + 60} height={h + 80} rx={16} fill="#FFFFFF" fillOpacity={0.78} stroke={INK} strokeWidth={5} />
      <line x1={x} y1={y + h} x2={x + w} y2={y + h} stroke={INK} strokeWidth={5} />
      <line x1={x} y1={y} x2={x} y2={y + h} stroke={INK} strokeWidth={5} />
      <path
        d={d}
        fill="none"
        stroke={color}
        strokeWidth={11}
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeDasharray={totalLen}
        strokeDashoffset={totalLen * (1 - drawProg)}
      />
      <text x={x + 24} y={y + 42} fill={INK} fontFamily={UI_FONT} fontSize={32} fontWeight={700}>
        {label}
      </text>
      <text x={x + w - 20} y={y + 62} textAnchor="end" fill={color} fontFamily={MARKER_FONT} fontSize={62}>
        {formatted}
      </text>
    </g>
  );
};

export const BarChart2D: React.FC<{
  x: number;
  y: number;
  w?: number;
  h?: number;
  bars: { label: string; value: number; color?: string }[];
  multiplierTag?: string;
  suffix?: string;
  prefix?: string;
  progress: number;
}> = ({ x, y, w = 900, h = 480, bars, multiplierTag, prefix = "", suffix = "", progress }) => {
  const maxVal = Math.max(1, ...bars.map((b) => b.value));
  const barW = Math.min(180, (w / Math.max(1, bars.length)) * 0.56);
  const gap = w / Math.max(1, bars.length);
  const grow = Math.min(1, progress * 1.5);

  return (
    <g>
      <line x1={x} y1={y + h} x2={x + w} y2={y + h} stroke={INK} strokeWidth={6} />
      {bars.map((b, idx) => {
        const bh = Math.max(20, (b.value / maxVal) * (h - 90) * grow);
        const bx = x + idx * gap + (gap - barW) * 0.5;
        const by = y + h - bh;
        const col = b.color || (idx === bars.length - 1 ? "#22C55E" : "#94A3B8");
        const num = Math.round(b.value * grow);
        return (
          <g key={idx}>
            <rect x={bx} y={by} width={barW} height={bh} rx={6} fill={col} stroke={INK} strokeWidth={5} />
            <text x={bx + barW / 2} y={by - 18} textAnchor="middle" fill={col} stroke={INK} strokeWidth={8} paintOrder="stroke" fontFamily={MARKER_FONT} fontSize={46}>
              {prefix}{num.toLocaleString("en-US")}{suffix}
            </text>
            <text x={bx + barW / 2} y={y + h + 46} textAnchor="middle" fill="#1E293B" fontFamily={UI_FONT} fontSize={28} fontWeight={700}>
              {b.label}
            </text>
          </g>
        );
      })}
      {multiplierTag && progress > 0.45 && (
        <g transform={`translate(${x + w - 90} ${y + 110}) rotate(-10)`}>
          <rect x={-72} y={-44} width={144} height={84} rx={10} fill="#FACC15" stroke={INK} strokeWidth={5} />
          <text x={0} y={14} textAnchor="middle" fill={INK} fontFamily={MARKER_FONT} fontSize={48}>
            {multiplierTag}
          </text>
        </g>
      )}
    </g>
  );
};

export const PieChart2D: React.FC<{
  x: number;
  y: number;
  radius?: number;
  slicePct: number;
  label: string;
  color?: string;
  progress: number;
}> = ({ x, y, radius = 230, slicePct, label, color = "#F59E0B", progress }) => {
  const pull = Math.min(1, progress * 1.7) * 48;
  const angle = (Math.min(90, Math.max(5, slicePct)) / 100) * Math.PI * 2;
  const x2 = Math.cos(angle) * radius;
  const y2 = Math.sin(angle) * radius;
  const shownPct = Math.round(slicePct * Math.min(1, progress * 1.5));

  return (
    <g transform={`translate(${x} ${y})`}>
      <ellipse cx={0} cy={28} rx={radius} ry={radius * 0.65} fill="#94A3B8" stroke={INK} strokeWidth={5} />
      <ellipse cx={0} cy={0} rx={radius} ry={radius * 0.65} fill="#E5E7EB" stroke={INK} strokeWidth={5} />
      <g transform={`translate(${pull * 0.7} ${-pull * 0.55})`}>
        <path
          d={`M 0 0 L ${radius} 0 A ${radius} ${radius * 0.65} 0 0 1 ${x2.toFixed(1)} ${(y2 * 0.65).toFixed(1)} Z`}
          fill={color}
          stroke={INK}
          strokeWidth={5}
        />
      </g>
      <text x={radius * 0.45} y={-radius * 0.72} textAnchor="middle" fill={color} stroke={INK} strokeWidth={9} paintOrder="stroke" fontFamily={MARKER_FONT} fontSize={74}>
        {shownPct}%
      </text>
      <text x={radius * 0.45} y={-radius * 0.45} textAnchor="middle" fill="#1E293B" fontFamily={UI_FONT} fontSize={30} fontWeight={700}>
        {label}
      </text>
    </g>
  );
};

export const BalanceScale2D: React.FC<{
  x: number;
  y: number;
  leftLabel: string;
  rightLabel: string;
  tiltDeg?: number;
  leftColor?: string;
  rightColor?: string;
  progress: number;
}> = ({ x, y, leftLabel, rightLabel, tiltDeg = 16, leftColor = "#22C55E", rightColor = "#EF4444", progress }) => {
  const ease = Math.min(1, progress * 1.6);
  const angle = tiltDeg * ease;
  const rad = (angle * Math.PI) / 180;
  const arm = 270;
  const lx = -Math.cos(rad) * arm;
  const ly = -Math.sin(rad) * arm;
  const rx = Math.cos(rad) * arm;
  const ry = Math.sin(rad) * arm;

  return (
    <g transform={`translate(${x} ${y})`}>
      <rect x={-90} y={210} width={180} height={30} rx={8} fill="#64748B" stroke={INK} strokeWidth={5} />
      <rect x={-14} y={-20} width={28} height={235} fill="#94A3B8" stroke={INK} strokeWidth={5} />
      <line x1={lx} y1={ly} x2={rx} y2={ry} stroke="#F59E0B" strokeWidth={16} strokeLinecap="round" />
      <circle cx={0} cy={0} r={22} fill="#FACC15" stroke={INK} strokeWidth={5} />
      {/* Left Pan */}
      <g transform={`translate(${lx} ${ly})`}>
        <line x1={0} y1={0} x2={-75} y2={135} stroke={INK} strokeWidth={4} />
        <line x1={0} y1={0} x2={75} y2={135} stroke={INK} strokeWidth={4} />
        <rect x={-105} y={135} width={210} height={24} rx={8} fill="#F59E0B" stroke={INK} strokeWidth={4} />
        <rect x={-85} y={70} width={170} height={65} rx={8} fill={leftColor} stroke={INK} strokeWidth={4} />
        <text x={0} y={112} textAnchor="middle" fill="#FFFFFF" fontFamily={UI_FONT} fontSize={26} fontWeight={700}>{leftLabel}</text>
      </g>
      {/* Right Pan */}
      <g transform={`translate(${rx} ${ry})`}>
        <line x1={0} y1={0} x2={-75} y2={135} stroke={INK} strokeWidth={4} />
        <line x1={0} y1={0} x2={75} y2={135} stroke={INK} strokeWidth={4} />
        <rect x={-105} y={135} width={210} height={24} rx={8} fill="#F59E0B" stroke={INK} strokeWidth={4} />
        <rect x={-95} y={42} width={190} height={93} rx={8} fill={rightColor} stroke={INK} strokeWidth={4} />
        <text x={0} y={98} textAnchor="middle" fill="#FFFFFF" fontFamily={UI_FONT} fontSize={26} fontWeight={700}>{rightLabel}</text>
      </g>
    </g>
  );
};

export const ConveyorBelt2D: React.FC<{
  x: number;
  y: number;
  w?: number;
  items: string[];
  accentHex?: string;
  frame: number;
  progress: number;
}> = ({ x, y, w = 1320, items, accentHex = "#22C55E", frame, progress }) => {
  const shift = (frame * 5) % 240;
  const stampDip = Math.abs(Math.sin(frame * 0.12)) * 45;

  return (
    <g transform={`translate(${x} ${y})`}>
      {/* Overhead Robotic Arm Stamping */}
      <g transform={`translate(${w * 0.5} ${-160 + stampDip})`}>
        <rect x={-26} y={-140} width={52} height={140} fill="#F97316" stroke={INK} strokeWidth={5} />
        <rect x={-64} y={0} width={128} height={30} rx={8} fill="#334155" stroke={INK} strokeWidth={5} />
      </g>
      {/* Belt Track */}
      <rect x={0} y={0} width={w} height={64} rx={32} fill="#374151" stroke={INK} strokeWidth={6} />
      {Array.from({ length: 6 }).map((_, ri) => (
        <circle key={ri} cx={60 + (ri / 5) * (w - 120)} cy={32} r={20} fill="#94A3B8" stroke={INK} strokeWidth={4} />
      ))}
      {/* Moving Items */}
      {items.map((lbl, idx) => {
        const ix = ((idx * 340 + shift) % (w - 160)) + 40;
        return (
          <g key={idx} transform={`translate(${ix} -96)`}>
            <rect x={0} y={0} width={140} height={96} rx={12} fill={accentHex} stroke={INK} strokeWidth={5} />
            <text x={70} y={60} textAnchor="middle" fill="#FFFFFF" fontFamily={MARKER_FONT} fontSize={34}>
              {lbl}
            </text>
          </g>
        );
      })}
      <line x1={0} y1={-4} x2={w} y2={-4} stroke="#FACC15" strokeWidth={8} strokeDasharray="24 18" strokeDashoffset={-shift} />
      <rect x={0} y={64} width={w} height={18} fill="#1F2937" opacity={0.4 + progress * 0.1} />
    </g>
  );
};

export const WorldMapArc2D: React.FC<{
  x: number;
  y: number;
  w?: number;
  h?: number;
  startPct?: [number, number];
  endPct?: [number, number];
  accentHex?: string;
  zoomLabel?: string;
  progress: number;
  frame: number;
}> = ({
  x,
  y,
  w = 1280,
  h = 640,
  startPct = [24, 48],
  endPct = [78, 52],
  accentHex = "#EF4444",
  zoomLabel = "GLOBAL LINK",
  progress,
  frame,
}) => {
  const sx = x + (startPct[0] / 100) * w;
  const sy = y + (startPct[1] / 100) * h;
  const ex = x + (endPct[0] / 100) * w;
  const ey = y + (endPct[1] / 100) * h;
  const mx = (sx + ex) * 0.5;
  const my = Math.min(sy, ey) - h * 0.25;
  const d = `M ${sx} ${sy} Q ${mx} ${my} ${ex} ${ey}`;
  const arcLen = w * 1.2;
  const draw = Math.min(1, progress * 1.4);

  return (
    <g>
      <rect x={x} y={y} width={w} height={h} rx={18} fill="#7DA8BE" stroke={INK} strokeWidth={6} />
      {/* Stylized Vector Continents */}
      <polygon points={`${x+100},${y+120} ${x+380},${y+100} ${x+430},${y+290} ${x+260},${y+480} ${x+140},${y+310}`} fill="#D6C49D" stroke={INK} strokeWidth={4} />
      <polygon points={`${x+560},${y+90} ${x+1120},${y+80} ${x+1180},${y+340} ${x+920},${y+420} ${x+620},${y+490} ${x+540},${y+250}`} fill="#D6C49D" stroke={INK} strokeWidth={4} />
      {/* Animated Curved Route */}
      <path d={d} fill="none" stroke={accentHex} strokeWidth={8} strokeDasharray="18 12" strokeDashoffset={-frame * 3} opacity={0.95} />
      <circle cx={sx} cy={sy} r={14} fill="#FACC15" stroke={INK} strokeWidth={4} />
      <circle cx={ex} cy={ey} r={16 * (0.7 + 0.4 * draw)} fill={accentHex} stroke={INK} strokeWidth={4} />
      {/* Magnifying Glass Loupe */}
      {progress > 0.3 && (
        <g transform={`translate(${ex - 30} ${ey - 20})`}>
          <circle cx={0} cy={0} r={96} fill="#FFFFFF" fillOpacity={0.22} stroke={INK} strokeWidth={8} />
          <line x1={68} y1={68} x2={132} y2={132} stroke={INK} strokeWidth={16} strokeLinecap="round" />
          <text x={0} y={-118} textAnchor="middle" fill="#FFFFFF" stroke={INK} strokeWidth={8} paintOrder="stroke" fontFamily={MARKER_FONT} fontSize={36}>
            {zoomLabel}
          </text>
        </g>
      )}
    </g>
  );
};

export const QuoteHighlight2D: React.FC<{
  x: number;
  y: number;
  w?: number;
  sourceTag: string;
  quoteBefore: string;
  highlightText: string;
  quoteAfter?: string;
  markStamp?: string;
  progress: number;
}> = ({
  x,
  y,
  w = 1160,
  sourceTag,
  quoteBefore,
  highlightText,
  quoteAfter = "",
  markStamp = "?!",
  progress,
}) => {
  const hiFrac = Math.max(0, Math.min(1, (progress - 0.15) / 0.35));
  const circleShow = progress > 0.48;

  return (
    <g transform={`translate(${x} ${y})`}>
      <rect x={0} y={0} width={w} height={460} rx={18} fill="#FFFFFF" stroke={INK} strokeWidth={6} />
      <rect x={0} y={0} width={w} height={74} rx={14} fill="#1E293B" stroke={INK} strokeWidth={5} />
      <circle cx={42} cy={37} r={14} fill="#22C55E" />
      <text x={78} y={48} fill="#FFFFFF" fontFamily={UI_FONT} fontSize={30} fontWeight={700}>
        {sourceTag}
      </text>
      <text x={70} y={175} fill="#475569" fontFamily={HAND_FONT} fontSize={54}>
        {quoteBefore}
      </text>
      {/* Animated Yellow Highlighter Sweep */}
      <rect x={64} y={208} width={Math.min(w - 140, highlightText.length * 29) * hiFrac} height={68} rx={8} fill="#FDE047" />
      <text x={70} y={260} fill={INK} fontFamily={HAND_FONT} fontSize={62} fontWeight={700}>
        {highlightText}
      </text>
      {quoteAfter && (
        <text x={70} y={355} fill="#475569" fontFamily={HAND_FONT} fontSize={50}>
          {quoteAfter}
        </text>
      )}
      {circleShow && (
        <g>
          <ellipse cx={260} cy={240} rx={220} ry={58} fill="none" stroke="#EF4444" strokeWidth={8} transform="rotate(-2 260 240)" />
          <text x={w - 120} y={180} fill="#EF4444" fontFamily={MARKER_FONT} fontSize={86} transform={`rotate(12 ${w - 120} 180)`}>
            {markStamp}
          </text>
        </g>
      )}
    </g>
  );
};

export const CalendarFlip2D: React.FC<{
  x: number;
  y: number;
  pages: { month: string; day: string }[];
  progress: number;
}> = ({ x, y, pages, progress }) => {
  const idx = Math.min(pages.length - 1, Math.floor(progress * pages.length));
  const cur = pages[idx] || { month: "NOV", day: "30" };
  return (
    <g transform={`translate(${x} ${y})`}>
      <rect x={-140} y={-160} width={280} height={310} rx={14} fill="#FFFFFF" stroke={INK} strokeWidth={6} />
      <rect x={-140} y={-160} width={280} height={84} rx={12} fill="#DC2626" stroke={INK} strokeWidth={6} />
      <text x={0} y={-100} textAnchor="middle" fill="#FFFFFF" fontFamily={MARKER_FONT} fontSize={50}>{cur.month}</text>
      <text x={0} y={74} textAnchor="middle" fill={INK} fontFamily={MARKER_FONT} fontSize={128}>{cur.day}</text>
      {progress > 0.65 && (
        <circle cx={0} cy={30} r={88} fill="none" stroke="#EF4444" strokeWidth={10} />
      )}
    </g>
  );
};

export const Stopwatch2D: React.FC<{
  x: number;
  y: number;
  radius?: number;
  maxSecLabel?: string;
  progress: number;
}> = ({ x, y, radius = 125, maxSecLabel = "6:00", progress }) => {
  const deg = progress * 360;
  return (
    <g transform={`translate(${x} ${y})`}>
      <rect x={-22} y={-radius - 32} width={44} height={32} rx={6} fill="#94A3B8" stroke={INK} strokeWidth={5} />
      <circle cx={0} cy={0} r={radius} fill="#F8FAFC" stroke={INK} strokeWidth={8} />
      <circle cx={0} cy={0} r={radius * 0.84} fill="none" stroke="#CBD5E1" strokeWidth={4} strokeDasharray="8 12" />
      <line x1={0} y1={0} x2={0} y2={-radius * 0.72} stroke="#EF4444" strokeWidth={8} strokeLinecap="round" transform={`rotate(${deg})`} />
      <circle cx={0} cy={0} r={12} fill={INK} />
      <text x={0} y={radius + 64} textAnchor="middle" fill="#1E293B" stroke="#FFFFFF" strokeWidth={8} paintOrder="stroke" fontFamily={MARKER_FONT} fontSize={48}>
        {maxSecLabel}
      </text>
    </g>
  );
};

export const SplitScreen3Panel: React.FC<{
  progress: number;
  panel1: React.ReactNode;
  panel2: React.ReactNode;
  panel3: React.ReactNode;
}> = ({ progress, panel1, panel2, panel3 }) => {
  const show2 = progress >= 0.25;
  const show3 = progress >= 0.52;
  return (
    <g>
      <g>{panel1}</g>
      {show2 && <g>{panel2}</g>}
      {show3 && <g>{panel3}</g>}
      <line x1={640} y1={0} x2={640} y2={1080} stroke={INK} strokeWidth={10} />
      <line x1={1280} y1={0} x2={1280} y2={1080} stroke={INK} strokeWidth={10} />
    </g>
  );
};

export const ReactorVessel2D: React.FC<{
  x: number;
  y: number;
  scale?: number;
  accentHex?: string;
  frame: number;
  progress: number;
}> = ({ x, y, scale = 1, accentHex = "#38BDF8", frame, progress }) => {
  const rodOffset = Math.sin(frame * 0.14) * 28;
  const lidLift = Math.min(1, progress * 1.5) * 40;
  return (
    <g transform={`translate(${x} ${y}) scale(${scale})`}>
      <path d="M -130 -60 Q -130 -230 0 -230 Q 130 -230 130 -60 L 130 160 L -130 160 Z" fill="#64748B" stroke={INK} strokeWidth={6} />
      {/* Cutaway Cherenkov Core Window */}
      <rect x={-90} y={-80} width={180} height={210} rx={16} fill="#0EA5E9" stroke={INK} strokeWidth={5} />
      <rect x={-76} y={-40} width={152} height={155} rx={10} fill={accentHex} opacity={0.75 + Math.sin(frame * 0.2) * 0.2} />
      {/* Oscillating Control Rods */}
      {[-42, 0, 42].map((rx, i) => (
        <rect key={i} x={rx - 10} y={-110 + rodOffset * (i % 2 === 0 ? 1 : -1)} width={20} height={140} rx={6} fill="#FACC15" stroke={INK} strokeWidth={4} />
      ))}
      <rect x={-148} y={-180 - lidLift} width={296} height={28} rx={8} fill="#475569" stroke={INK} strokeWidth={5} />
    </g>
  );
};

export const CoolingTower2D: React.FC<{
  x: number;
  y: number;
  scale?: number;
  accentHex?: string;
  frame: number;
}> = ({ x, y, scale = 1, accentHex = "#38BDF8", frame }) => {
  const puff = (frame * 2.1) % 120;
  return (
    <g transform={`translate(${x} ${y}) scale(${scale})`}>
      <polygon points="-130,170 -85,-140 85,-140 130,170" fill="#94A3B8" stroke={INK} strokeWidth={6} />
      <rect x={-92} y={80} width={184} height={74} rx={8} fill={accentHex} stroke={INK} strokeWidth={4} />
      {/* Rising Steam Clouds */}
      {[0, 40, 80].map((off, i) => {
        const py = -165 - ((puff + off) % 120);
        const op = 1 - ((puff + off) % 120) / 130;
        return <circle key={i} cx={-25 + i * 26} cy={py} r={34} fill="#F8FAFC" stroke={INK} strokeWidth={4} opacity={op} />;
      })}
    </g>
  );
};

export const ServerRack2D: React.FC<{
  x: number;
  y: number;
  scale?: number;
  accentHex?: string;
  frame: number;
}> = ({ x, y, scale = 1, accentHex = "#22D3EE", frame }) => (
  <g transform={`translate(${x} ${y}) scale(${scale})`}>
    <rect x={-105} y={-190} width={210} height={380} rx={12} fill="#1E293B" stroke={INK} strokeWidth={6} />
    {[-140, -80, -20, 40, 100].map((ry, i) => {
      const active = Math.sin(frame * 0.25 - i * 0.9) > -0.2;
      return (
        <g key={i}>
          <rect x={-82} y={ry} width={164} height={44} rx={6} fill="#334155" stroke={INK} strokeWidth={4} />
          <circle cx={-56} cy={ry + 22} r={8} fill={active ? accentHex : "#475569"} />
          <rect x={-28} y={ry + 15} width={86} height={14} rx={4} fill={active ? "#38BDF8" : "#475569"} />
        </g>
      );
    })}
  </g>
);

export const Microchip2D: React.FC<{
  x: number;
  y: number;
  scale?: number;
  color?: string;
  cracked?: boolean;
  overheating?: boolean;
  frame: number;
  progress: number;
}> = ({ x, y, scale = 1, color = "#22C55E", cracked = false, overheating = false, frame, progress }) => {
  const fillCol = overheating ? "#F97316" : color;
  const crackProg = Math.min(1, progress * 1.6);
  return (
    <g transform={`translate(${x} ${y}) scale(${scale})`}>
      {[-120, -60, 0, 60, 120].map((p, i) => (
        <React.Fragment key={i}>
          <rect x={p - 12} y={-188} width={24} height={36} fill="#FACC15" stroke={INK} strokeWidth={4} />
          <rect x={p - 12} y={152} width={24} height={36} fill="#FACC15" stroke={INK} strokeWidth={4} />
          <rect x={-188} y={p - 12} width={36} height={24} fill="#FACC15" stroke={INK} strokeWidth={4} />
          <rect x={152} y={p - 12} width={36} height={24} fill="#FACC15" stroke={INK} strokeWidth={4} />
        </React.Fragment>
      ))}
      <rect x={-154} y={-154} width={308} height={308} rx={20} fill="#14532D" stroke={INK} strokeWidth={7} />
      <rect x={-105} y={-105} width={210} height={210} rx={12} fill={fillCol} stroke={INK} strokeWidth={5} opacity={0.85 + Math.sin(frame * 0.25) * 0.15} />
      {cracked && (
        <path
          d="M 85 -85 L 25 -20 L 55 15 L -30 90"
          fill="none"
          stroke="#FEF08A"
          strokeWidth={9}
          strokeLinecap="round"
          strokeDasharray={300}
          strokeDashoffset={300 * (1 - crackProg)}
        />
      )}
    </g>
  );
};

export const PowerPylon2D: React.FC<{
  x: number;
  y: number;
  scale?: number;
  accentHex?: string;
  frame: number;
}> = ({ x, y, scale = 1, accentHex = "#F59E0B", frame }) => {
  const pulse = 0.6 + 0.4 * Math.sin(frame * 0.3);
  return (
    <g transform={`translate(${x} ${y}) scale(${scale})`}>
      <polygon points="-90,190 -24,-190 24,-190 90,190" fill="none" stroke={INK} strokeWidth={8} />
      <line x1={-125} y1={-90} x2={125} y2={-90} stroke={INK} strokeWidth={10} strokeLinecap="round" />
      <line x1={-95} y1={-150} x2={95} y2={-150} stroke={INK} strokeWidth={10} strokeLinecap="round" />
      <circle cx={-120} cy={-78} r={14} fill={accentHex} stroke={INK} strokeWidth={4} opacity={pulse} />
      <circle cx={120} cy={-78} r={14} fill={accentHex} stroke={INK} strokeWidth={4} opacity={pulse} />
    </g>
  );
};

export const BatteryBank2D: React.FC<{
  x: number;
  y: number;
  scale?: number;
  accentHex?: string;
  frame: number;
  progress: number;
}> = ({ x, y, scale = 1, accentHex = "#10B981", frame, progress }) => {
  const lvl = Math.max(0.25, Math.min(1, progress + 0.15 * Math.sin(frame * 0.12)));
  return (
    <g transform={`translate(${x} ${y}) scale(${scale})`}>
      <rect x={-140} y={-110} width={280} height={220} rx={16} fill="#E2E8F0" stroke={INK} strokeWidth={6} />
      <rect x={-105} y={-72} width={140} height={144} rx={8} fill="#334155" stroke={INK} strokeWidth={4} />
      <rect x={58} y={76 - lvl * 144} width={44} height={lvl * 144} rx={6} fill={accentHex} stroke={INK} strokeWidth={4} />
    </g>
  );
};

export const AnimatedPipe2D: React.FC<{
  d: string;
  color?: string;
  fluidColor?: string;
  strokeWidth?: number;
  frame: number;
}> = ({ d, color = "#475569", fluidColor = "#22D3EE", strokeWidth = 28, frame }) => (
  <g>
    <path d={d} fill="none" stroke={INK} strokeWidth={strokeWidth + 10} strokeLinecap="round" strokeLinejoin="round" />
    <path d={d} fill="none" stroke={color} strokeWidth={strokeWidth} strokeLinecap="round" strokeLinejoin="round" />
    <path
      d={d}
      fill="none"
      stroke={fluidColor}
      strokeWidth={strokeWidth * 0.45}
      strokeDasharray="24 22"
      strokeDashoffset={-frame * 5}
      strokeLinecap="round"
    />
  </g>
);

export const ExplosionBurst2D: React.FC<{
  x: number;
  y: number;
  color?: string;
  triggerSec: number;
  localTime: number;
}> = ({ x, y, color = "#FACC15", triggerSec, localTime }) => {
  const dt = localTime - triggerSec;
  if (dt < 0 || dt > 0.65) return null;
  const s = 0.4 + (dt / 0.65) * 1.4;
  const op = 1 - dt / 0.65;
  return (
    <g transform={`translate(${x} ${y}) scale(${s})`} opacity={op}>
      <polygon
        points="0,-90 22,-28 86,-42 36,10 82,66 14,38 -20,92 -28,26 -90,12 -32,-22"
        fill={color}
        stroke={INK}
        strokeWidth={5}
      />
    </g>
  );
};
'''

FILES["src/components/CartoonStage2D.tsx"] = r'''
import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { SCENE_REGISTRY } from "../generated/SceneRegistry";
import type { CartoonPlan, Transition2D } from "../types";

function computeTransitionTransform(
  transition: Transition2D,
  enterProg: number,
  width: number,
  height: number
): { transform?: string; opacity: number } {
  const p = Math.max(0, Math.min(1, enterProg));
  const ease = p * p * (3 - 2 * p);

  switch (transition) {
    case "slide_left":
      return { transform: `translateX(${(1 - ease) * width}px)`, opacity: 1 };
    case "slide_up":
      return { transform: `translateY(${(1 - ease) * height}px)`, opacity: 1 };
    case "wipe_right":
      return { transform: `translateX(${-(1 - ease) * width}px)`, opacity: 1 };
    case "zoom_dissolve":
      return { transform: `scale(${0.92 + 0.08 * ease})`, opacity: ease };
    case "flash_cut":
    default:
      return { opacity: Math.min(1, p * 2.5) };
  }
}

export const CartoonStage2D: React.FC<{ plan: CartoonPlan }> = ({ plan }) => {
  const frame = useCurrentFrame();
  const { width, height, fps } = useVideoConfig();
  const tSec = frame / fps;
  const isVertical = height > width;
  const transSec = 0.28; // Snappy 8-frame human-editor transition

  let activeIdx = plan.scenes.findIndex((s) => tSec >= s.startSec && tSec <= s.endSec);
  if (activeIdx === -1) activeIdx = plan.scenes.length - 1;

  const activeScene = plan.scenes[activeIdx];
  const prevScene = activeIdx > 0 ? plan.scenes[activeIdx - 1] : null;
  if (!activeScene) return null;

  const timeIntoScene = tSec - activeScene.startSec;
  const inTransition = Boolean(prevScene && timeIntoScene < transSec);
  const enterProg = inTransition ? Math.max(0, Math.min(1, timeIntoScene / transSec)) : 1;

  const ActiveComp = SCENE_REGISTRY[activeScene.id];
  const PrevComp = prevScene ? SCENE_REGISTRY[prevScene.id] : null;

  const activeDur = Math.max(0.1, activeScene.endSec - activeScene.startSec);
  const activeProgress = Math.max(0, Math.min(1, timeIntoScene / activeDur));
  const activeStyle = inTransition
    ? computeTransitionTransform(activeScene.transition, enterProg, width, height)
    : { opacity: 1 };

  const flashOpacity =
    inTransition && activeScene.transition === "flash_cut"
      ? interpolate(enterProg, [0, 0.35, 1], [0.85, 0.4, 0], { extrapolateRight: "clamp" })
      : 0;

  return (
    <AbsoluteFill style={{ backgroundColor: "#05070B", overflow: "hidden" }}>
      {inTransition && prevScene && PrevComp && (
        <AbsoluteFill>
          <PrevComp
            frame={frame}
            localFrame={Math.max(0, frame - Math.round(prevScene.startSec * fps))}
            localTime={tSec - prevScene.startSec}
            durationSec={Math.max(0.1, prevScene.endSec - prevScene.startSec)}
            progress={1}
            peakTimes={prevScene.localPeakTimes}
            accentHex={prevScene.accentHex}
            backdropTheme={prevScene.backdropTheme}
            cameraMove={prevScene.cameraMove}
            isVertical={isVertical}
          />
        </AbsoluteFill>
      )}

      {ActiveComp && (
        <AbsoluteFill style={activeStyle}>
          <ActiveComp
            frame={frame}
            localFrame={Math.max(0, frame - Math.round(activeScene.startSec * fps))}
            localTime={timeIntoScene}
            durationSec={activeDur}
            progress={activeProgress}
            peakTimes={activeScene.localPeakTimes}
            accentHex={activeScene.accentHex}
            backdropTheme={activeScene.backdropTheme}
            cameraMove={activeScene.cameraMove}
            isVertical={isVertical}
          />
        </AbsoluteFill>
      )}

      {flashOpacity > 0 && (
        <AbsoluteFill style={{ backgroundColor: "#FFFFFF", opacity: flashOpacity, pointerEvents: "none" }} />
      )}
    </AbsoluteFill>
  );
};
'''

FILES["src/generated/scenes/Scene_01.tsx"] = r'''
import React from "react";
import {
  SceneBackdrop2D,
  Camera2D,
  CartoonCharacter2D,
  Microchip2D,
  InkCallout2D,
} from "../../components/CartoonKit2D";
import type { Scene2DProps } from "../../types";

export const Scene_01: React.FC<Scene2DProps> = (props) => {
  const { frame, localTime, progress, peakTimes, accentHex, backdropTheme, cameraMove, isVertical } = props;
  const vb = isVertical ? "0 0 1080 1920" : "0 0 1920 1080";
  return (
    <svg viewBox={vb} style={{ width: "100%", height: "100%", display: "block" }}>
      <SceneBackdrop2D theme={backdropTheme} frame={frame} accentHex={accentHex} />
      <Camera2D move={cameraMove} progress={progress} frame={frame} peakTimes={peakTimes} localTime={localTime}>
        <CartoonCharacter2D
          x={isVertical ? 330 : 540}
          y={isVertical ? 1120 : 690}
          scale={1.35}
          variant="ceo"
          mood="worried"
          pose="hold_up"
          glasses={true}
          sweatDrop={true}
          frame={frame}
        />
        <Microchip2D
          x={isVertical ? 650 : 1220}
          y={isVertical ? 760 : 530}
          scale={1.45}
          color={accentHex}
          cracked={true}
          frame={frame}
          progress={progress}
        />
        <InkCallout2D
          x={isVertical ? 540 : 1480}
          y={isVertical ? 320 : 210}
          text="$100B"
          color="#EF4444"
          fontSize={86}
          localTime={localTime}
          delaySec={0.2}
        />
      </Camera2D>
    </svg>
  );
};
'''

FILES["src/generated/SceneRegistry.ts"] = r'''
import type React from "react";
import type { Scene2DProps } from "../types";
import { Scene_01 } from "./scenes/Scene_01";

export const SCENE_REGISTRY: Record<string, React.FC<Scene2DProps>> = {
  scene_01: Scene_01,
};
'''

FILES["src/generated/ScenesData.ts"] = r'''
import type { CartoonPlan } from "../types";

export const SCENE_PLAN: CartoonPlan = {
  channel: "InfraVerse2D",
  fps: 30,
  width: 1920,
  height: 1080,
  totalDurationSec: 6,
  hasAudio: false,
  bpm: 104,
  emphasisPeaksSec: [0.4, 3.2],
  scenes: [
    {
      id: "scene_01",
      componentName: "Scene_01",
      visualConcept: "Baseline 2D Cartoon Scene",
      visualSpec: "Character holding cracking chip on night mountains",
      titleText: "",
      backdropTheme: "night_mountains",
      cameraMove: "push_in",
      transition: "flash_cut",
      sfx: "sub_impact",
      accentHex: "#22C55E",
      startSec: 0,
      endSec: 6,
      localPeakTimes: [0.4, 3.2],
    },
  ],
};
'''

FILES["src/generated/GeneratedTimeline.tsx"] = r'''
import React from "react";
import { AbsoluteFill } from "remotion";
import { CartoonStage2D } from "../components/CartoonStage2D";
import { SCENE_PLAN } from "./ScenesData";

export const GENERATED_TOTAL_FRAMES = 180;

export const GeneratedTimeline: React.FC = () => {
  return (
    <AbsoluteFill>
      <CartoonStage2D plan={SCENE_PLAN} />
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
    <AbsoluteFill style={{ backgroundColor: "#05070B" }}>
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
      include_bgm:
        description: "Include auto background music? (false = pure voice + SFX so you can add YT Audio Library music)"
        required: false
        default: "true"
        type: choice
        options:
          - "true"
          - "false"
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

      - name: Step 1 - Audio Clean & Word-Level Whisper Sync
        if: steps.check_input.outputs.has_input == 'true'
        env:
          INPUT_FOLDER: "input"
          TRIM_SILENCE: ${{ github.event.inputs.trim_silence || 'false' }}
          WHISPER_MODEL: ${{ github.event.inputs.whisper_model || 'small' }}
          PREVIEW_SECONDS: ${{ github.event.inputs.preview_seconds || '0' }}
        run: |
          python scripts/analyze_audio.py

      - name: Step 2 - Gemini 2D Cartoon Storyboard, Scene Illustrator & Self-Healer
        if: steps.check_input.outputs.has_input == 'true'
        env:
          INPUT_FOLDER: "input"
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
          QUALITY_PRESET: ${{ github.event.inputs.quality_preset || '1080p_30fps' }}
          VIDEO_FORMAT: "long_16_9"
        run: |
          python scripts/generate_scenes.py

      - name: Step 3 - Audit Zero Repetition & Continuous Flow
        if: steps.check_input.outputs.has_input == 'true'
        run: |
          python scripts/validate_scenes.py

      - name: Step 4 - Synthesize & Sync SFX + Underscore Audio
        if: steps.check_input.outputs.has_input == 'true'
        env:
          INCLUDE_BGM: ${{ github.event.inputs.include_bgm || 'true' }}
        run: |
          python scripts/mix_audio.py

      - name: Step 5 - Frame 0 Smoke Test & Bundle Once
        if: steps.check_input.outputs.has_input == 'true'
        run: |
          npx remotion still src/index.ts Main work/frame0_smoke.png --frame=0
          npx remotion bundle src/index.ts --public-dir public --out-dir build_bundle

      - name: Step 6 - Plan Adaptive Parallel Workers (1 / 4 / 6)
        id: chunk_plan
        if: steps.check_input.outputs.has_input == 'true'
        env:
          FORCE_WORKERS: ${{ github.event.inputs.force_workers || 'auto' }}
        run: |
          python scripts/plan_chunks.py

      - name: Upload Prepared Bundle & Audio
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
    timeout-minutes: 60
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

      - name: Render 2D Cartoon Chunk ${{ matrix.chunk.idx }}
        run: |
          mkdir -p out
          npx remotion render build_bundle Main out/chunk_${{ matrix.chunk.idx }}.mp4 \
            --frames=${{ matrix.chunk.start }}-${{ matrix.chunk.end }} \
            --muted \
            --concurrency=3 \
            --codec=h264 \
            --pixel-format=yuv420p \
            --crf=21 \
            --x264-preset=veryfast \
            --image-format=jpeg \
            --jpeg-quality=92

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

      - name: Join Chunks + Master Audio
        env:
          VIDEO_FORMAT: "long_16_9"
        run: |
          python scripts/stitch_chunks.py

      - name: Upload Final 16:9 2D Video
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
      include_bgm:
        description: "Include auto background music?"
        required: false
        default: "true"
        type: choice
        options:
          - "true"
          - "false"
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

      - name: Step 1 - Clean Short Audio & Word Sync
        if: steps.check_input.outputs.has_input == 'true'
        env:
          INPUT_FOLDER: "input_short"
          TRIM_SILENCE: ${{ github.event.inputs.trim_silence || 'false' }}
          WHISPER_MODEL: ${{ github.event.inputs.whisper_model || 'small' }}
          PREVIEW_SECONDS: "0"
        run: |
          python scripts/analyze_audio.py

      - name: Step 2 - Gemini Vertical 9:16 2D Cartoon Illustrator
        if: steps.check_input.outputs.has_input == 'true'
        env:
          INPUT_FOLDER: "input_short"
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
          VIDEO_FORMAT: "short_9_16"
        run: |
          python scripts/generate_scenes.py

      - name: Step 3 - Audit Zero Repetition & Continuous Flow
        if: steps.check_input.outputs.has_input == 'true'
        run: |
          python scripts/validate_scenes.py

      - name: Step 4 - Synthesize & Sync SFX + Underscore Audio
        if: steps.check_input.outputs.has_input == 'true'
        env:
          INCLUDE_BGM: ${{ github.event.inputs.include_bgm || 'true' }}
        run: |
          python scripts/mix_audio.py

      - name: Step 5 - Frame 0 Smoke Test & Bundle Once
        if: steps.check_input.outputs.has_input == 'true'
        run: |
          npx remotion still src/index.ts Main work/frame0_smoke.png --frame=0
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

      - name: Render Vertical 9:16 2D Chunk ${{ matrix.chunk.idx }}
        run: |
          mkdir -p out
          npx remotion render build_bundle Main out/chunk_${{ matrix.chunk.idx }}.mp4 \
            --frames=${{ matrix.chunk.start }}-${{ matrix.chunk.end }} \
            --muted \
            --concurrency=3 \
            --codec=h264 \
            --pixel-format=yuv420p \
            --crf=21 \
            --x264-preset=veryfast \
            --image-format=jpeg \
            --jpeg-quality=92

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

      - name: Join Short Video + Master Audio
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
        git("commit", "-m", "Upgrade to v4.0: Video-1 2D Cartoon Style + Characters + Switchable Environments")
    if git("push", check=False).returncode != 0:
        git("push", "-u", "origin", "HEAD")
    print("\n[setup_factory] SUCCESS! v4.0 Video-1 2D Cartoon Factory is live on GitHub.")


if __name__ == "__main__":
    write_all_files()
    try:
        run_git_push()
    except subprocess.CalledProcessError as exc:
        print(f"\n[setup_factory] Git error ({exc}).")
        sys.exit(exc.returncode)

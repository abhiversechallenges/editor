#!/usr/bin/env python3
"""
InfraVerse Unlimited Dynamic 3D Factory (v2.2).
Two effortless folders:
  - input/        -> Automatic 16:9 Full HD (1920x1080, 30fps) using up to 6 parallel workers
  - input_short/  -> Automatic 9:16 Full HD Vertical (1080x1920, 30fps) matching your exact
                     X-second custom voiceover + custom look & elements description
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
  "version": "2.2.0",
  "private": true,
  "description": "Unlimited dynamic continuous 3D documentary & custom Shorts factory",
  "scripts": {
    "dev": "remotion studio src/index.ts",
    "build": "remotion bundle src/index.ts --public-dir public --out-dir build_bundle",
    "typecheck": "tsc --noEmit"
  },
  "dependencies": {
    "@react-three/drei": "9.120.4",
    "@react-three/fiber": "8.17.10",
    "@remotion/cli": "4.0.543",
    "@remotion/three": "4.0.543",
    "react": "18.3.1",
    "react-dom": "18.3.1",
    "remotion": "4.0.543",
    "three": "0.170.0"
  },
  "devDependencies": {
    "@types/react": "18.3.12",
    "@types/react-dom": "18.3.12",
    "@types/three": "0.170.0",
    "typescript": "5.6.3"
  }
}
'''

FILES["requirements.txt"] = r'''
google-genai>=1.49.0
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
Config.setJpegQuality(88);
Config.setOffthreadVideoCacheSizeInBytes(1024 * 1024 * 1024);
Config.setCodec("h264");
Config.setPixelFormat("yuv420p");
'''

FILES["input/visuals_EXAMPLE.txt"] = r'''
# Upload your long voiceover.mp3 + visuals.txt inside input/ for a 16:9 (1920x1080) video!
# Describe the look (colors, lighting mood) and the exact elements/cutaways you want.

Example:
Look & Mood: Deep obsidian dark studio with glowing cyan and warm amber highlights.
- Opening: Start wide outside a massive AI data center campus; smoothly lift the roof off and dive into a glowing server rack aisle.
- Next: Pull a single GPU blade out in exploded view showing copper heatpipes and 8 glowing GPU chips.
- Next: Zoom into a silicon die overheating fiery red with rising heat plumes, then clamp a dual-loop cold plate turning hot orange fluid into cyan streams.
- Next: Follow pipes outside to cutaway hyperbolic cooling towers spinning fans with rising vapor clouds.
'''

FILES["input_short/visuals_EXAMPLE.txt"] = r'''
# Upload your X-second Short voiceover.mp3 + visuals.txt inside input_short/ for a 9:16 (1080x1920) Short!
# Your FULL uploaded Short voiceover (with your custom hook) is used untouched from start to finish.

Example:
Look & Mood: High-contrast dark nuclear steel aesthetic with glowing Cherenkov blue and electric amber accents.
- Hook (first 4s): Fast dramatic orbit around a vertical Small Modular Nuclear Reactor steel dome splitting open to reveal the glowing blue core inside.
- Middle: Dive vertically down along oscillating uranium fuel rods and upward-streaming coolant pipes driving a spinning multi-stage turbine tower.
- Climax & Ending: Pull out into glowing high-voltage transmission pylons feeding bright energy pulses directly into a towering AI server stack.
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

PRO_MODEL_CHAIN = [
    "gemini-2.5-pro",
    "gemini-2.5-flash",
    "gemini-3.8-flash",
    "gemini-3.5-flash",
]

FLASH_MODEL_CHAIN = [
    "gemini-2.5-flash",
    "gemini-3.8-flash",
    "gemini-3.5-flash",
    "gemini-2.5-pro",
]


def get_client() -> genai.Client:
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError(
            "Missing GEMINI_API_KEY secret. Add it in GitHub Repo -> Settings -> Secrets -> Actions."
        )
    return genai.Client(api_key=api_key)


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
    max_output_tokens: int = 32768,
    temperature: float = 0.4,
) -> str:
    models = PRO_MODEL_CHAIN if role == "pro" else FLASH_MODEL_CHAIN
    config_kwargs: dict[str, Any] = {
        "temperature": temperature,
        "max_output_tokens": max_output_tokens,
    }
    if json_mode:
        config_kwargs["response_mime_type"] = "application/json"

    config = types.GenerateContentConfig(**config_kwargs)

    last_error: Optional[Exception] = None
    for model_name in models:
        for attempt in range(4):
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=contents,
                    config=config,
                )
                text = response.text or ""
                if not text.strip():
                    raise RuntimeError(f"Empty response from {model_name}")
                return clean_json_text(text) if json_mode else text
            except APIError as exc:
                last_error = exc
                msg = str(exc).lower()
                if any(k in msg for k in ("404", "403", "not found", "permission", "restricted")):
                    print(f"[gemini_helper] {model_name} unavailable ({exc}); switching model...")
                    break
                wait_sec = 8 * (2 ** attempt)
                print(f"[gemini_helper] {model_name} rate/transient error ({exc}); retrying in {wait_sec}s...")
                time.sleep(wait_sec)
            except Exception as exc:
                last_error = exc
                wait_sec = 5 * (2 ** attempt)
                print(f"[gemini_helper] {model_name} error ({exc}); retrying in {wait_sec}s...")
                time.sleep(wait_sec)

    raise RuntimeError(f"All Gemini models failed. Last error: {last_error}")


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
            "AI supercluster, Nvidia GPU, NVLink, InfiniBand, liquid cooling, cold plate, "
            "data center, nuclear SMR, small modular reactor, substation, transformer, "
            "power grid, subsea fiber optic cable, megawatt, gigawatt, battery farm, blackout."
        ),
    )

    segments: List[Dict[str, Any]] = []
    for seg in segments_iter:
        segments.append(
            {
                "id": seg.id,
                "start": round(float(seg.start), 3),
                "end": round(float(seg.end), 3),
                "text": seg.text.strip(),
            }
        )

    return {
        "language": info.language,
        "duration_sec": round(float(info.duration), 3),
        "segments": segments,
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

    min_distance = int((2.2 * sr) / hop_length)
    peaks, _ = find_peaks(
        combined,
        height=float(np.percentile(combined, 70)),
        distance=max(1, min_distance),
        prominence=0.10,
    )
    peak_times = [round(float(librosa.frames_to_time(p, sr=sr, hop_length=hop_length)), 3) for p in peaks]

    tempo, _ = librosa.beat.beat_track(onset_envelope=onset_env, sr=sr, hop_length=hop_length)
    bpm_val = float(np.atleast_1d(tempo)[0]) if np.size(tempo) > 0 else 96.0
    if bpm_val < 70 or bpm_val > 135:
        bpm_val = 96.0

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
    print(f"[analyze_audio] Done: {beats['duration_sec']:.2f}s, {len(transcript['segments'])} segments.")


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
'''

FILES["scripts/validate_scenes.py"] = r'''
import json
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parent.parent
PLAN_PATH = ROOT / "work" / "scene_plan.json"
SCENES_DIR = ROOT / "src" / "generated" / "scenes"
TIMELINE_PATH = ROOT / "src" / "generated" / "GeneratedTimeline.tsx"

FORBIDDEN_MARKERS = ("<Text", "<Html", "Subtitle", "Caption", "Karaoke", "<Sequence")


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

        if len(sc.get("cameraWaypoints") or []) < 2:
            errors.append(f"{sc['id']} has fewer than 2 cameraWaypoints.")

        cname = sc.get("componentName")
        if not (SCENES_DIR / f"{cname}.tsx").exists():
            errors.append(f"Missing generated scene component: {cname}.tsx")

    return errors


def audit_source_files() -> List[str]:
    errors: List[str] = []
    files = list(SCENES_DIR.glob("Scene_*.tsx")) + [TIMELINE_PATH]
    for f in files:
        if not f.exists():
            continue
        txt = f.read_text(encoding="utf-8")
        for m in FORBIDDEN_MARKERS:
            if m in txt:
                errors.append(f"Forbidden token '{m}' found inside {f.name}")
    return errors


def main() -> None:
    if not PLAN_PATH.exists():
        raise SystemExit("Missing work/scene_plan.json")
    plan = json.loads(PLAN_PATH.read_text(encoding="utf-8"))
    errs = audit_plan(plan) + audit_source_files()
    if errs:
        raise SystemExit("[validate_scenes] FAILED:\n - " + "\n - ".join(errs))
    print(f"[validate_scenes] PASSED: {len(plan['scenes'])} unique continuous dynamic scenes.")


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
    n = int(1.10 * SAMPLE_RATE)
    t = np.arange(n) / SAMPLE_RATE
    env = np.sin(np.pi * t / 1.10) ** 1.8
    air = bandpass(rng.normal(0.0, 1.0, n), 160.0, 950.0) * env
    sub = np.sin(2.0 * np.pi * (54.0 - 16.0 * (t / 1.10)) * t) * env * 0.35
    sig = air * 0.65 + sub
    stereo = np.column_stack([sig, sig * 0.96])
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

    bgm_stereo = synthesize_documentary_bgm(n_samples, float(plan.get("bpm", 96.0)))
    mix = vo_stereo * 0.92 + bgm_stereo * duck_gain[:, None]

    swell = synthesize_glide_swell() * 0.14
    for sc in plan["scenes"][1:]:
        start_idx = max(0, int((float(sc["startSec"]) - 0.55) * SAMPLE_RATE))
        end_idx = min(n_samples, start_idx + len(swell))
        if end_idx > start_idx:
            mix[start_idx:end_idx] += swell[: end_idx - start_idx]

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

export interface CameraWaypoint {
  offset: V3;
  lookOffset: V3;
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
  cameraWaypoints: CameraWaypoint[];
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
  scenes: DocumentaryScene[];
}
'''

FILES["src/components/StudioKit.tsx"] = r'''
import React, { Component, Suspense, useMemo } from "react";
import { useGLTF } from "@react-three/drei";
import { staticFile } from "remotion";
import * as THREE from "three";
import type { V3 } from "../types";

const safeVec = (v?: V3, fallback: V3 = [0, 0, 0]): V3 =>
  Array.isArray(v) && v.length === 3 ? [Number(v[0]) || 0, Number(v[1]) || 0, Number(v[2]) || 0] : fallback;

const safeHex = (c?: string, fallback = "#334155"): string =>
  typeof c === "string" && c.trim() ? c.trim() : fallback;

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
}> = ({
  pos,
  rot,
  size = [1, 1, 1],
  color = "#334155",
  emissive,
  emissiveIntensity = 1.4,
  roughness = 0.42,
  metalness = 0.28,
  opacity = 1,
}) => (
  <mesh position={safeVec(pos)} rotation={safeVec(rot)}>
    <boxGeometry args={safeVec(size, [1, 1, 1])} />
    <meshStandardMaterial
      color={safeHex(color)}
      emissive={emissive ? safeHex(emissive) : "#000000"}
      emissiveIntensity={emissive ? emissiveIntensity : 0}
      roughness={roughness}
      metalness={metalness}
      transparent={opacity < 1}
      opacity={opacity}
    />
  </mesh>
);

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
  roughness = 0.38,
  metalness = 0.35,
}) => (
  <mesh position={safeVec(pos)} rotation={safeVec(rot)}>
    <cylinderGeometry
      args={[radiusTop, radiusBottom, height, segments, 1, openEnded, thetaStart, thetaLength]}
    />
    <meshStandardMaterial
      color={safeHex(color)}
      emissive={emissive ? safeHex(emissive) : "#000000"}
      emissiveIntensity={emissive ? emissiveIntensity : 0}
      roughness={roughness}
      metalness={metalness}
      side={doubleSide ? THREE.DoubleSide : THREE.FrontSide}
    />
  </mesh>
);

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
  metalness = 0.25,
}) => (
  <mesh position={safeVec(pos)} scale={safeVec(scale, [1, 1, 1])}>
    <sphereGeometry args={[radius, 18, 16]} />
    <meshStandardMaterial
      color={safeHex(color)}
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
      color={safeHex(color)}
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
}> = ({
  pos,
  rot,
  radius = 0.5,
  height = 1,
  segments = 20,
  color = "#475569",
  emissive,
  emissiveIntensity = 1.4,
}) => (
  <mesh position={safeVec(pos)} rotation={safeVec(rot)}>
    <coneGeometry args={[radius, height, segments]} />
    <meshStandardMaterial
      color={safeHex(color)}
      emissive={emissive ? safeHex(emissive) : "#000000"}
      emissiveIntensity={emissive ? emissiveIntensity : 0}
      roughness={0.4}
      metalness={0.3}
    />
  </mesh>
);

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
  tubeRadius = 0.06,
  tubeColor = "#1E293B",
  particleColor = "#22D3EE",
  particleSize = 0.11,
  count = 6,
  speed = 0.65,
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
  const t = (frame / 30) * speed;
  const safeCount = Math.max(1, Math.min(20, Math.round(count)));

  return (
    <group>
      <mesh>
        <tubeGeometry args={[curve, 36, tubeRadius, 10, false]} />
        <meshStandardMaterial color={safeHex(tubeColor)} roughness={0.35} metalness={0.3} />
      </mesh>
      {Array.from({ length: safeCount }).map((_, idx) => {
        const u = ((t + idx / safeCount) % 1 + 1) % 1;
        const pt = curve.getPoint(u);
        return (
          <mesh key={idx} position={[pt.x, pt.y, pt.z]}>
            <sphereGeometry args={[particleSize, 10, 10]} />
            <meshStandardMaterial
              color={safeHex(particleColor)}
              emissive={safeHex(particleColor)}
              emissiveIntensity={2.0}
            />
          </mesh>
        );
      })}
    </group>
  );
};

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
  spread = 0.9,
  height = 2.2,
  count = 10,
  size = 0.14,
  color = "#F97316",
  speed = 0.45,
  frame,
}) => {
  const o = safeVec(origin);
  const t = (frame / 30) * speed;
  const safeCount = Math.max(1, Math.min(24, Math.round(count)));

  return (
    <group>
      {Array.from({ length: safeCount }).map((_, i) => {
        const life = ((t + i / safeCount) % 1 + 1) % 1;
        const angle = i * 2.3 + t * 0.8;
        const r = 0.15 + life * spread;
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
  size = 0.1,
  color = "#22D3EE",
  speed = 0.8,
  tilt = [0, 0, 0],
  frame,
}) => {
  const t = (frame / 30) * speed;
  const safeCount = Math.max(1, Math.min(24, Math.round(count)));
  return (
    <group position={safeVec(center)} rotation={safeVec(tilt)}>
      {Array.from({ length: safeCount }).map((_, i) => {
        const a = t + (i / safeCount) * Math.PI * 2;
        return (
          <mesh key={i} position={[Math.cos(a) * radius, 0, Math.sin(a) * radius]}>
            <sphereGeometry args={[size, 10, 10]} />
            <meshStandardMaterial
              color={safeHex(color)}
              emissive={safeHex(color)}
              emissiveIntensity={1.9}
            />
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
  const dur = Math.max(0.1, scene.endSec - scene.startSec);
  const u = Math.max(0, Math.min(1, (tSec - scene.startSec) / dur));
  const wps = scene.cameraWaypoints;
  const segCount = Math.max(1, wps.length - 1);
  const scaled = u * segCount;
  const segIdx = Math.min(segCount - 1, Math.floor(scaled));
  const localT = smoothstep(0, 1, scaled - segIdx);

  const wpA = wps[segIdx];
  const wpB = wps[Math.min(wps.length - 1, segIdx + 1)];

  const driftX = Math.sin(frame * 0.014) * 0.16;
  const driftY = Math.cos(frame * 0.011) * 0.09;
  const pull = isVertical ? 1.16 : 1.0;

  return {
    pos: [
      scene.worldPos[0] + lerp(wpA.offset[0], wpB.offset[0], localT) * pull + driftX,
      scene.worldPos[1] + lerp(wpA.offset[1], wpB.offset[1], localT) + driftY,
      scene.worldPos[2] + lerp(wpA.offset[2], wpB.offset[2], localT) * pull,
    ],
    look: [
      scene.worldPos[0] + lerp(wpA.lookOffset[0], wpB.lookOffset[0], localT),
      scene.worldPos[1] + lerp(wpA.lookOffset[1], wpB.lookOffset[1], localT),
      scene.worldPos[2] + lerp(wpA.lookOffset[2], wpB.lookOffset[2], localT),
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
    return { camPos: [0, 2, 7], lookAt: [0, 0, 0], bgHex: "#08101E", accentHex: "#22D3EE" };
  }

  let activeIdx = scenes.findIndex((s) => tSec >= s.startSec && tSec <= s.endSec);
  if (activeIdx === -1) activeIdx = scenes.length - 1;

  const current = scenes[activeIdx];
  const currSample = sampleSceneCamera(current, tSec, frame, isVertical);
  const halfWin = isVertical ? 0.9 : 1.15;

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

const AmbientParticleField: React.FC<{
  camPos: [number, number, number];
  accentHex: string;
  frame: number;
}> = ({ camPos, accentHex, frame }) => {
  const seeds = useMemo(
    () =>
      Array.from({ length: 65 }).map((_, i) => ({
        x: ((i * 7.31) % 24) - 12,
        y: ((i * 5.17) % 14) - 7,
        z: ((i * 11.43) % 24) - 12,
        size: 0.024 + (i % 4) * 0.01,
      })),
    []
  );

  const wrap = (val: number, cam: number, span: number) => {
    const rel = (((val - cam) % span) + span) % span;
    return cam + rel - span / 2;
  };

  return (
    <group>
      {seeds.map((s, idx) => (
        <mesh
          key={idx}
          position={[
            wrap(s.x + frame * 0.008, camPos[0], 24),
            wrap(s.y + Math.sin(frame * 0.02 + idx) * 0.25, camPos[1], 14),
            wrap(s.z, camPos[2], 24),
          ]}
        >
          <sphereGeometry args={[s.size, 6, 6]} />
          <meshStandardMaterial color={accentHex} emissive={accentHex} emissiveIntensity={1.5} />
        </mesh>
      ))}
    </group>
  );
};

export const Continuous3DWorld: React.FC<{ plan: DocumentaryPlan }> = ({ plan }) => {
  const frame = useCurrentFrame();
  const { width, height, fps } = useVideoConfig();
  const tSec = frame / fps;
  const isVertical = height > width;

  const camState = computeContinuousCamera(plan, tSec, frame, isVertical);
  const visibleScenes = plan.scenes.filter(
    (s) => tSec >= s.startSec - 2.4 && tSec <= s.endSec + 2.4
  );

  return (
    <ThreeCanvas
      width={width}
      height={height}
      camera={{ fov: isVertical ? 52 : 40, near: 0.1, far: 45, position: camState.camPos }}
      gl={{ antialias: true, powerPreference: "high-performance" }}
    >
      <color attach="background" args={[camState.bgHex]} />
      <fog attach="fog" args={[camState.bgHex, 8.5, 19.5]} />

      <CameraController camPos={camState.camPos} lookAt={camState.lookAt} />

      <ambientLight intensity={0.7} />
      <directionalLight
        position={[camState.camPos[0] + 6, camState.camPos[1] + 9, camState.camPos[2] + 5]}
        intensity={1.7}
        color="#F8FAFC"
      />
      <pointLight
        position={[camState.lookAt[0] - 4, camState.lookAt[1] + 3, camState.lookAt[2] + 2]}
        intensity={1.45}
        color={camState.accentHex}
      />

      <AmbientParticleField camPos={camState.camPos} accentHex={camState.accentHex} frame={frame} />

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

FILES["src/generated/scenes/Scene_01.tsx"] = r'''
import React from "react";
import {
  MatteBox,
  MatteCylinder,
  RevealSlideGroup,
  SpinGroup,
  FlowStream,
} from "../../components/StudioKit";
import type { DynamicSceneProps } from "../../types";

export const Scene_01: React.FC<DynamicSceneProps> = ({ frame, progress, accentHex }) => {
  return (
    <group>
      <MatteBox pos={[0, -0.7, 0]} size={[5.4, 0.2, 3.8]} color="#141C2B" />
      <MatteBox pos={[0, 0.05, 0]} size={[3.6, 1.1, 2.2]} color="#243146" />
      <RevealSlideGroup startPos={[0, 0, 0]} endPos={[0, 1.8, 0]} progress={progress} startAt={0.2} endAt={0.65}>
        <MatteBox pos={[0, 0.65, 0]} size={[3.7, 0.14, 2.3]} color="#334155" />
        <SpinGroup pos={[-0.9, 0.8, 0]} axis="y" speed={4.0} frame={frame}>
          <MatteCylinder radiusTop={0.25} radiusBottom={0.25} height={0.12} color={accentHex} emissive={accentHex} />
        </SpinGroup>
        <SpinGroup pos={[0.9, 0.8, 0]} axis="y" speed={4.0} frame={frame}>
          <MatteCylinder radiusTop={0.25} radiusBottom={0.25} height={0.12} color={accentHex} emissive={accentHex} />
        </SpinGroup>
      </RevealSlideGroup>
      <FlowStream
        points={[[-2.6, -0.35, 0], [-0.9, -0.35, 0], [0.9, -0.35, 0], [2.6, -0.35, 0]]}
        tubeColor="#1E293B"
        particleColor={accentHex}
        count={6}
        speed={0.8}
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
  totalDurationSec: 10,
  hasAudio: false,
  bpm: 96,
  emphasisPeaksSec: [3, 7],
  scenes: [
    {
      id: "scene_01",
      componentName: "Scene_01",
      visualConcept: "Baseline AI Data Center Cutaway",
      visualSpec: "Data center cutaway roof lift with glowing fiber flows",
      startSec: 0,
      endSec: 10,
      worldPos: [0, 0, 0],
      bgHex: "#08101E",
      accentHex: "#22D3EE",
      cameraWaypoints: [
        { offset: [5.5, 3.0, 6.0], lookOffset: [0, 0.2, 0] },
        { offset: [0.5, 1.8, 4.2], lookOffset: [0, 0.1, 0] },
        { offset: [-3.5, 2.2, 4.8], lookOffset: [0, 0, 0] },
      ],
    },
  ],
};
'''

FILES["src/generated/GeneratedTimeline.tsx"] = r'''
import React from "react";
import { AbsoluteFill } from "remotion";
import { Continuous3DWorld } from "../components/Continuous3DWorld";
import { SCENE_PLAN } from "./ScenesData";

export const GENERATED_TOTAL_FRAMES = 300;

export const GeneratedTimeline: React.FC = () => {
  return (
    <AbsoluteFill>
      <Continuous3DWorld plan={SCENE_PLAN} />
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
    <AbsoluteFill style={{ backgroundColor: "#08101E" }}>
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

      - name: Step 1 - Audio Clean & Whisper Timestamps
        if: steps.check_input.outputs.has_input == 'true'
        env:
          INPUT_FOLDER: "input"
          TRIM_SILENCE: ${{ github.event.inputs.trim_silence || 'false' }}
          WHISPER_MODEL: ${{ github.event.inputs.whisper_model || 'small' }}
          PREVIEW_SECONDS: ${{ github.event.inputs.preview_seconds || '0' }}
        run: |
          python scripts/analyze_audio.py

      - name: Step 2 - Gemini Unlimited Dynamic 3D Scene Coder & Self-Healer
        if: steps.check_input.outputs.has_input == 'true'
        env:
          INPUT_FOLDER: "input"
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
          QUALITY_PRESET: ${{ github.event.inputs.quality_preset || '1080p_30fps' }}
          VIDEO_FORMAT: "long_16_9"
        run: |
          python scripts/generate_scenes.py

      - name: Step 3 - Validate Uniqueness, Zero Text & Zero Hard Cuts
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

      - name: Render Silent 3D Chunk ${{ matrix.chunk.idx }}
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
            --jpeg-quality=88 \
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

      - name: Step 1 - Clean Full X-Second Short Audio & Transcribe
        if: steps.check_input.outputs.has_input == 'true'
        env:
          INPUT_FOLDER: "input_short"
          TRIM_SILENCE: ${{ github.event.inputs.trim_silence || 'false' }}
          WHISPER_MODEL: ${{ github.event.inputs.whisper_model || 'small' }}
          PREVIEW_SECONDS: "0"
        run: |
          python scripts/analyze_audio.py

      - name: Step 2 - Gemini Vertical 9:16 3D Scene Coder & Self-Healer
        if: steps.check_input.outputs.has_input == 'true'
        env:
          INPUT_FOLDER: "input_short"
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
          VIDEO_FORMAT: "short_9_16"
        run: |
          python scripts/generate_scenes.py

      - name: Step 3 - Validate Uniqueness, Zero Text & Zero Hard Cuts
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

      - name: Render Vertical 9:16 Chunk ${{ matrix.chunk.idx }}
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
            --jpeg-quality=88 \
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
        git("commit", "-m", "Add dedicated 9:16 Shorts factory alongside 16:9 factory")
    if git("push", check=False).returncode != 0:
        git("push", "-u", "origin", "HEAD")
    print("\n[setup_factory] SUCCESS! Both 16:9 and 9:16 factories are live on GitHub.")


if __name__ == "__main__":
    write_all_files()
    try:
        run_git_push()
    except subprocess.CalledProcessError as exc:
        print(f"\n[setup_factory] Git error ({exc}).")
        sys.exit(exc.returncode)
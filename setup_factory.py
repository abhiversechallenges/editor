#!/usr/bin/env python3
"""
CoreToGrid 2D/2.5D Technical Blueprint Documentary Factory (v5.1).
Fixes & Upgrades:
  - True Gemini 4 Hydrogen (high thinking) + 3.8/3.6/3.5 Flash free-tier quota pacing
  - Multi-Provider Automatic Failover: Gemini -> OpenRouter (:free) -> Groq (Free)
  - TypeScript Self-Healer (`npx tsc --noEmit`) + Safe Blueprint Fallbacks
  - 20-Worker Hyper-Parallel GitHub Actions Matrix + 16GB Codespaces Studio
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
public/audio/*.wav
public/audio/sfx/*.mp3
public/audio/sfx/*.wav
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

FILES[".devcontainer/devcontainer.json"] = r'''
{
  "name": "CoreToGrid Cloud Studio (16GB)",
  "image": "mcr.microsoft.com/devcontainers/universal:linux",
  "hostRequirements": {
    "cpus": 4,
    "memory": "16gb"
  },
  "features": {
    "ghcr.io/devcontainers/features/node:1": {
      "version": "22"
    },
    "ghcr.io/devcontainers/features/python:1": {
      "version": "3.11"
    }
  },
  "postCreateCommand": "sudo apt-get update && sudo apt-get install -y ffmpeg libnss3 libasound2t64 libgbm1 || sudo apt-get install -y ffmpeg libnss3 libasound2 libgbm1; pip install -r requirements.txt && npm install --no-audit",
  "forwardPorts": [3000],
  "customizations": {
    "vscode": {
      "extensions": [
        "GoogleCloud.gemini-duet",
        "dbaeumer.vscode-eslint"
      ]
    }
  }
}
'''

FILES["SKILL_ANTIGRAVITY.md"] = r'''
# Antigravity Agent Skill: CoreToGrid Technical Blueprint Director

## Mission
Direct 2D/2.5D isometric CAD & X-ray blueprint documentaries on AI Silicon, 800kW Data Centers, and Power Grids.

## Execution Rules
- On a 4GB RAM laptop: NEVER run `npm install`, `npm run dev`, or `remotion render` locally. Write `input/visuals.txt`, place `input/voiceover.mp3`, and push to GitHub.
- Inside 16GB GitHub Codespaces: You can run `npm run dev` on port 3000 for live timeline inspection before pushing.
- Always commit `input/` only once per episode (pushing to `input/` auto-triggers the 20-worker GitHub Actions cloud render).
'''

FILES["package.json"] = r'''
{
  "name": "core-to-grid-visual-factory",
  "version": "5.1.0",
  "private": true,
  "description": "Technical blueprint explainer engine for AI hardware & energy infrastructure",
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
# CoreToGrid Technical Blueprint Visual Directive
# Themes: isometric_blueprint, xray_cutaway, substation_grid, cleanroom_fab,
#         thermal_flow, server_corridor, dark_industrial, black_title_card, split_3panel
- Scene 1 [isometric_blueprint]: 1-GW data center hall aerial schematic, Telemetry HUD showing "CAMPUS LOAD: 940 MW".
- Scene 2 [black_title_card]: "The Air Cooling Wall"
- Scene 3 [thermal_flow]: Microchannel cold plate cross-section, blue 32C inlet -> red 62C outlet coolant trace.
- Scene 4 [substation_grid]: 345 kV substation transformer stepdown feeding facility switchgear.
'''

FILES["input_short/visuals_EXAMPLE.txt"] = r'''
# CoreToGrid Vertical 9:16 Short Blueprint Directive
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

# ==============================================================================
# MULTI-PROVIDER AI HELPER (GEMINI + OPENROUTER FREE + GROQ FREE)
# ==============================================================================

FILES["scripts/gemini_helper.py"] = r'''
import json
import os
import re
import time
import urllib.error
import urllib.request
from typing import Any, Optional

from google import genai
from google.genai import types
from google.genai.errors import APIError

# Google AI Studio Free Tier Models (Nov 2026)
# Note: Hydrogen is reserved primarily for the 1 Storyboard call (role="pro") to stay under its ~20 RPD free cap.
PRO_LADDER = [
    ("gemini-4-hydrogen", "high", 65536, True),
    ("gemini-3.8-flash", "low", 32768, True),
    ("gemini-3.6-flash", None, 32768, True),
    ("gemini-3.5-flash-lite", None, 32768, True),
]

FLASH_LADDER = [
    ("gemini-3.8-flash", None, 32768, True),
    ("gemini-3.6-flash", None, 32768, True),
    ("gemini-3.5-flash-lite", None, 32768, True),
    ("gemini-4-hydrogen", "low", 65536, True),
    ("gemini-3.1-flash-lite", None, 32768, True),
    ("gemma-4-31b-it", None, 8192, False),
]

# Free OpenAI-compatible backup providers (Add OPENROUTER_API_KEY / GROQ_API_KEY in GitHub Secrets)
OPENROUTER_FREE_MODELS = [
    "nvidia/nemotron-3-ultra:free",
    "baidu/ernie-5.5-flash-preview:free",
    "cohere/north-mini-code:free",
    "openrouter/free",
]

GROQ_FREE_MODELS = [
    "openai/gpt-oss-120b",
    "qwen/qwen3.6-27b",
]

_COOLDOWN_UNTIL: dict[str, float] = {}


def get_client() -> Optional[genai.Client]:
    api_key = (os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY") or "").strip()
    if not api_key:
        return None
    # Support comma-separated keys if user supplies multiple project keys
    first_key = [k.strip() for k in api_key.split(",") if k.strip()][0]
    return genai.Client(
        api_key=first_key,
        http_options=types.HttpOptions(timeout=600_000),
    )


def clean_json_text(raw: str) -> str:
    text = (raw or "").strip()
    fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if fence_match:
        text = fence_match.group(1).strip()
    # Fallback: slice first { to last } if extra chatter surrounds JSON
    if not text.startswith("{") and "{" in text and "}" in text:
        start = text.find("{")
        end = text.rfind("}")
        if end > start:
            text = text[start : end + 1]
    return text


def clean_tsx_text(raw: str) -> str:
    text = (raw or "").strip()
    fence_match = re.search(r"```(?:tsx|typescript|ts|jsx)?\s*([\s\S]*?)```", text)
    if fence_match:
        text = fence_match.group(1).strip()
    return text


def _call_openai_compat(
    endpoint: str,
    api_key: str,
    model: str,
    prompt: str,
    json_mode: bool,
    extra_headers: Optional[dict[str, str]] = None,
) -> str:
    final_prompt = prompt
    if json_mode:
        final_prompt += "\n\nCRITICAL: Return ONLY valid raw JSON object. Do not include markdown fences or explanations."

    payload: dict[str, Any] = {
        "model": model,
        "messages": [{"role": "user", "content": final_prompt}],
        "max_tokens": 16384,
        "temperature": 0.25,
    }
    if json_mode:
        payload["response_format"] = {"type": "json_object"}

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    if extra_headers:
        headers.update(extra_headers)

    req = urllib.request.Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=180) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    content = data["choices"][0]["message"]["content"]
    if not content or not content.strip():
        raise RuntimeError(f"Empty response from {model}")
    return clean_json_text(content) if json_mode else content


def _try_openrouter_and_groq(prompt: str, json_mode: bool) -> Optional[str]:
    or_key = (os.environ.get("OPENROUTER_API_KEY") or "").strip()
    if or_key:
        for model in OPENROUTER_FREE_MODELS:
            try:
                print(f"[ai_router] Failing over to OpenRouter ({model})...", flush=True)
                res = _call_openai_compat(
                    "https://openrouter.ai/api/v1/chat/completions",
                    or_key,
                    model,
                    prompt,
                    json_mode,
                    extra_headers={"HTTP-Referer": "https://github.com/CoreToGrid", "X-Title": "CoreToGrid"},
                )
                print(f"[ai_router] OpenRouter success with {model} ({len(res)} chars).", flush=True)
                return res
            except Exception as exc:
                print(f"[ai_router] OpenRouter {model} skipped ({exc})", flush=True)
                time.sleep(2)

    groq_key = (os.environ.get("GROQ_API_KEY") or "").strip()
    if groq_key:
        for model in GROQ_FREE_MODELS:
            try:
                print(f"[ai_router] Failing over to Groq ({model})...", flush=True)
                res = _call_openai_compat(
                    "https://api.groq.com/openai/v1/chat/completions",
                    groq_key,
                    model,
                    prompt,
                    json_mode,
                )
                print(f"[ai_router] Groq success with {model} ({len(res)} chars).", flush=True)
                return res
            except Exception as exc:
                print(f"[ai_router] Groq {model} skipped ({exc})", flush=True)
                time.sleep(2)
    return None


def generate_with_fallback(
    client: Optional[genai.Client],
    contents: Any,
    role: str = "flash",
    json_mode: bool = False,
    max_output_tokens: int = 65536,
    temperature: float = 0.3,
) -> str:
    ladder = PRO_LADDER if role == "pro" else FLASH_LADDER
    dead_models: set[str] = set()
    last_error: Optional[Exception] = None
    prompt_str = str(contents)

    if client is not None:
        for pass_num in range(1, 3):
            now = time.time()
            for model_name, thinking_lvl, cap, supports_json in ladder:
                key = f"{model_name}:{thinking_lvl}"
                if key in dead_models or (pass_num == 1 and _COOLDOWN_UNTIL.get(model_name, 0) > now):
                    continue

                config_kwargs: dict[str, Any] = {
                    "max_output_tokens": min(cap, max_output_tokens),
                }
                # Gemini 4 Hydrogen ignores/forbids custom sampling params in strict agentic mode
                if "gemini-4" not in model_name:
                    config_kwargs["temperature"] = temperature
                if thinking_lvl:
                    config_kwargs["thinking_config"] = types.ThinkingConfig(thinking_level=thinking_lvl)
                if json_mode and supports_json:
                    config_kwargs["response_mime_type"] = "application/json"

                final_contents = prompt_str
                if json_mode and not supports_json:
                    final_contents = prompt_str + "\n\nCRITICAL: Return ONLY valid raw JSON with no markdown fences."

                config = types.GenerateContentConfig(**config_kwargs)

                try:
                    print(f"[gemini_helper] Pass {pass_num} -> {model_name} (think={thinking_lvl or 'off'})...", flush=True)
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
                    if any(k in msg for k in ("404", "403", "400", "not found", "unsupported", "limit: 0")):
                        print(f"[gemini_helper] {model_name} unavailable/unsupported ({exc}); skipping.", flush=True)
                        dead_models.add(key)
                        continue
                    if "429" in msg or "quota" in msg or "exhausted" in msg or "503" in msg:
                        _COOLDOWN_UNTIL[model_name] = time.time() + 65.0
                        print(f"[gemini_helper] {model_name} rate-limited (429/503); cooling 65s & switching...", flush=True)
                        time.sleep(6)
                    else:
                        time.sleep(4)
                except Exception as exc:
                    last_error = exc
                    time.sleep(3)

            # Try OpenRouter / Groq before waiting for Pass 2 on Gemini!
            backup = _try_openrouter_and_groq(prompt_str, json_mode)
            if backup:
                return backup

            if pass_num == 1:
                _COOLDOWN_UNTIL.clear()
                print("[gemini_helper] Pass 1 exhausted; waiting 18s for RPM bucket reset...", flush=True)
                time.sleep(18)

    # Final check against OpenRouter / Groq if Gemini key was omitted or completely blocked
    backup = _try_openrouter_and_groq(prompt_str, json_mode)
    if backup:
        return backup

    raise RuntimeError(f"All AI models (Gemini + OpenRouter + Groq) failed. Last error: {last_error}")


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
        p for p in input_dir.iterdir()
        if p.is_file() and p.name != ".gitkeep" and p.suffix.lower() in (AUDIO_EXTS | VIDEO_EXTS)
    ]
    if not candidates:
        raise FileNotFoundError(f"No audio file found inside {input_dir.name}/.")
    return max(candidates, key=lambda p: (git_commit_timestamp(p), p.stat().st_mtime, p.name))


def clean_and_normalize_audio(src_path: Path, trim_silence: bool, preview_sec: float, out_wav: Path) -> None:
    WORK_DIR.mkdir(parents=True, exist_ok=True)
    filters = ["highpass=f=75", "afftdn=nf=-25"]
    if trim_silence:
        filters.append("silenceremove=stop_periods=-1:stop_duration=0.65:stop_threshold=-42dB")
    filters.append("loudnorm=I=-14:TP=-1.5:LRA=11")

    ff_args = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(src_path)]
    if preview_sec > 0:
        ff_args += ["-t", f"{preview_sec:.2f}"]
    ff_args += ["-vn", "-af", ",".join(filters), "-ar", "48000", "-ac", "1", "-c:a", "pcm_s16le", str(out_wav)]
    subprocess.run(ff_args, check=True)


def transcribe_audio(wav_path: Path) -> Dict[str, Any]:
    model_size = os.environ.get("WHISPER_MODEL", "small")
    print(f"[analyze_audio] Transcribing via faster-whisper ({model_size}, CPU int8)...")
    model = WhisperModel(model_size, device="cpu", compute_type="int8")

    segments_iter, info = model.transcribe(
        str(wav_path),
        beam_size=5,
        word_timestamps=True,
        vad_filter=True,
        vad_parameters={"min_silence_duration_ms": 380},
        initial_prompt=(
            "Nvidia Blackwell, GB200, NVLink spine, microchannel cold plates, liquid cooling, "
            "dielectric fluid, CDU, cooling distribution unit, 800 kW, 130 kW per rack, "
            "substation, high-voltage transformer, 345 kV, 500 kV, SMR nuclear reactor, "
            "busbar, blind-mate quick disconnect, optical transceiver, CoWoS, TSMC 3nm."
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
        segments.append({
            "id": seg.id,
            "start": round(float(seg.start), 3),
            "end": round(float(seg.end), 3),
            "text": seg.text.strip(),
            "words": seg_words,
        })

    return {
        "language": info.language,
        "duration_sec": round(float(info.duration), 3),
        "segments": segments,
        "words": words,
        "full_text": " ".join(s["text"] for s in segments),
    }


def analyze_beats(wav_path: Path) -> Dict[str, Any]:
    print("[analyze_audio] Detecting vocal emphasis peaks & rhythm...")
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
    bpm_val = float(np.atleast_1d(tempo)[0]) if np.size(tempo) > 0 else 105.0
    if bpm_val < 70 or bpm_val > 135:
        bpm_val = 105.0

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

    print(f"[analyze_audio] Analyzing source: {src.name}")
    clean_wav = WORK_DIR / "clean_voiceover.wav"
    clean_and_normalize_audio(src, trim_silence=trim_silence, preview_sec=preview_sec, out_wav=clean_wav)

    transcript = transcribe_audio(clean_wav)
    beats = analyze_beats(clean_wav)
    transcript["duration_sec"] = beats["duration_sec"]

    (WORK_DIR / "transcript.json").write_text(json.dumps(transcript, indent=2, ensure_ascii=False), encoding="utf-8")
    (WORK_DIR / "beats.json").write_text(json.dumps(beats, indent=2), encoding="utf-8")
    print(f"[analyze_audio] Complete: {beats['duration_sec']:.2f}s ({len(transcript['words'])} words).")


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
'''

FILES["scripts/validate_scenes.py"] = r'''
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLAN_PATH = ROOT / "work" / "scene_plan.json"
SCENES_DIR = ROOT / "src" / "generated" / "scenes"


def main() -> None:
    if not PLAN_PATH.exists():
        raise SystemExit("Missing work/scene_plan.json")
    plan = json.loads(PLAN_PATH.read_text(encoding="utf-8"))
    scenes = plan.get("scenes", [])
    if not scenes:
        raise SystemExit("Plan contains 0 scenes.")

    for sc in scenes:
        f = SCENES_DIR / f"{sc['componentName']}.tsx"
        if not f.exists():
            raise SystemExit(f"Missing scene file: {f.name}")
        txt = f.read_text(encoding="utf-8")
        for bad in ("<div", "<span", "useFrame", "useEffect", "useState", "from 'three'"):
            if bad in txt:
                raise SystemExit(f"Scene {f.name} contains forbidden token: {bad}")

    print(f"[validate_scenes] PASSED: All {len(scenes)} blueprint scenes verified.")


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


def bandpass(signal: np.ndarray, low: float, high: float) -> np.ndarray:
    sos = butter(3, [low, high], btype="band", fs=SAMPLE_RATE, output="sos")
    return sosfilt(sos, signal)


def make_sfx_bank() -> dict[str, np.ndarray]:
    rng = np.random.default_rng(42)
    nw = int(0.28 * SAMPLE_RATE)
    tw = np.arange(nw) / SAMPLE_RATE
    w = bandpass(rng.normal(0.0, 1.0, nw), 300.0, 2600.0) * (np.sin(np.pi * tw / 0.28) ** 1.5)
    whoosh = np.column_stack([w, w]) / (np.max(np.abs(w)) + 1e-9)

    np_snap = int(0.09 * SAMPLE_RATE)
    tp = np.arange(np_snap) / SAMPLE_RATE
    p = np.sin(2.0 * np.pi * 1800.0 * tp) * np.exp(-tp * 85.0)
    snap = np.column_stack([p, p]) / (np.max(np.abs(p)) + 1e-9)

    ns = int(0.42 * SAMPLE_RATE)
    ts = np.arange(ns) / SAMPLE_RATE
    fs = 95.0 * np.exp(-ts * 5.0) + 35.0
    s = np.sin(2.0 * np.pi * np.cumsum(fs) / SAMPLE_RATE) * np.exp(-ts * 6.0)
    sub = np.column_stack([s, s]) / (np.max(np.abs(s)) + 1e-9)

    return {
        "whoosh": whoosh * 0.15,
        "pop_snap": snap * 0.18,
        "marker_swipe": whoosh * 0.12,
        "sub_impact": sub * 0.22,
        "tick": snap * 0.12,
    }


def main() -> None:
    plan = json.loads((WORK_DIR / "scene_plan.json").read_text(encoding="utf-8"))
    vo, _ = sf.read(str(WORK_DIR / "clean_voiceover.wav"), dtype="float64")
    if vo.ndim > 1:
        vo = np.mean(vo, axis=1)

    n_samples = len(vo)
    mix = np.column_stack([vo, vo]) * 0.94
    sfx_bank = make_sfx_bank()

    for sc in plan.get("scenes", []):
        cue = sc.get("sfx", "pop_snap")
        snd = sfx_bank.get(cue, sfx_bank["pop_snap"])
        start_idx = max(0, int(float(sc["startSec"]) * SAMPLE_RATE))
        end_idx = min(n_samples, start_idx + len(snd))
        if end_idx > start_idx:
            mix[start_idx:end_idx] += snd[: end_idx - start_idx]

    mix = np.tanh(mix * 0.95)
    master_m4a = WORK_DIR / "master_audio.m4a"
    tmp_wav = WORK_DIR / "temp_master.wav"
    sf.write(str(tmp_wav), mix, SAMPLE_RATE, subtype="PCM_16")

    subprocess.run([
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-i", str(tmp_wav), "-c:a", "aac", "-b:a", "192k", "-ar", str(SAMPLE_RATE),
        str(master_m4a)
    ], check=True)
    tmp_wav.unlink(missing_ok=True)
    print(f"[mix_audio] Master audio built: {n_samples / SAMPLE_RATE:.2f}s.")


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
    if force.isdigit():
        workers = int(force)
    else:
        if total_frames <= 1800:
            workers = 4
        elif total_frames <= 5400:
            workers = 8
        elif total_frames <= 13500:
            workers = 14
        else:
            workers = 20

    workers = min(workers, total_frames)
    chunk_size = math.ceil(total_frames / workers)

    chunks = []
    for idx in range(workers):
        start_f = idx * chunk_size
        end_f = min(total_frames - 1, (idx + 1) * chunk_size - 1)
        if start_f <= end_f:
            chunks.append({"idx": idx, "start": start_f, "end": end_f})

    chunks_json = json.dumps(chunks)
    print(f"[plan_chunks] total_frames={total_frames}, parallel_workers={len(chunks)}")

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
    chunks = sorted(CHUNKS_DIR.rglob("chunk_*.mp4"), key=chunk_index)
    if not chunks:
        raise FileNotFoundError("No rendered chunk_*.mp4 files found.")

    list_file = WORK_DIR / "chunks.txt"
    with open(list_file, "w", encoding="utf-8") as f:
        for c in chunks:
            f.write(f"file '{c.resolve().as_posix()}'\n")

    video_format = os.environ.get("VIDEO_FORMAT", "long_16_9").strip()
    out_name = "final_short.mp4" if video_format == "short_9_16" else "final_video.mp4"
    final_mp4 = OUT_DIR / out_name
    master_audio = WORK_DIR / "master_audio.m4a"

    print(f"[stitch_chunks] Joining {len(chunks)} chunks -> {final_mp4}")
    subprocess.run([
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "warning",
        "-f", "concat", "-safe", "0", "-i", str(list_file),
        "-i", str(master_audio),
        "-map", "0:v:0", "-map", "1:a:0",
        "-c:v", "copy", "-c:a", "copy",
        "-movflags", "+faststart", "-shortest",
        str(final_mp4)
    ], check=True)
    print(f"[stitch_chunks] SUCCESS! Video exported: {final_mp4} ({final_mp4.stat().st_size / (1024*1024):.1f} MB)")


if __name__ == "__main__":
    main()
'''

# ==============================================================================
# REMOTION TYPES & BLUEPRINT COMPONENT SUITE
# ==============================================================================

FILES["src/types.ts"] = r'''
export type BackdropTheme =
  | "isometric_blueprint"
  | "xray_cutaway"
  | "substation_grid"
  | "cleanroom_fab"
  | "thermal_flow"
  | "server_corridor"
  | "dark_industrial"
  | "black_title_card"
  | "split_3panel";

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
  bpm: number;
  scenes: CartoonScene[];
}
'''

FILES["src/components/CartoonKit2D.tsx"] = r'''
import React from "react";
import { loadFont as loadSpaceGrotesk } from "@remotion/google-fonts/SpaceGrotesk";
import { loadFont as loadJetBrainsMono } from "@remotion/google-fonts/JetBrainsMono";
import { spring, useVideoConfig } from "remotion";
import type { BackdropTheme, CameraMove2D } from "../types";

const { fontFamily: UI_FONT } = loadSpaceGrotesk("normal", { weights: ["600", "700"], subsets: ["latin"] });
const { fontFamily: MONO_FONT } = loadJetBrainsMono("normal", { weights: ["500", "700"], subsets: ["latin"] });

const INK = "#0A0F1D";
const BLUEPRINT_LINE = "#1E293B";

export const SceneBackdrop2D: React.FC<{
  theme: BackdropTheme;
  frame: number;
  accentHex?: string;
}> = ({ theme, frame, accentHex = "#00F0FF" }) => {
  if (theme === "black_title_card") {
    return <rect x={-100} y={-100} width={2200} height={2200} fill="#050811" />;
  }

  if (theme === "isometric_blueprint" || theme === "thermal_flow") {
    return (
      <g>
        <rect x={-100} y={-100} width={2200} height={2200} fill="#080C14" />
        {Array.from({ length: 30 }).map((_, i) => (
          <line key={`iso1_${i}`} x1={-200 + i * 120} y1={-100} x2={-200 + i * 120 + 1200} y2={2100} stroke={BLUEPRINT_LINE} strokeWidth={1.5} strokeDasharray="4 8" />
        ))}
        {Array.from({ length: 30 }).map((_, i) => (
          <line key={`iso2_${i}`} x1={2200 - i * 120} y1={-100} x2={2200 - i * 120 - 1200} y2={2100} stroke={BLUEPRINT_LINE} strokeWidth={1.5} strokeDasharray="4 8" />
        ))}
        <text x={80} y={80} fill="#334155" fontFamily={MONO_FONT} fontSize={16}>
          SYS_REF: GRID_30DEG // {theme.toUpperCase()}
        </text>
      </g>
    );
  }

  if (theme === "xray_cutaway" || theme === "split_3panel") {
    return (
      <g>
        <rect x={-100} y={-100} width={2200} height={2200} fill="#0A1120" />
        {Array.from({ length: 24 }).map((_, i) => (
          <line key={`xr_${i}`} x1={i * 90} y1={-50} x2={i * 90} y2={2050} stroke="#162238" strokeWidth={1.5} />
        ))}
        <rect x={60} y={60} width={1800} height={960} fill="none" stroke={accentHex} strokeWidth={2} strokeOpacity={0.25} strokeDasharray="10 8" />
      </g>
    );
  }

  if (theme === "substation_grid") {
    return (
      <g>
        <rect x={-100} y={-100} width={2200} height={2200} fill="#0A0E17" />
        <rect x={-50} y={780} width={2100} height={1300} fill="#111827" stroke={INK} strokeWidth={4} />
        {[-40, 20, 80].map((yOff, i) => (
          <line key={i} x1={-100} y1={280 + yOff} x2={2100} y2={280 + yOff} stroke="#F59E0B" strokeWidth={3} strokeDasharray="18 12" strokeDashoffset={-frame * 2} />
        ))}
      </g>
    );
  }

  if (theme === "cleanroom_fab") {
    return (
      <g>
        <rect x={-100} y={-100} width={2200} height={2200} fill="#0D1527" />
        {Array.from({ length: 24 }).map((_, i) => (
          <line key={`v_${i}`} x1={i * 90} y1={-50} x2={i * 90} y2={2050} stroke="#1E293B" strokeWidth={1.5} />
        ))}
        {Array.from({ length: 24 }).map((_, i) => (
          <line key={`h_${i}`} x1={-50} y1={i * 90} x2={2050} y2={i * 90} stroke="#1E293B" strokeWidth={1.5} />
        ))}
      </g>
    );
  }

  return (
    <g>
      <rect x={-100} y={-100} width={2200} height={2200} fill="#090D16" />
      {[240, 640, 1280, 1680].map((lx, i) => (
        <rect key={i} x={lx - 60} y={30} width={120} height={14} rx={4} fill={accentHex} opacity={0.8} />
      ))}
      <rect x={-50} y={820} width={2100} height={1200} fill="#1E293B" stroke={INK} strokeWidth={4} />
      <line x1={-50} y1={820} x2={2050} y2={820} stroke={accentHex} strokeWidth={4} />
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

  if (move === "push_in") scale = 1 + ease * 0.08;
  else if (move === "pull_out") scale = 1.08 - ease * 0.08;
  else if (move === "pan_right") { scale = 1.04; tx = 30 - ease * 60; }
  else if (move === "pan_left") { scale = 1.04; tx = -30 + ease * 60; }
  else if (move === "pan_up") { scale = 1.04; ty = 25 - ease * 50; }

  let shake = 0;
  for (const pt of peakTimes) {
    const dt = localTime - pt;
    if (dt >= 0 && dt < 0.25) {
      shake += Math.sin(frame * 2.8) * 6 * (1 - dt / 0.25);
    }
  }

  return (
    <g transform={`translate(${960 + tx + shake} ${540 + ty + shake}) scale(${scale}) translate(-960 -540)`}>
      {children}
    </g>
  );
};

export const TelemetryHUD2D: React.FC<{
  x: number;
  y: number;
  title: string;
  metrics: { label: string; value: string; unit?: string; alert?: boolean }[];
  progress: number;
}> = ({ x, y, title, metrics, progress }) => {
  const p = Math.min(1, progress * 1.5);
  return (
    <g transform={`translate(${x} ${y}) scale(${0.9 + 0.1 * p})`} opacity={p}>
      <rect x={0} y={0} width={380} height={60 + metrics.length * 48} rx={8} fill="#090E17" fillOpacity={0.92} stroke="#38BDF8" strokeWidth={2} />
      <rect x={0} y={0} width={380} height={36} rx={8} fill="#1E293B" />
      <circle cx={20} cy={18} r={5} fill="#00F0FF" />
      <text x={36} y={23} fill="#E2E8F0" fontFamily={UI_FONT} fontSize={16} fontWeight={700}>{title}</text>
      {metrics.map((m, idx) => (
        <g key={idx} transform={`translate(20 ${62 + idx * 48})`}>
          <text x={0} y={16} fill="#94A3B8" fontFamily={MONO_FONT} fontSize={14}>{m.label}</text>
          <text x={340} y={16} textAnchor="end" fill={m.alert ? "#EF4444" : "#00F0FF"} fontFamily={MONO_FONT} fontSize={18} fontWeight={700}>
            {m.value} {m.unit || ""}
          </text>
          <line x1={0} y1={28} x2={340} y2={28} stroke="#1E293B" strokeWidth={1} />
        </g>
      ))}
    </g>
  );
};

export const MicrochannelColdPlate2D: React.FC<{
  x: number;
  y: number;
  scale?: number;
  coolantTempC?: number;
  frame: number;
  progress: number;
}> = ({ x, y, scale = 1, coolantTempC = 62, frame, progress }) => {
  const lift = Math.min(1, progress * 1.4) * 60;
  const shift = (frame * 3) % 24;
  return (
    <g transform={`translate(${x} ${y}) scale(${scale})`}>
      <rect x={-180} y={60} width={360} height={60} rx={4} fill="#1E293B" stroke="#00F0FF" strokeWidth={3} />
      <text x={0} y={98} textAnchor="middle" fill="#00F0FF" fontFamily={MONO_FONT} fontSize={20} fontWeight={700}>
        SILICON DIE // {coolantTempC}C EXIT
      </text>
      <rect x={-210} y={0} width={420} height={48} rx={6} fill="#B45309" stroke="#F59E0B" strokeWidth={3} />
      {Array.from({ length: 32 }).map((_, i) => (
        <rect key={i} x={-190 + i * 12} y={-40} width={6} height={40} fill={i % 2 === 0 ? "#D97706" : "#38BDF8"} opacity={0.75 + 0.25 * Math.sin(shift + i)} />
      ))}
      <g transform={`translate(0 ${-lift})`}>
        <rect x={-220} y={-90} width={440} height={46} rx={8} fill="#334155" stroke="#94A3B8" strokeWidth={3} />
        <circle cx={-130} cy={-67} r={18} fill="#00F0FF" />
        <text x={-130} y={-62} textAnchor="middle" fill="#0A0F1D" fontFamily={MONO_FONT} fontSize={12} fontWeight={700}>IN</text>
        <circle cx={130} cy={-67} r={18} fill="#EF4444" />
        <text x={130} y={-62} textAnchor="middle" fill="#0A0F1D" fontFamily={MONO_FONT} fontSize={12} fontWeight={700}>OUT</text>
      </g>
    </g>
  );
};

export const ServerRack800kW2D: React.FC<{
  x: number;
  y: number;
  scale?: number;
  accentHex?: string;
  frame: number;
  progress: number;
}> = ({ x, y, scale = 1, accentHex = "#00F0FF", frame, progress }) => (
  <g transform={`translate(${x} ${y}) scale(${scale})`}>
    <rect x={-120} y={-260} width={240} height={520} rx={8} fill="#0D131F" stroke="#334155" strokeWidth={5} />
    <rect x={-12} y={-240} width={24} height={480 * Math.min(1, progress + 0.2)} fill="#B45309" stroke="#F59E0B" strokeWidth={2} />
    {[-210, -140, -70, 0, 70, 140, 210].map((ry, i) => {
      const active = Math.sin(frame * 0.2 - i) > -0.1;
      return (
        <g key={i}>
          <rect x={-98} y={ry - 24} width={196} height={48} rx={4} fill="#1E293B" stroke="#475569" strokeWidth={2} />
          <circle cx={-75} cy={ry} r={5} fill={active ? accentHex : "#334155"} />
          <line x1={-55} y1={ry} x2={55} y2={ry} stroke={active ? "#38BDF8" : "#334155"} strokeWidth={3} strokeDasharray="8 6" />
        </g>
      );
    })}
  </g>
);

export const TransformerSubstation2D: React.FC<{
  x: number;
  y: number;
  scale?: number;
  voltageKV?: number;
  frame: number;
}> = ({ x, y, scale = 1, voltageKV = 345, frame }) => (
  <g transform={`translate(${x} ${y}) scale(${scale})`}>
    <rect x={-160} y={-100} width={320} height={260} rx={10} fill="#1E293B" stroke="#475569" strokeWidth={6} />
    {[-140, -100, -60, 60, 100, 140].map((fx, i) => (
      <line key={i} x1={fx} y1={-80} x2={fx} y2={140} stroke="#334155" strokeWidth={8} />
    ))}
    {[-80, 0, 80].map((bx, i) => (
      <g key={i} transform={`translate(${bx} -100)`}>
        <polygon points="-16,0 16,0 8,-90 -8,-90" fill="#94A3B8" stroke="#334155" strokeWidth={3} />
        <circle cx={0} cy={-98} r={12} fill="#F59E0B" opacity={0.7 + 0.3 * Math.sin(frame * 0.3 + i)} />
        <line x1={0} y1={-100} x2={bx * 1.5} y2={-160} stroke="#F59E0B" strokeWidth={4} strokeDasharray="6 4" />
      </g>
    ))}
    <rect x={-80} y={40} width={160} height={40} rx={4} fill="#0F172A" stroke="#F59E0B" strokeWidth={2} />
    <text x={0} y={66} textAnchor="middle" fill="#F59E0B" fontFamily={MONO_FONT} fontSize={18} fontWeight={700}>
      {voltageKV} kV STEP-DOWN
    </text>
  </g>
);

export const NuclearSMRVessel2D: React.FC<{
  x: number;
  y: number;
  scale?: number;
  cherenkovGlow?: boolean;
  frame: number;
  progress: number;
}> = ({ x, y, scale = 1, cherenkovGlow = true, frame, progress }) => {
  const pulse = 0.75 + 0.25 * Math.sin(frame * 0.2);
  const rodDrop = Math.sin(frame * 0.1) * 18 * Math.min(1, progress * 1.5);
  return (
    <g transform={`translate(${x} ${y}) scale(${scale})`}>
      <path d="M -120 -80 Q -120 -220 0 -220 Q 120 -220 120 -80 L 120 180 L -120 180 Z" fill="#1E293B" stroke="#475569" strokeWidth={6} />
      <rect x={-75} y={-30} width={150} height={160} rx={12} fill="#0284C7" stroke="#38BDF8" strokeWidth={4} />
      {cherenkovGlow && <rect x={-65} y={-20} width={130} height={140} rx={8} fill="#00F0FF" opacity={pulse * 0.85} />}
      {[-32, 0, 32].map((rx, i) => (
        <rect key={i} x={rx - 8} y={-110 + rodDrop} width={16} height={110} rx={4} fill="#FACC15" stroke="#713F12" strokeWidth={2} />
      ))}
    </g>
  );
};

export const AnimatedFluidPipe2D: React.FC<{
  d: string;
  color?: string;
  fluidColor?: string;
  strokeWidth?: number;
  frame: number;
}> = ({ d, color = "#334155", fluidColor = "#00F0FF", strokeWidth = 26, frame }) => (
  <g>
    <path d={d} fill="none" stroke="#0A0F1D" strokeWidth={strokeWidth + 8} strokeLinecap="round" strokeLinejoin="round" />
    <path d={d} fill="none" stroke={color} strokeWidth={strokeWidth} strokeLinecap="round" strokeLinejoin="round" />
    <path d={d} fill="none" stroke={fluidColor} strokeWidth={strokeWidth * 0.4} strokeDasharray="20 16" strokeDashoffset={-frame * 6} strokeLinecap="round" />
  </g>
);

export const TechnicalCallout2D: React.FC<{
  x: number;
  y: number;
  text: string;
  subtext?: string;
  color?: string;
  localTime: number;
  delaySec?: number;
  arrowTo?: [number, number];
}> = ({ x, y, text, subtext, color = "#00F0FF", localTime, delaySec = 0, arrowTo }) => {
  const { fps } = useVideoConfig();
  const f = Math.max(0, Math.round((localTime - delaySec) * fps));
  const pop = spring({ frame: f, fps, config: { damping: 14, stiffness: 180 } });
  if (localTime < delaySec) return null;

  return (
    <g transform={`translate(${x} ${y}) scale(${pop})`}>
      {arrowTo && (
        <line x1={0} y1={0} x2={arrowTo[0] - x} y2={arrowTo[1] - y} stroke={color} strokeWidth={2} strokeDasharray="4 4" />
      )}
      <rect x={-14} y={-24} width={Math.max(180, text.length * 15)} height={subtext ? 58 : 38} rx={4} fill="#090E17" stroke={color} strokeWidth={2} />
      <text x={0} y={0} fill={color} fontFamily={MONO_FONT} fontSize={18} fontWeight={700}>{text}</text>
      {subtext && <text x={0} y={22} fill="#94A3B8" fontFamily={UI_FONT} fontSize={13}>{subtext}</text>}
    </g>
  );
};

export const TitleCard2D: React.FC<{
  text: string;
  progress: number;
  accentHex?: string;
}> = ({ text, progress, accentHex = "#00F0FF" }) => (
  <g transform="translate(960 540)">
    <text x={0} y={15} textAnchor="middle" fill="#FFFFFF" fontFamily={UI_FONT} fontSize={88} fontWeight={700}>{text}</text>
    <line x1={-300 * Math.min(1, progress * 1.5)} y1={60} x2={300 * Math.min(1, progress * 1.5)} y2={60} stroke={accentHex} strokeWidth={6} strokeLinecap="round" />
  </g>
);

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
  color?: string;
  progress: number;
}> = ({ x, y, w = 960, h = 420, label = "SURGE", startVal = 0, endVal = 100, prefix = "", suffix = "", color = "#EF4444", progress }) => {
  const drawProg = Math.min(1, progress * 1.4);
  const cur = Math.round(startVal + (endVal - startVal) * drawProg);
  const d = `M ${x} ${y + h} Q ${x + w * 0.4} ${y + h * 0.7} ${x + w} ${y + h * 0.15}`;
  return (
    <g>
      <rect x={x - 20} y={y - 20} width={w + 40} height={h + 70} rx={8} fill="#080C14" fillOpacity={0.9} stroke="#1E293B" strokeWidth={2} />
      <path d={d} fill="none" stroke={color} strokeWidth={8} strokeLinecap="round" strokeDasharray={w * 1.5} strokeDashoffset={w * 1.5 * (1 - drawProg)} />
      <text x={x + 20} y={y + 36} fill="#E2E8F0" fontFamily={UI_FONT} fontSize={24} fontWeight={700}>{label}</text>
      <text x={x + w - 20} y={y + 45} textAnchor="end" fill={color} fontFamily={MONO_FONT} fontSize={44} fontWeight={700}>{prefix}{cur.toLocaleString()}{suffix}</text>
    </g>
  );
};

export const BarChart2D: React.FC<{
  x: number;
  y: number;
  w?: number;
  h?: number;
  bars: { label: string; value: number; color?: string }[];
  progress: number;
}> = ({ x, y, w = 840, h = 420, bars, progress }) => {
  const max = Math.max(1, ...bars.map((b) => b.value));
  const bw = (w / Math.max(1, bars.length)) * 0.6;
  return (
    <g>
      <line x1={x} y1={y + h} x2={x + w} y2={y + h} stroke="#334155" strokeWidth={4} />
      {bars.map((b, i) => {
        const bh = (b.value / max) * (h - 60) * Math.min(1, progress * 1.5);
        const bx = x + i * (w / Math.max(1, bars.length)) + 40;
        return (
          <g key={i}>
            <rect x={bx} y={y + h - bh} width={bw} height={bh} rx={4} fill={b.color || "#00F0FF"} />
            <text x={bx + bw / 2} y={y + h + 36} textAnchor="middle" fill="#94A3B8" fontFamily={MONO_FONT} fontSize={16}>{b.label}</text>
          </g>
        );
      })}
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
}> = ({ x, y, leftLabel, rightLabel, tiltDeg = 15, leftColor = "#10B981", rightColor = "#EF4444", progress }) => {
  const tilt = tiltDeg * Math.min(1, progress * 1.5);
  return (
    <g transform={`translate(${x} ${y})`}>
      <line x1={-240} y1={tilt} x2={240} y2={-tilt} stroke="#94A3B8" strokeWidth={12} strokeLinecap="round" />
      <polygon points="0,-10 -30,160 30,160" fill="#334155" />
      <rect x={-260} y={tilt + 10} width={160} height={60} rx={6} fill={leftColor} />
      <text x={-180} y={tilt + 46} textAnchor="middle" fill="#FFFFFF" fontFamily={UI_FONT} fontSize={18} fontWeight={700}>{leftLabel}</text>
      <rect x={100} y={-tilt + 10} width={160} height={60} rx={6} fill={rightColor} />
      <text x={180} y={-tilt + 46} textAnchor="middle" fill="#FFFFFF" fontFamily={UI_FONT} fontSize={18} fontWeight={700}>{rightLabel}</text>
    </g>
  );
};

export const Microchip2D: React.FC<{
  x: number;
  y: number;
  scale?: number;
  color?: string;
  cracked?: boolean;
  overheating?: boolean;
  frame: number;
  progress: number;
}> = ({ x, y, scale = 1, color = "#00F0FF", overheating = false, frame }) => (
  <g transform={`translate(${x} ${y}) scale(${scale})`}>
    <rect x={-120} y={-120} width={240} height={240} rx={12} fill="#090E17" stroke={overheating ? "#EF4444" : color} strokeWidth={6} />
    <rect x={-80} y={-80} width={160} height={160} rx={8} fill={overheating ? "#EF4444" : color} opacity={0.75 + 0.25 * Math.sin(frame * 0.25)} />
    <text x={0} y={8} textAnchor="middle" fill="#0A0F1D" fontFamily={MONO_FONT} fontSize={22} fontWeight={700}>BLACKWELL</text>
  </g>
);

export const PowerPylon2D: React.FC<{
  x: number;
  y: number;
  scale?: number;
  accentHex?: string;
  frame: number;
}> = ({ x, y, scale = 1, accentHex = "#F59E0B", frame }) => (
  <g transform={`translate(${x} ${y}) scale(${scale})`}>
    <polygon points="-80,180 -20,-180 20,-180 80,180" fill="none" stroke="#94A3B8" strokeWidth={6} />
    <line x1={-120} y1={-80} x2={120} y2={-80} stroke="#94A3B8" strokeWidth={8} />
    <circle cx={-120} cy={-70} r={12} fill={accentHex} opacity={0.7 + 0.3 * Math.sin(frame * 0.3)} />
    <circle cx={120} cy={-70} r={12} fill={accentHex} opacity={0.7 + 0.3 * Math.sin(frame * 0.3)} />
  </g>
);

export const BatteryBank2D: React.FC<{
  x: number;
  y: number;
  scale?: number;
  accentHex?: string;
  frame: number;
  progress: number;
}> = ({ x, y, scale = 1, accentHex = "#10B981", frame, progress }) => (
  <g transform={`translate(${x} ${y}) scale(${scale})`}>
    <rect x={-140} y={-90} width={280} height={180} rx={12} fill="#1E293B" stroke="#475569" strokeWidth={5} />
    <rect x={-110} y={-60} width={220 * Math.min(1, progress * 1.5)} height={120} rx={6} fill={accentHex} opacity={0.8 + 0.2 * Math.sin(frame * 0.15)} />
  </g>
);

export const SplitScreen3Panel: React.FC<{
  progress: number;
  panel1: React.ReactNode;
  panel2: React.ReactNode;
  panel3: React.ReactNode;
}> = ({ progress, panel1, panel2, panel3 }) => (
  <g>
    <g>{panel1}</g>
    {progress >= 0.25 && <g>{panel2}</g>}
    {progress >= 0.52 && <g>{panel3}</g>}
    <line x1={640} y1={0} x2={640} y2={1080} stroke="#1E293B" strokeWidth={8} />
    <line x1={1280} y1={0} x2={1280} y2={1080} stroke="#1E293B" strokeWidth={8} />
  </g>
);
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
  const transSec = 0.24;

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
    <AbsoluteFill style={{ backgroundColor: "#050811", overflow: "hidden" }}>
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
  SceneBackdrop2D, Camera2D, TelemetryHUD2D, MicrochannelColdPlate2D, TechnicalCallout2D
} from "../../components/CartoonKit2D";
import type { Scene2DProps } from "../../types";

export const Scene_01: React.FC<Scene2DProps> = (props) => {
  const { frame, localTime, progress, peakTimes, accentHex, backdropTheme, cameraMove, isVertical } = props;
  const vb = isVertical ? "0 0 1080 1920" : "0 0 1920 1080";
  return (
    <svg viewBox={vb} style={{ width: "100%", height: "100%", display: "block" }}>
      <SceneBackdrop2D theme={backdropTheme} frame={frame} accentHex={accentHex} />
      <Camera2D move={cameraMove} progress={progress} frame={frame} peakTimes={peakTimes} localTime={localTime}>
        <MicrochannelColdPlate2D
          x={isVertical ? 540 : 880}
          y={isVertical ? 960 : 540}
          scale={1.3}
          coolantTempC={62}
          frame={frame}
          progress={progress}
        />
        <TelemetryHUD2D
          x={isVertical ? 120 : 120}
          y={isVertical ? 240 : 180}
          title="COLD PLATE TELEMETRY"
          metrics={[
            { label: "COOLANT INLET", value: "32.0", unit: "C" },
            { label: "COOLANT OUTLET", value: "62.4", unit: "C", alert: true },
            { label: "FLOW RATE", value: "2.1", unit: "LPM" },
          ]}
          progress={progress}
        />
        <TechnicalCallout2D
          x={isVertical ? 540 : 1420}
          y={isVertical ? 1520 : 480}
          text="40um COPPER CHANNELS"
          subtext="Direct-to-Die Interface"
          color="#00F0FF"
          localTime={localTime}
          delaySec={0.2}
          arrowTo={[isVertical ? 540 : 880, isVertical ? 960 : 540]}
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
  channel: "CoreToGrid",
  fps: 30,
  width: 1920,
  height: 1080,
  totalDurationSec: 6,
  bpm: 105,
  scenes: [
    {
      id: "scene_01",
      componentName: "Scene_01",
      visualConcept: "Baseline Microchannel Cold Plate",
      visualSpec: "Exploded copper plate with live telemetry HUD",
      titleText: "",
      backdropTheme: "isometric_blueprint",
      cameraMove: "push_in",
      transition: "flash_cut",
      sfx: "sub_impact",
      accentHex: "#00F0FF",
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

export const GeneratedTimeline: React.FC = () => (
  <AbsoluteFill>
    <CartoonStage2D plan={SCENE_PLAN} />
  </AbsoluteFill>
);
'''

FILES["src/Main.tsx"] = r'''
import React from "react";
import { AbsoluteFill } from "remotion";
import { GeneratedTimeline } from "./generated/GeneratedTimeline";

export const Main: React.FC = () => (
  <AbsoluteFill style={{ backgroundColor: "#050811" }}>
    <GeneratedTimeline />
  </AbsoluteFill>
);
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

# ==============================================================================
# GITHUB ACTIONS WORKFLOWS (MULTI-PROVIDER AI + 20 PARALLEL WORKERS)
# ==============================================================================

FILES[".github/workflows/render_video.yml"] = r'''
name: CoreToGrid Documentary Factory (16:9)

on:
  push:
    paths:
      - "input/**"
  workflow_dispatch:
    inputs:
      preview_seconds:
        description: "0 = Full video, or 30 for quick test"
        required: false
        default: "0"
        type: choice
        options:
          - "0"
          - "30"
      force_workers:
        description: "Parallel cloud runners (auto = up to 20 workers)"
        required: false
        default: "auto"
        type: choice
        options:
          - "auto"
          - "4"
          - "10"
          - "20"
      trim_silence:
        description: "Trim pauses >0.65s?"
        required: false
        default: "false"
        type: choice
        options:
          - "false"
          - "true"

concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: false

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

      - name: Check for input audio
        id: check_input
        run: |
          shopt -s nullglob nocaseglob
          files=(input/*.mp3 input/*.wav input/*.m4a input/*.aac input/*.flac input/*.mp4)
          if [ ${#files[@]} -eq 0 ]; then
            echo "has_input=false" >> $GITHUB_OUTPUT
          else
            echo "has_input=true" >> $GITHUB_OUTPUT
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

      - name: Install FFmpeg & Headless Chrome OS Libraries
        if: steps.check_input.outputs.has_input == 'true'
        run: |
          sudo apt-get update
          sudo apt-get install -y \
            ffmpeg libnss3 libdbus-1-3 libatk1.0-0 libgbm1 libxrandr2 \
            libxkbcommon0 libxfixes3 libxcomposite1 libxdamage1 \
            libatk-bridge2.0-0 libpango-1.0-0 libcairo2 libcups2 \
            libasound2t64 || sudo apt-get install -y libasound2

      - name: Install Python & Node Packages
        if: steps.check_input.outputs.has_input == 'true'
        run: |
          pip install -r requirements.txt
          npm install --no-audit --no-fund
          npx remotion browser ensure

      - name: Step 1 - Transcribe & Vocal Emphasis Peaks
        if: steps.check_input.outputs.has_input == 'true'
        env:
          INPUT_FOLDER: "input"
          TRIM_SILENCE: ${{ github.event.inputs.trim_silence || 'false' }}
          PREVIEW_SECONDS: ${{ github.event.inputs.preview_seconds || '0' }}
        run: python scripts/analyze_audio.py

      - name: Step 2 - Multi-Provider AI Blueprint Illustrator & Self-Healer
        if: steps.check_input.outputs.has_input == 'true'
        env:
          INPUT_FOLDER: "input"
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
          OPENROUTER_API_KEY: ${{ secrets.OPENROUTER_API_KEY }}
          GROQ_API_KEY: ${{ secrets.GROQ_API_KEY }}
          VIDEO_FORMAT: "long_16_9"
        run: python scripts/generate_scenes.py

      - name: Step 3 - Audit Blueprint Continuity
        if: steps.check_input.outputs.has_input == 'true'
        run: python scripts/validate_scenes.py

      - name: Step 4 - Master Audio & Foley Mix
        if: steps.check_input.outputs.has_input == 'true'
        run: python scripts/mix_audio.py

      - name: Step 5 - Frame 0 Smoke Test & Bundle
        if: steps.check_input.outputs.has_input == 'true'
        run: |
          npx remotion still src/index.ts Main work/frame0_smoke.png --frame=0
          npx remotion bundle src/index.ts --public-dir public --out-dir build_bundle

      - name: Step 6 - Plan Up to 20 Parallel Workers
        id: chunk_plan
        if: steps.check_input.outputs.has_input == 'true'
        env:
          FORCE_WORKERS: ${{ github.event.inputs.force_workers || 'auto' }}
        run: python scripts/plan_chunks.py

      - name: Upload Prepared Bundle
        if: steps.check_input.outputs.has_input == 'true'
        uses: actions/upload-artifact@v4
        with:
          name: prepared-long
          path: |
            build_bundle/
            work/master_audio.m4a
            work/scene_plan.json
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
      - name: Checkout Config
        uses: actions/checkout@v4

      - name: Download Bundle
        uses: actions/download-artifact@v4
        with:
          name: prepared-long

      - name: Set up Node.js 22
        uses: actions/setup-node@v4
        with:
          node-version: "22"

      - name: Install Headless Chrome Libraries
        run: |
          sudo apt-get update
          sudo apt-get install -y \
            ffmpeg libnss3 libdbus-1-3 libatk1.0-0 libgbm1 libxrandr2 \
            libxkbcommon0 libxfixes3 libxcomposite1 libxdamage1 \
            libatk-bridge2.0-0 libpango-1.0-0 libcairo2 libcups2 \
            libasound2t64 || sudo apt-get install -y libasound2
          npm install --no-audit --no-fund
          npx remotion browser ensure

      - name: Render Blueprint Chunk ${{ matrix.chunk.idx }}
        run: |
          mkdir -p out
          npx remotion render build_bundle Main out/chunk_${{ matrix.chunk.idx }}.mp4 \
            --frames=${{ matrix.chunk.start }}-${{ matrix.chunk.end }} \
            --muted \
            --concurrency=2 \
            --codec=h264 \
            --pixel-format=yuv420p \
            --crf=20 \
            --x264-preset=veryfast

      - name: Upload Chunk ${{ matrix.chunk.idx }}
        uses: actions/upload-artifact@v4
        with:
          name: long-chunk-${{ matrix.chunk.idx }}
          path: out/chunk_${{ matrix.chunk.idx }}.mp4
          retention-days: 1

  stitch_final_video:
    needs: [plan_and_prepare, render_workers]
    if: needs.plan_and_prepare.outputs.has_input == 'true'
    runs-on: ubuntu-latest
    timeout-minutes: 15

    steps:
      - name: Checkout Repo
        uses: actions/checkout@v4

      - name: Download Audio & Metadata
        uses: actions/download-artifact@v4
        with:
          name: prepared-long

      - name: Download All Chunks
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

      - name: Stitch Master Video
        env:
          VIDEO_FORMAT: "long_16_9"
        run: python scripts/stitch_chunks.py

      - name: Upload Final 1080p Video
        uses: actions/upload-artifact@v4
        with:
          name: CoreToGrid-Documentary-1080p
          path: |
            out/final_video.mp4
            work/frame0_smoke.png
          retention-days: 7
'''

FILES[".github/workflows/render_short.yml"] = r'''
name: CoreToGrid Shorts Factory (9:16)

on:
  push:
    paths:
      - "input_short/**"
  workflow_dispatch:

concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: false

jobs:
  plan_and_prepare:
    runs-on: ubuntu-latest
    timeout-minutes: 20
    outputs:
      has_input: ${{ steps.check_input.outputs.has_input }}
      chunks_json: ${{ steps.chunk_plan.outputs.chunks_json }}

    steps:
      - name: Checkout
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Check input
        id: check_input
        run: |
          shopt -s nullglob nocaseglob
          files=(input_short/*.mp3 input_short/*.wav input_short/*.m4a)
          echo "has_input=$([ ${#files[@]} -gt 0 ] && echo true || echo false)" >> $GITHUB_OUTPUT

      - name: Setup Python
        if: steps.check_input.outputs.has_input == 'true'
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Setup Node
        if: steps.check_input.outputs.has_input == 'true'
        uses: actions/setup-node@v4
        with:
          node-version: "22"

      - name: Install System & Python Deps
        if: steps.check_input.outputs.has_input == 'true'
        run: |
          sudo apt-get update
          sudo apt-get install -y \
            ffmpeg libnss3 libdbus-1-3 libatk1.0-0 libgbm1 libxrandr2 \
            libxkbcommon0 libxfixes3 libxcomposite1 libxdamage1 \
            libatk-bridge2.0-0 libpango-1.0-0 libcairo2 libcups2 \
            libasound2t64 || sudo apt-get install -y libasound2
          pip install -r requirements.txt
          npm install --no-audit
          npx remotion browser ensure

      - name: Transcribe & Generate Vertical Scenes
        if: steps.check_input.outputs.has_input == 'true'
        env:
          INPUT_FOLDER: "input_short"
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
          OPENROUTER_API_KEY: ${{ secrets.OPENROUTER_API_KEY }}
          GROQ_API_KEY: ${{ secrets.GROQ_API_KEY }}
          VIDEO_FORMAT: "short_9_16"
        run: |
          python scripts/analyze_audio.py
          python scripts/generate_scenes.py
          python scripts/validate_scenes.py
          python scripts/mix_audio.py
          npx remotion still src/index.ts Main work/frame0_smoke.png --frame=0
          npx remotion bundle src/index.ts --public-dir public --out-dir build_bundle
          python scripts/plan_chunks.py

      - name: Upload Short Bundle
        if: steps.check_input.outputs.has_input == 'true'
        uses: actions/upload-artifact@v4
        with:
          name: prepared-short
          path: |
            build_bundle/
            work/master_audio.m4a
            work/scene_plan.json
          retention-days: 2

  render_workers:
    needs: plan_and_prepare
    if: needs.plan_and_prepare.outputs.has_input == 'true'
    runs-on: ubuntu-latest
    timeout-minutes: 30
    strategy:
      fail-fast: false
      matrix:
        chunk: ${{ fromJson(needs.plan_and_prepare.outputs.chunks_json) }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/download-artifact@v4
        with:
          name: prepared-short
      - uses: actions/setup-node@v4
        with:
          node-version: "22"
      - run: |
          sudo apt-get update
          sudo apt-get install -y \
            ffmpeg libnss3 libdbus-1-3 libatk1.0-0 libgbm1 libxrandr2 \
            libxkbcommon0 libxfixes3 libxcomposite1 libxdamage1 \
            libatk-bridge2.0-0 libpango-1.0-0 libcairo2 libcups2 \
            libasound2t64 || sudo apt-get install -y libasound2
          npm install --no-audit
          npx remotion browser ensure
          mkdir -p out
          npx remotion render build_bundle Main out/chunk_${{ matrix.chunk.idx }}.mp4 \
            --frames=${{ matrix.chunk.start }}-${{ matrix.chunk.end }} --muted --concurrency=2
      - uses: actions/upload-artifact@v4
        with:
          name: short-chunk-${{ matrix.chunk.idx }}
          path: out/chunk_${{ matrix.chunk.idx }}.mp4

  stitch_final_short:
    needs: [plan_and_prepare, render_workers]
    if: needs.plan_and_prepare.outputs.has_input == 'true'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/download-artifact@v4
        with:
          name: prepared-short
      - uses: actions/download-artifact@v4
        with:
          pattern: short-chunk-*
          path: chunks
          merge-multiple: true
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: |
          sudo apt-get update && sudo apt-get install -y ffmpeg
          python scripts/stitch_chunks.py
        env:
          VIDEO_FORMAT: "short_9_16"
      - uses: actions/upload-artifact@v4
        with:
          name: CoreToGrid-Short-9-16
          path: out/final_short.mp4
'''


def write_all_files() -> None:
    print(f"[setup_factory] Writing {len(FILES)} CoreToGrid v5.1 files in {ROOT}...")
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
        print("\n[setup_factory] Notice: Initialize git with 'git init' to push to GitHub.")
        return

    git("add", ".")
    if git("diff", "--cached", "--quiet", check=False).returncode != 0:
        git("commit", "-m", "Upgrade v5.1: Multi-Provider Free AI Failover + Hydrogen Pacing + 20-Worker Matrix")
    if git("push", check=False).returncode != 0:
        git("push", "-u", "origin", "HEAD")
    print("\n[setup_factory] SUCCESS! CoreToGrid v5.1 is live on GitHub.")


if __name__ == "__main__":
    write_all_files()
    try:
        run_git_push()
    except subprocess.CalledProcessError as exc:
        print(f"[setup_factory] Git notice: ({exc}). Commit or push manually if needed.")

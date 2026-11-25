#!/usr/bin/env python3
"""
CoreToGrid 2.5D Technical Blueprint Documentary Factory (v5.2).
All-in-one installer & cloud unpacker (--no-git).
"""

import shutil
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

FILES[".agents/skills/coretogrid-director/SKILL.md"] = r'''
---
name: coretogrid-director
description: Directs 2.5D technical CAD blueprint documentaries for CoreToGrid (AI hardware, 800kW racks, power grids).
---

# CoreToGrid Technical Blueprint Director
- Palette: Dark slate blueprint (#070C16), neon cyan coolant (#00F0FF), thermal red (#EF4444), HV amber (#F59E0B).
- Layout discipline: Keep hero schematics in left 65% (x: 60..1240), TelemetryHUD2D + StatCounter2D in right 30% (x: 1310..1850), label all pipes, rotate layouts every 4-6s.
'''

FILES["package.json"] = r'''
{
  "name": "core-to-grid-visual-factory",
  "version": "5.2.0",
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
# Rotate every 4-6s: isometric_blueprint, spec_document, xray_cutaway, thermal_flow, us_grid_map, substation_grid, black_title_card
- Scene 1 [isometric_blueprint]: 2.5D Data Hall with right HUD (1,000 MW, 600 kW, $100B) & labeled 18C/45C pipes.
- Scene 2 [black_title_card]: "The Air Cooling Wall"
- Scene 3 [spec_document]: $100B Capex breakdown document.
- Scene 4 [thermal_flow]: 2.5D Microchannel Cold Plate cross-section with labeled coolant tubes.
- Scene 5 [us_grid_map]: US Grid Map with 345 kV Transformer & SMR nodes.
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

PRO_LADDER = [
    ("gemini-4-hydrogen", "low", 65536, True),
    ("gemini-3.8-flash", None, 32768, True),
]

FLASH_LADDER = [
    ("gemini-4-hydrogen", "low", 65536, True),
    ("gemini-3.8-flash", None, 32768, True),
]

OPENROUTER_FAST_MODELS = [
    "baidu/ernie-5.5-flash-preview:free",
    "openrouter/free",
]

GROQ_FREE_MODELS = [
    "openai/gpt-oss-120b",
    "qwen/qwen3.8-27b",
]

OPENROUTER_HEAVY_MODELS = [
    "nvidia/nemotron-3.5-super-vl:free",
    "nvidia/nemotron-3-ultra-550b-a55b:free",
]

_COOLDOWN_UNTIL: dict[str, float] = {}
_FENCE = "\x60\x60\x60"


def get_client() -> Optional[genai.Client]:
    api_key = (os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY") or "").strip()
    if not api_key:
        return None
    first_key = [k.strip() for k in api_key.split(",") if k.strip()][0]
    return genai.Client(api_key=first_key, http_options=types.HttpOptions(timeout=25_000))


def _strip_think(raw: str) -> str:
    return re.sub(r"<think>[\s\S]*?</think>", "", raw or "").strip()


def clean_json_text(raw: str) -> str:
    text = _strip_think(raw)
    fence_match = re.search(_FENCE + r"(?:json)?\s*([\s\S]*?)" + _FENCE, text)
    if fence_match:
        text = fence_match.group(1).strip()
    if not text.startswith("{") and "{" in text and "}" in text:
        start, end = text.find("{"), text.rfind("}")
        if end > start:
            text = text[start : end + 1]
    return text


def clean_tsx_text(raw: str) -> str:
    text = _strip_think(raw)
    fence_match = re.search(_FENCE + r"(?:tsx|typescript|ts|jsx)?\s*([\s\S]*?)" + _FENCE, text)
    if fence_match:
        text = fence_match.group(1).strip()
    return text


def _call_openai_compat(
    endpoint: str,
    api_key: str,
    model: str,
    prompt: str,
    json_mode: bool,
    timeout_sec: int,
    extra_headers: Optional[dict[str, str]] = None,
) -> str:
    final_prompt = prompt
    if json_mode:
        final_prompt += "\n\nCRITICAL: Return ONLY one valid raw JSON object starting with { and ending with }. No markdown fences."

    payload: dict[str, Any] = {
        "model": model,
        "messages": [{"role": "user", "content": final_prompt}],
        "max_tokens": 16384,
        "temperature": 0.2,
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "User-Agent": "OpenAI/Python",
    }
    if extra_headers:
        headers.update(extra_headers)

    req = urllib.request.Request(endpoint, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as err:
        body = err.read().decode("utf-8", errors="ignore")[:220]
        raise RuntimeError(f"HTTP {err.code}: {body}") from err

    content = data["choices"][0]["message"]["content"]
    if not content or not content.strip():
        raise RuntimeError(f"Empty response from {model}")

    if json_mode:
        cleaned = clean_json_text(content)
        json.loads(cleaned)
        return cleaned
    return content


def _try_openrouter_list(models: list[str], label: str, prompt: str, json_mode: bool, timeout_sec: int) -> Optional[str]:
    or_key = (os.environ.get("OPENROUTER_API_KEY") or "").strip()
    if not or_key:
        return None
    for model in models:
        if _COOLDOWN_UNTIL.get(model, 0) > time.time():
            continue
        try:
            print(f"[ai_router] {label} -> OpenRouter ({model})...", flush=True)
            res = _call_openai_compat(
                "https://openrouter.ai/api/v1/chat/completions",
                or_key,
                model,
                prompt,
                json_mode,
                timeout_sec=timeout_sec,
                extra_headers={"HTTP-Referer": "https://github.com/CoreToGrid", "X-Title": "CoreToGrid"},
            )
            print(f"[ai_router] OpenRouter success with {model} ({len(res)} chars).", flush=True)
            return res
        except Exception as exc:
            msg = str(exc)
            if "429" in msg or "404" in msg:
                _COOLDOWN_UNTIL[model] = time.time() + 120.0
            print(f"[ai_router] OpenRouter {model} skipped ({msg[:160]})", flush=True)
            time.sleep(1)
    return None


def _try_groq(prompt: str, json_mode: bool) -> Optional[str]:
    groq_key = (os.environ.get("GROQ_API_KEY") or "").strip()
    if not groq_key:
        return None
    for model in GROQ_FREE_MODELS:
        if _COOLDOWN_UNTIL.get(model, 0) > time.time():
            continue
        try:
            print(f"[ai_router] Fast Tier -> Groq ({model})...", flush=True)
            res = _call_openai_compat(
                "https://api.groq.com/openai/v1/chat/completions",
                groq_key,
                model,
                prompt,
                json_mode,
                timeout_sec=45,
            )
            print(f"[ai_router] Groq success with {model} ({len(res)} chars).", flush=True)
            return res
        except Exception as exc:
            msg = str(exc)
            if "429" in msg:
                _COOLDOWN_UNTIL[model] = time.time() + 65.0
            print(f"[ai_router] Groq {model} skipped ({msg[:160]})", flush=True)
            time.sleep(1)
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

    for pass_num in range(1, 3):
        if client is not None:
            now = time.time()
            for model_name, thinking_lvl, cap, supports_json in ladder:
                key = f"{model_name}:{thinking_lvl}"
                if key in dead_models or _COOLDOWN_UNTIL.get(model_name, 0) > now:
                    continue

                config_kwargs: dict[str, Any] = {"max_output_tokens": min(cap, max_output_tokens)}
                if "gemini-4" not in model_name:
                    config_kwargs["temperature"] = temperature
                if thinking_lvl:
                    config_kwargs["thinking_config"] = types.ThinkingConfig(thinking_level=thinking_lvl)
                if json_mode and supports_json:
                    config_kwargs["response_mime_type"] = "application/json"

                config = types.GenerateContentConfig(**config_kwargs)
                try:
                    print(f"[ai_router] Priority -> {model_name} (think={thinking_lvl or 'off'})...", flush=True)
                    response = client.models.generate_content(model=model_name, contents=prompt_str, config=config)
                    text = response.text or ""
                    if not text.strip():
                        raise RuntimeError(f"Empty response from {model_name}")
                    if json_mode:
                        cleaned = clean_json_text(text)
                        json.loads(cleaned)
                        print(f"[ai_router] Success with {model_name} ({len(cleaned)} chars).", flush=True)
                        return cleaned
                    print(f"[ai_router] Success with {model_name} ({len(text)} chars).", flush=True)
                    return text
                except APIError as exc:
                    last_error = exc
                    msg = str(exc).lower()
                    if any(k in msg for k in ("404", "403", "400", "not found", "unsupported", "limit: 0")):
                        dead_models.add(key)
                    elif "429" in msg or "quota" in msg or "exhausted" in msg or "503" in msg:
                        _COOLDOWN_UNTIL[model_name] = time.time() + 180.0
                        print(f"[ai_router] {model_name} busy (429/503); pausing 3m & switching...", flush=True)
                except Exception as exc:
                    last_error = exc
                    _COOLDOWN_UNTIL[model_name] = time.time() + 120.0
                    print(f"[ai_router] {model_name} errored ({str(exc)[:120]}); switching...", flush=True)

        fast_or = _try_openrouter_list(OPENROUTER_FAST_MODELS, "Fast Tier", prompt_str, json_mode, timeout_sec=45)
        if fast_or:
            return fast_or

        groq_res = _try_groq(prompt_str, json_mode)
        if groq_res:
            return groq_res

        heavy_or = _try_openrouter_list(OPENROUTER_HEAVY_MODELS, "Backup Tier", prompt_str, json_mode, timeout_sec=90)
        if heavy_or:
            return heavy_or

        if pass_num == 1:
            _COOLDOWN_UNTIL.clear()
            print("[ai_router] All providers busy; waiting 12s before final retry...", flush=True)
            time.sleep(12)

    raise RuntimeError(f"All AI tiers failed. Last error: {last_error}")


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
            cwd=str(ROOT), capture_output=True, text=True, check=False,
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
            "dielectric fluid, CDU, 800 kW, 600 kW, 1.12 PUE, substation, 345 kV, 500 kV, SMR nuclear reactor, busbar, CoWoS."
        ),
    )

    segments: List[Dict[str, Any]] = []
    words: List[Dict[str, Any]] = []
    for seg in segments_iter:
        seg_words: List[Dict[str, Any]] = []
        if seg.words:
            for w in seg.words:
                w_item = {"word": w.word.strip(), "start": round(float(w.start), 3), "end": round(float(w.end), 3)}
                if w_item["word"]:
                    words.append(w_item)
                    seg_words.append(w_item)
        segments.append({"id": seg.id, "start": round(float(seg.start), 3), "end": round(float(seg.end), 3), "text": seg.text.strip(), "words": seg_words})

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
    combined = 0.65 * (rms / (np.max(rms) + 1e-8)) + 0.35 * (onset_env / (np.max(onset_env) + 1e-8))

    peaks, _ = find_peaks(combined, height=float(np.percentile(combined, 68)), distance=max(1, int((1.8 * sr) / hop_length)), prominence=0.09)
    peak_times = [round(float(librosa.frames_to_time(p, sr=sr, hop_length=hop_length)), 3) for p in peaks]

    tempo, _ = librosa.beat.beat_track(onset_envelope=onset_env, sr=sr, hop_length=hop_length)
    bpm_val = float(np.atleast_1d(tempo)[0]) if np.size(tempo) > 0 else 105.0
    if bpm_val < 70 or bpm_val > 135:
        bpm_val = 105.0

    return {"duration_sec": round(duration_sec, 3), "bpm": round(bpm_val, 1), "emphasis_peaks": peak_times}


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
import os
import subprocess
from pathlib import Path
import numpy as np
import soundfile as sf
from scipy.signal import butter, sosfilt

ROOT = Path(__file__).resolve().parent.parent
WORK_DIR = ROOT / "work"
SFX_DIR = ROOT / "public" / "audio" / "sfx"
SAMPLE_RATE = 48000


def lowpass(signal: np.ndarray, cutoff_hz: float, order: int = 4) -> np.ndarray:
    return sosfilt(butter(order, cutoff_hz, btype="low", fs=SAMPLE_RATE, output="sos"), signal)


def bandpass(signal: np.ndarray, low: float, high: float) -> np.ndarray:
    return sosfilt(butter(3, [low, high], btype="band", fs=SAMPLE_RATE, output="sos"), signal)


def synthesize_calm_underscore(n_samples: int, bpm: float) -> np.ndarray:
    t = np.arange(n_samples, dtype=np.float64) / SAMPLE_RATE
    bar_sec = (60.0 / max(75.0, min(125.0, bpm))) * 4.0
    chords = [
        [146.83, 220.00, 261.63, 329.63],
        [116.54, 174.61, 220.00, 293.66],
        [130.81, 196.00, 246.94, 293.66],
        [110.00, 164.81, 220.00, 261.63],
    ]
    bar_idx = (t / bar_sec).astype(int) % len(chords)
    env = np.sin(np.pi * np.clip((t % bar_sec) / bar_sec, 0.0, 1.0)) ** 0.5
    left, right = np.zeros(n_samples), np.zeros(n_samples)
    for c_i, freqs in enumerate(chords):
        mask = (bar_idx == c_i).astype(np.float64)
        sl, sr_sig = np.zeros(n_samples), np.zeros(n_samples)
        for v_i, freq in enumerate(freqs):
            sl += 0.22 * np.sin(2.0 * np.pi * freq * t)
            sr_sig += 0.22 * np.sin(2.0 * np.pi * freq * (1.002 if v_i % 2 == 0 else 0.998) * t + 0.35)
        left += mask * env * sl
        right += mask * env * sr_sig

    beat_period = 60.0 / bpm
    pulse = np.sin(2.0 * np.pi * 146.83 * t) * np.exp(-((t % beat_period) / beat_period) * 14.0) * 0.10
    stereo = np.column_stack([lowpass(left + pulse, 880.0), lowpass(right + pulse, 880.0)])
    stereo = stereo / (float(np.max(np.abs(stereo))) + 1e-9)
    fade_in, fade_out = min(n_samples, int(1.5 * SAMPLE_RATE)), min(n_samples, int(2.0 * SAMPLE_RATE))
    if fade_in > 0:
        stereo[:fade_in] *= np.linspace(0.0, 1.0, fade_in)[:, None]
    if fade_out > 0:
        stereo[-fade_out:] *= np.linspace(1.0, 0.0, fade_out)[:, None]
    return stereo


def load_or_synthesize_sfx() -> dict[str, np.ndarray]:
    rng = np.random.default_rng(42)
    nw = int(0.30 * SAMPLE_RATE)
    w = bandpass(rng.normal(0.0, 1.0, nw), 320.0, 2600.0) * (np.sin(np.pi * (np.arange(nw) / SAMPLE_RATE) / 0.30) ** 1.5)
    whoosh = np.column_stack([w, w * 0.94]) / (np.max(np.abs(w)) + 1e-9)

    npop = int(0.10 * SAMPLE_RATE)
    tp = np.arange(npop) / SAMPLE_RATE
    p = np.sin(2.0 * np.pi * np.cumsum(420.0 + 520.0 * (1.0 - np.exp(-tp * 40.0))) / SAMPLE_RATE) * np.exp(-tp * 34.0)
    pop = np.column_stack([p, p]) / (np.max(np.abs(p)) + 1e-9)

    nt = int(0.06 * SAMPLE_RATE)
    tt = np.arange(nt) / SAMPLE_RATE
    tk = np.sin(2.0 * np.pi * 1950.0 * tt) * np.exp(-tt * 85.0)
    tick = np.column_stack([tk, tk]) / (np.max(np.abs(tk)) + 1e-9)

    na = int(0.24 * SAMPLE_RATE)
    ta = np.arange(na) / SAMPLE_RATE
    al = (np.sin(2.0 * np.pi * 1180.0 * ta) + 0.5 * np.sin(2.0 * np.pi * 1760.0 * ta)) * np.exp(-ta * 16.0)
    alert = np.column_stack([al, al]) / (np.max(np.abs(al)) + 1e-9)

    ni = int(0.45 * SAMPLE_RATE)
    ti = np.arange(ni) / SAMPLE_RATE
    im = np.sin(2.0 * np.pi * np.cumsum(100.0 * np.exp(-ti * 4.8) + 36.0) / SAMPLE_RATE) * np.exp(-ti * 5.8) * np.minimum(1.0, ti / 0.01)
    impact = np.column_stack([im, im]) / (np.max(np.abs(im)) + 1e-9)

    bank = {"whoosh": whoosh * 0.14, "pop": pop * 0.16, "tick": tick * 0.12, "alert": alert * 0.14, "impact": impact * 0.22}
    for name in list(bank.keys()):
        custom_wav = SFX_DIR / f"{name}.wav"
        if custom_wav.exists():
            data, sr = sf.read(str(custom_wav), dtype="float64")
            if sr == SAMPLE_RATE:
                if data.ndim == 1:
                    data = np.column_stack([data, data])
                bank[name] = (data / (float(np.max(np.abs(data))) + 1e-9)) * 0.18
    return bank


def place_sfx(mix: np.ndarray, snd: np.ndarray, sec: float) -> None:
    s = max(0, int(sec * SAMPLE_RATE))
    e = min(len(mix), s + len(snd))
    if e > s:
        mix[s:e] += snd[: e - s]


def main() -> None:
    plan = json.loads((WORK_DIR / "scene_plan.json").read_text(encoding="utf-8"))
    vo, _ = sf.read(str(WORK_DIR / "clean_voiceover.wav"), dtype="float64")
    if vo.ndim > 1:
        vo = np.mean(vo, axis=1)

    n_samples = len(vo)
    vo_stereo = np.column_stack([vo, vo])
    include_bgm = os.environ.get("INCLUDE_BGM", "true").lower() == "true"

    if include_bgm:
        smooth_env = lowpass(np.abs(vo), 3.0)
        speech_active = np.clip(smooth_env / (np.percentile(smooth_env, 90) + 1e-6), 0.0, 1.0)
        duck_gain = 0.085 - 0.048 * speech_active
        mix = vo_stereo * 0.92 + synthesize_calm_underscore(n_samples, float(plan.get("bpm", 105.0))) * duck_gain[:, None]
    else:
        mix = vo_stereo * 0.94

    bank = load_or_synthesize_sfx()
    for sc in plan.get("scenes", []):
        place_sfx(mix, bank.get(sc.get("sfx", "whoosh"), bank["whoosh"]), float(sc["startSec"]))
        if sc.get("statCounter"):
            place_sfx(mix, bank["pop"], float(sc["startSec"]) + float(sc["statCounter"].get("triggerSec", 0.15)))
        if sc.get("stampText"):
            place_sfx(mix, bank["alert"], float(sc["startSec"]) + float(sc.get("stampTriggerSec", 0.65)))

    for idx, p_sec in enumerate(plan.get("emphasisPeaksSec", [])):
        place_sfx(mix, bank["impact" if idx % 5 == 0 else "tick"], float(p_sec))

    mix = np.tanh(mix * 0.95)
    master_m4a, tmp_wav = WORK_DIR / "master_audio.m4a", WORK_DIR / "temp_master.wav"
    sf.write(str(tmp_wav), mix, SAMPLE_RATE, subtype="PCM_16")
    subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(tmp_wav), "-c:a", "aac", "-b:a", "192k", "-ar", str(SAMPLE_RATE), str(master_m4a)], check=True)
    tmp_wav.unlink(missing_ok=True)
    print(f"[mix_audio] Master mix complete: {n_samples / SAMPLE_RATE:.2f}s (BGM={include_bgm}).")


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
    elif total_frames <= 1800:
        workers = 4
    elif total_frames <= 5400:
        workers = 8
    elif total_frames <= 13500:
        workers = 14
    else:
        workers = 20

    workers = min(workers, total_frames)
    chunk_size = math.ceil(total_frames / workers)
    chunks = [{"idx": i, "start": i * chunk_size, "end": min(total_frames - 1, (i + 1) * chunk_size - 1)} for i in range(workers) if i * chunk_size <= total_frames - 1]
    print(f"[plan_chunks] total_frames={total_frames}, parallel_workers={len(chunks)}")

    gh_out = os.environ.get("GITHUB_OUTPUT")
    if gh_out:
        with open(gh_out, "a", encoding="utf-8") as f:
            f.write(f"total_frames={total_frames}\nworker_count={len(chunks)}\nchunks_json={json.dumps(chunks)}\n")


if __name__ == "__main__":
    main()
'''

FILES["scripts/stitch_chunks.py"] = r'''
import os
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHUNKS_DIR, WORK_DIR, OUT_DIR = ROOT / "chunks", ROOT / "work", ROOT / "out"


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

    out_name = "final_short.mp4" if os.environ.get("VIDEO_FORMAT", "long_16_9").strip() == "short_9_16" else "final_video.mp4"
    final_mp4 = OUT_DIR / out_name
    subprocess.run([
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "warning",
        "-f", "concat", "-safe", "0", "-i", str(list_file), "-i", str(WORK_DIR / "master_audio.m4a"),
        "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy", "-c:a", "copy", "-movflags", "+faststart", "-shortest", str(final_mp4)
    ], check=True)
    print(f"[stitch_chunks] SUCCESS! Exported {final_mp4} ({final_mp4.stat().st_size / (1024*1024):.1f} MB)")


if __name__ == "__main__":
    main()
'''

FILES["src/types.ts"] = r'''
export type BackdropTheme =
  | "isometric_blueprint" | "xray_cutaway" | "substation_grid" | "cleanroom_fab"
  | "thermal_flow" | "server_corridor" | "dark_industrial" | "spec_document"
  | "us_grid_map" | "black_title_card" | "split_3panel";

export type CameraMove2D = "push_in" | "pull_out" | "pan_right" | "pan_left" | "pan_up" | "shake_hit";
export type Transition2D = "slide_left" | "slide_up" | "wipe_right" | "zoom_dissolve" | "flash_cut";

export interface StatCounterSpec {
  label: string;
  startVal: number;
  endVal: number;
  prefix?: string;
  suffix?: string;
  decimals?: number;
  color?: string;
  triggerSec?: number;
}

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
  chapterTag: string;
  isVertical: boolean;
}

export interface CartoonScene {
  id: string;
  componentName: string;
  chapterTag: string;
  visualConcept: string;
  visualSpec: string;
  titleText: string;
  stampText?: string;
  stampColor?: string;
  stampTriggerSec?: number;
  statCounter?: StatCounterSpec;
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
  emphasisPeaksSec?: number[];
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
const INK = "#060A12";
const BLUEPRINT_LINE = "#18243A";

function formatNumber(val: number, decimals = 0, prefix = "", suffix = ""): string {
  const fixed = Number(val.toFixed(decimals));
  return `${prefix}${fixed.toLocaleString("en-US", { minimumFractionDigits: decimals, maximumFractionDigits: decimals })}${suffix}`;
}

export const SceneBackdrop2D: React.FC<{
  theme: BackdropTheme;
  frame: number;
  accentHex?: string;
  chapterTag?: string;
}> = ({ theme, frame, accentHex = "#00F0FF", chapterTag = "01 // CORE TO GRID" }) => {
  if (theme === "black_title_card") {
    return <rect x={-100} y={-100} width={2200} height={2200} fill="#04070E" />;
  }
  const pillW = Math.max(320, chapterTag.length * 14 + 70);
  const chapterOverlay = (
    <g transform="translate(52 38)">
      <rect x={0} y={0} width={pillW} height={46} rx={8} fill="#09101E" fillOpacity={0.94} stroke={accentHex} strokeWidth={2} />
      <circle cx={24} cy={23} r={6} fill={accentHex} opacity={0.6 + 0.4 * Math.sin(frame * 0.25)} />
      <text x={44} y={29} fill="#F8FAFC" fontFamily={MONO_FONT} fontSize={19} fontWeight={700} letterSpacing={1}>{chapterTag.toUpperCase()}</text>
    </g>
  );

  if (theme === "isometric_blueprint" || theme === "thermal_flow") {
    return (
      <g>
        <rect x={-100} y={-100} width={2200} height={2200} fill="#070C16" />
        {Array.from({ length: 30 }).map((_, i) => <line key={`a${i}`} x1={-200 + i * 120} y1={-100} x2={-200 + i * 120 + 1200} y2={2100} stroke={BLUEPRINT_LINE} strokeWidth={1.5} strokeDasharray="4 8" />)}
        {Array.from({ length: 30 }).map((_, i) => <line key={`b${i}`} x1={2200 - i * 120} y1={-100} x2={2200 - i * 120 - 1200} y2={2100} stroke={BLUEPRINT_LINE} strokeWidth={1.5} strokeDasharray="4 8" />)}
        <rect x={36} y={24} width={1848} height={1032} rx={12} fill="none" stroke="#1E293B" strokeWidth={2} />
        {chapterOverlay}
      </g>
    );
  }
  if (theme === "spec_document" || theme === "us_grid_map" || theme === "xray_cutaway" || theme === "split_3panel") {
    return (
      <g>
        <rect x={-100} y={-100} width={2200} height={2200} fill="#08101E" />
        {Array.from({ length: 24 }).map((_, i) => <line key={i} x1={i * 90} y1={-50} x2={i * 90} y2={2050} stroke="#132036" strokeWidth={1.5} />)}
        <rect x={44} y={28} width={1832} height={1024} fill="none" stroke={accentHex} strokeWidth={2} strokeOpacity={0.22} strokeDasharray="10 8" />
        {chapterOverlay}
      </g>
    );
  }
  if (theme === "substation_grid") {
    return (
      <g>
        <rect x={-100} y={-100} width={2200} height={2200} fill="#080C16" />
        <rect x={-50} y={770} width={2100} height={1300} fill="#0F172A" stroke={INK} strokeWidth={4} />
        {[-40, 20, 80].map((yOff, i) => <line key={i} x1={-100} y1={260 + yOff} x2={2100} y2={260 + yOff} stroke="#F59E0B" strokeWidth={3} strokeDasharray="18 12" strokeDashoffset={-frame * 2.5} />)}
        {chapterOverlay}
      </g>
    );
  }
  return (
    <g>
      <rect x={-100} y={-100} width={2200} height={2200} fill="#080D17" />
      {[240, 640, 1280, 1680].map((lx, i) => <rect key={i} x={lx - 60} y={24} width={120} height={12} rx={4} fill={accentHex} opacity={0.85} />)}
      <rect x={-50} y={830} width={2100} height={1200} fill="#111827" stroke={INK} strokeWidth={4} />
      <line x1={-50} y1={830} x2={2050} y2={830} stroke={accentHex} strokeWidth={4} />
      {chapterOverlay}
    </g>
  );
};

export const Camera2D: React.FC<{
  move: CameraMove2D; progress: number; frame: number; peakTimes?: number[]; localTime: number; children?: React.ReactNode;
}> = ({ move, progress, frame, peakTimes = [], localTime, children }) => {
  const ease = progress * progress * (3 - 2 * progress);
  let scale = 1, tx = 0, ty = 0;
  if (move === "push_in") scale = 1 + ease * 0.06;
  else if (move === "pull_out") scale = 1.07 - ease * 0.07;
  else if (move === "pan_right") { scale = 1.03; tx = 24 - ease * 48; }
  else if (move === "pan_left") { scale = 1.03; tx = -24 + ease * 48; }
  else if (move === "pan_up") { scale = 1.03; ty = 20 - ease * 40; }

  let shake = 0;
  for (const pt of peakTimes) {
    const dt = localTime - pt;
    if (dt >= 0 && dt < 0.25) shake += Math.sin(frame * 2.8) * 6 * (1 - dt / 0.25);
  }
  return <g transform={`translate(${960 + tx + shake} ${540 + ty + shake}) scale(${scale}) translate(-960 -540)`}>{children}</g>;
};

export const TelemetryHUD2D: React.FC<{
  x: number; y: number; w?: number; title: string;
  metrics: { label: string; value: string; unit?: string; alert?: boolean; barPct?: number }[]; progress: number;
}> = ({ x, y, w = 540, title, metrics, progress }) => {
  const p = Math.min(1, progress * 1.6);
  const h = 76 + metrics.length * 78;
  return (
    <g transform={`translate(${x} ${y}) scale(${0.94 + 0.06 * p})`} opacity={p}>
      <rect x={12} y={14} width={w} height={h} rx={14} fill="#000000" opacity={0.55} />
      <rect x={0} y={0} width={w} height={h} rx={14} fill="#09101F" fillOpacity={0.95} stroke="#38BDF8" strokeWidth={2.5} />
      <rect x={0} y={0} width={w} height={48} rx={14} fill="#111D35" />
      <circle cx={24} cy={24} r={6} fill="#00F0FF" />
      <text x={44} y={30} fill="#F1F5F9" fontFamily={UI_FONT} fontSize={20} fontWeight={700}>{title}</text>
      {metrics.map((m, idx) => {
        const col = m.alert ? "#EF4444" : "#00F0FF";
        const pct = Math.max(12, Math.min(100, m.barPct ?? (m.alert ? 92 : 68))) * p;
        return (
          <g key={idx} transform={`translate(24 ${76 + idx * 78})`}>
            <text x={0} y={18} fill="#94A3B8" fontFamily={MONO_FONT} fontSize={17}>{m.label}</text>
            <text x={w - 48} y={20} textAnchor="end" fill={col} fontFamily={MONO_FONT} fontSize={26} fontWeight={700}>{m.value} {m.unit || ""}</text>
            <rect x={0} y={34} width={w - 48} height={8} rx={4} fill="#1E293B" />
            <rect x={0} y={34} width={((w - 48) * pct) / 100} height={8} rx={4} fill={col} />
          </g>
        );
      })}
    </g>
  );
};

export const StatCounter2D: React.FC<{
  x: number; y: number; w?: number; label: string; startVal: number; endVal: number;
  prefix?: string; suffix?: string; decimals?: number; color?: string; localTime: number; triggerSec?: number;
}> = ({ x, y, w = 540, label, startVal, endVal, prefix = "", suffix = "", decimals = 0, color = "#00F0FF", localTime, triggerSec = 0.1 }) => {
  const { fps } = useVideoConfig();
  const elapsed = Math.max(0, localTime - triggerSec);
  const ease = 1 - Math.pow(1 - Math.min(1, elapsed / 0.85), 3);
  const pop = spring({ frame: Math.max(0, Math.round(elapsed * fps)), fps, config: { damping: 14, stiffness: 200 } });
  return (
    <g transform={`translate(${x} ${y}) scale(${0.92 + 0.08 * pop})`}>
      <rect x={-w / 2 + 10} y={-68} width={w} height={160} rx={14} fill="#000000" opacity={0.55} />
      <rect x={-w / 2} y={-80} width={w} height={160} rx={14} fill="#0A1222" fillOpacity={0.96} stroke={color} strokeWidth={3} />
      <text x={0} y={-32} textAnchor="middle" fill="#94A3B8" fontFamily={MONO_FONT} fontSize={20} fontWeight={700}>{label.toUpperCase()}</text>
      <text x={0} y={42} textAnchor="middle" fill={color} fontFamily={MONO_FONT} fontSize={64} fontWeight={700}>{formatNumber(startVal + (endVal - startVal) * ease, decimals, prefix, suffix)}</text>
    </g>
  );
};

export const BlueprintStamp2D: React.FC<{
  x: number; y: number; text: string; color?: string; rotateDeg?: number; localTime: number; triggerSec?: number;
}> = ({ x, y, text, color = "#EF4444", rotateDeg = -7, localTime, triggerSec = 0.6 }) => {
  const { fps } = useVideoConfig();
  if (localTime < triggerSec) return null;
  const slam = spring({ frame: Math.max(0, Math.round((localTime - triggerSec) * fps)), fps, config: { damping: 11, stiffness: 280, mass: 0.7 } });
  const stampW = Math.max(300, text.length * 26 + 64);
  return (
    <g transform={`translate(${x} ${y}) rotate(${rotateDeg}) scale(${1.65 - 0.65 * slam})`} opacity={Math.min(1, slam * 1.4)}>
      <rect x={-stampW / 2 + 8} y={-36} width={stampW} height={88} rx={10} fill="#000000" opacity={0.65} />
      <rect x={-stampW / 2} y={-44} width={stampW} height={88} rx={10} fill="#080D18" fillOpacity={0.94} stroke={color} strokeWidth={6} />
      <rect x={-stampW / 2 + 8} y={-36} width={stampW - 16} height={72} rx={6} fill="none" stroke={color} strokeWidth={2} strokeDasharray="8 6" />
      <text x={0} y={14} textAnchor="middle" fill={color} fontFamily={MONO_FONT} fontSize={36} fontWeight={700}>{text.toUpperCase()}</text>
    </g>
  );
};

export const ServerRack800kW2D: React.FC<{
  x: number; y: number; scale?: number; accentHex?: string; frame: number; progress: number;
}> = ({ x, y, scale = 1, accentHex = "#00F0FF", frame, progress }) => (
  <g transform={`translate(${x} ${y}) scale(${scale})`}>
    <polygon points="-100,255 115,255 150,235 -65,235" fill="#000000" opacity={0.6} />
    <polygon points="100,-240 132,-260 132,230 100,250" fill="#070B14" stroke="#334155" strokeWidth={3} />
    <polygon points="-100,-240 -68,-260 132,-260 100,-240" fill="#1E293B" stroke="#475569" strokeWidth={3} />
    <rect x={-100} y={-240} width={200} height={490} rx={4} fill="#0D1424" stroke="#475569" strokeWidth={4} />
    <rect x={-10} y={-225} width={20} height={460 * Math.min(1, progress + 0.2)} fill="#B45309" stroke="#F59E0B" strokeWidth={2} />
    {[-195, -130, -65, 0, 65, 130, 195].map((ry, i) => {
      const active = Math.sin(frame * 0.2 - i) > -0.15;
      return (
        <g key={i}>
          <rect x={-84} y={ry - 22} width={168} height={44} rx={3} fill="#162033" stroke="#334155" strokeWidth={2} />
          <circle cx={-66} cy={ry} r={5} fill={active ? accentHex : "#334155"} />
          <line x1={-48} y1={ry} x2={52} y2={ry} stroke={active ? "#38BDF8" : "#334155"} strokeWidth={3} strokeDasharray="8 6" />
        </g>
      );
    })}
  </g>
);

export const AnimatedFluidPipe2D: React.FC<{
  d: string; color?: string; fluidColor?: string; strokeWidth?: number; label?: string; labelX?: number; labelY?: number; frame: number;
}> = ({ d, color = "#24324B", fluidColor = "#00F0FF", strokeWidth = 24, label, labelX, labelY, frame }) => {
  const badgeW = label ? Math.max(240, label.length * 12.5 + 36) : 0;
  return (
    <g>
      <path d={d} fill="none" stroke="#04070E" strokeWidth={strokeWidth + 8} strokeLinecap="round" strokeLinejoin="round" />
      <path d={d} fill="none" stroke={color} strokeWidth={strokeWidth} strokeLinecap="round" strokeLinejoin="round" />
      <path d={d} fill="none" stroke={fluidColor} strokeWidth={strokeWidth * 0.42} strokeDasharray="22 16" strokeDashoffset={-frame * 6.5} strokeLinecap="round" />
      {label && labelX !== undefined && labelY !== undefined && (
        <g transform={`translate(${labelX} ${labelY})`}>
          <rect x={-badgeW / 2} y={-20} width={badgeW} height={38} rx={6} fill="#080E1B" fillOpacity={0.95} stroke={fluidColor} strokeWidth={2} />
          <text x={0} y={5} textAnchor="middle" fill={fluidColor} fontFamily={MONO_FONT} fontSize={16} fontWeight={700}>{label}</text>
        </g>
      )}
    </g>
  );
};

export const DataHall25D: React.FC<{
  accentHex?: string; frame: number; progress: number; isVertical?: boolean;
}> = ({ accentHex = "#00F0FF", frame, progress, isVertical = false }) => {
  const backRow = isVertical ? [220, 420, 620, 820] : [170, 360, 550, 740, 930, 1120];
  const frontRow = isVertical ? [270, 490, 710] : [230, 430, 630, 830, 1030];
  return (
    <g>
      <polygon points={isVertical ? "60,640 1020,640 1050,1240 30,1240" : "70,480 1230,480 1260,860 40,860"} fill="#0B1222" stroke="#1E293B" strokeWidth={3} />
      <AnimatedFluidPipe2D d={isVertical ? "M 140 520 L 940 520" : "M 120 260 L 1180 260"} color="#334155" fluidColor="#F59E0B" strokeWidth={18} label="48V DC BUSWAY" labelX={isVertical ? 540 : 650} labelY={isVertical ? 485 : 225} frame={frame} />
      {backRow.map((rx, i) => <ServerRack800kW2D key={`br${i}`} x={rx} y={isVertical ? 760 : 480} scale={0.48} accentHex={accentHex} frame={frame + i * 3} progress={progress} />)}
      {frontRow.map((rx, i) => <ServerRack800kW2D key={`fr${i}`} x={rx} y={isVertical ? 1020 : 690} scale={0.62} accentHex={accentHex} frame={frame + i * 5} progress={progress} />)}
      <AnimatedFluidPipe2D d={isVertical ? "M 100 1320 L 980 1320" : "M 80 910 L 1220 910"} fluidColor="#00F0FF" strokeWidth={22} label="CHILLED COOLANT IN -> 18C" labelX={isVertical ? 540 : 420} labelY={isVertical ? 1278 : 872} frame={frame} />
      <AnimatedFluidPipe2D d={isVertical ? "M 980 1420 L 100 1420" : "M 1220 995 L 80 995"} fluidColor="#EF4444" strokeWidth={22} label="<- HEATED RETURN 45C" labelX={isVertical ? 540 : 880} labelY={isVertical ? 1465 : 1035} frame={frame} />
    </g>
  );
};

export const SpecDocument2D: React.FC<{
  x: number; y: number; w?: number; title: string; subtitle?: string;
  items: { label: string; value: string; pct: number; color?: string }[]; progress: number;
}> = ({ x, y, w = 1120, title, subtitle = "ARCHITECTURAL ALLOCATION", items, progress }) => {
  const ease = Math.min(1, progress * 1.45);
  const h = 150 + items.length * 135;
  return (
    <g transform={`translate(${x} ${y})`}>
      <rect x={16} y={18} width={w} height={h} rx={16} fill="#000000" opacity={0.6} />
      <rect x={0} y={0} width={w} height={h} rx={16} fill="#0A1120" fillOpacity={0.96} stroke="#38BDF8" strokeWidth={3} />
      <rect x={0} y={0} width={w} height={74} rx={14} fill="#111C33" />
      <circle cx={38} cy={37} r={10} fill="#00F0FF" />
      <text x={68} y={44} fill="#F8FAFC" fontFamily={UI_FONT} fontSize={28} fontWeight={700}>{title}</text>
      <text x={w - 36} y={44} textAnchor="end" fill="#38BDF8" fontFamily={MONO_FONT} fontSize={18} fontWeight={700}>{subtitle}</text>
      {items.map((it, idx) => {
        const col = it.color || "#00F0FF";
        return (
          <g key={idx} transform={`translate(48 ${115 + idx * 135})`}>
            <text x={0} y={24} fill="#E2E8F0" fontFamily={UI_FONT} fontSize={26} fontWeight={700}>{it.label}</text>
            <text x={w - 96} y={26} textAnchor="end" fill={col} fontFamily={MONO_FONT} fontSize={32} fontWeight={700}>{it.value}</text>
            <rect x={0} y={46} width={w - 96} height={30} rx={6} fill="#162238" stroke="#1E293B" strokeWidth={2} />
            <rect x={0} y={46} width={((w - 96) * Math.min(100, it.pct) * ease) / 100} height={30} rx={6} fill={col} />
          </g>
        );
      })}
    </g>
  );
};

export const USGridMap2D: React.FC<{
  x: number; y: number; w?: number; h?: number; accentHex?: string; frame: number; progress: number;
}> = ({ x, y, w = 1140, h = 680, accentHex = "#F59E0B", frame, progress }) => {
  const nodes = [
    { nx: x + 0.16 * w, ny: y + 0.48 * h, tag: "WEST 500 kV", col: "#00F0FF" },
    { nx: x + 0.48 * w, ny: y + 0.72 * h, tag: "ERCOT TEXAS", col: "#EF4444" },
    { nx: x + 0.62 * w, ny: y + 0.34 * h, tag: "MIDWEST SMR", col: "#10B981" },
    { nx: x + 0.82 * w, ny: y + 0.42 * h, tag: "PJM VIRGINIA", col: "#F59E0B" },
  ];
  return (
    <g>
      <rect x={x + 12} y={y + 14} width={w} height={h} rx={16} fill="#000000" opacity={0.55} />
      <rect x={x} y={y} width={w} height={h} rx={16} fill="#08101E" stroke="#1E293B" strokeWidth={3} />
      <polygon points={`${x + 0.08 * w},${y + 0.22 * h} ${x + 0.45 * w},${y + 0.18 * h} ${x + 0.75 * w},${y + 0.22 * h} ${x + 0.92 * w},${y + 0.16 * h} ${x + 0.88 * w},${y + 0.56 * h} ${x + 0.78 * w},${y + 0.84 * h} ${x + 0.65 * w},${y + 0.72 * h} ${x + 0.48 * w},${y + 0.88 * h} ${x + 0.24 * w},${y + 0.68 * h} ${x + 0.08 * w},${y + 0.54 * h}`} fill="#101B30" stroke="#38BDF8" strokeWidth={3} />
      <path d={`M ${nodes[0].nx} ${nodes[0].ny} L ${nodes[1].nx} ${nodes[1].ny} L ${nodes[3].nx} ${nodes[3].ny} L ${nodes[2].nx} ${nodes[2].ny} Z`} fill="none" stroke={accentHex} strokeWidth={5} strokeDasharray="16 12" strokeDashoffset={-frame * 4} />
      {nodes.map((n, i) => (
        <g key={i} transform={`translate(${n.nx} ${n.ny})`}>
          <circle cx={0} cy={0} r={(18 + Math.sin(frame * 0.2 + i) * 6) * Math.min(1, progress * 1.5)} fill={n.col} opacity={0.25} />
          <circle cx={0} cy={0} r={12} fill={n.col} stroke="#060A12" strokeWidth={3} />
          <rect x={-78} y={-48} width={156} height={28} rx={5} fill="#060B15" stroke={n.col} strokeWidth={2} />
          <text x={0} y={-29} textAnchor="middle" fill="#F8FAFC" fontFamily={MONO_FONT} fontSize={14} fontWeight={700}>{n.tag}</text>
        </g>
      ))}
    </g>
  );
};

export const MicrochannelColdPlate2D: React.FC<{
  x: number; y: number; scale?: number; coolantTempC?: number; frame: number; progress: number;
}> = ({ x, y, scale = 1, coolantTempC = 45, frame, progress }) => {
  const lift = Math.min(1, progress * 1.4) * 58;
  const shift = (frame * 3) % 24;
  return (
    <g transform={`translate(${x} ${y}) scale(${scale})`}>
      <polygon points="180,60 210,42 210,102 180,120" fill="#0F172A" stroke="#00F0FF" strokeWidth={2} />
      <rect x={-180} y={60} width={360} height={60} rx={4} fill="#1E293B" stroke="#00F0FF" strokeWidth={3} />
      <text x={0} y={98} textAnchor="middle" fill="#00F0FF" fontFamily={MONO_FONT} fontSize={20} fontWeight={700}>SILICON DIE // {coolantTempC}C EXIT</text>
      <polygon points="210,0 240,-18 240,30 210,48" fill="#78350F" stroke="#F59E0B" strokeWidth={2} />
      <rect x={-210} y={0} width={420} height={48} rx={4} fill="#B45309" stroke="#F59E0B" strokeWidth={3} />
      {Array.from({ length: 32 }).map((_, i) => <rect key={i} x={-190 + i * 12} y={-40} width={6} height={40} fill={i % 2 === 0 ? "#D97706" : "#38BDF8"} opacity={0.75 + 0.25 * Math.sin(shift + i)} />)}
      <g transform={`translate(0 ${-lift})`}>
        <polygon points="-220,-90 -190,-108 250,-108 220,-90" fill="#475569" stroke="#94A3B8" strokeWidth={2} />
        <polygon points="220,-90 250,-108 250,-62 220,-44" fill="#1E293B" stroke="#94A3B8" strokeWidth={2} />
        <rect x={-220} y={-90} width={440} height={46} rx={6} fill="#334155" stroke="#94A3B8" strokeWidth={3} />
        <circle cx={-130} cy={-67} r={18} fill="#00F0FF" />
        <text x={-130} y={-62} textAnchor="middle" fill="#060A12" fontFamily={MONO_FONT} fontSize={12} fontWeight={700}>18C</text>
        <circle cx={130} cy={-67} r={18} fill="#EF4444" />
        <text x={130} y={-62} textAnchor="middle" fill="#060A12" fontFamily={MONO_FONT} fontSize={12} fontWeight={700}>{coolantTempC}C</text>
      </g>
    </g>
  );
};

export const TransformerSubstation2D: React.FC<{
  x: number; y: number; scale?: number; voltageKV?: number; frame: number;
}> = ({ x, y, scale = 1, voltageKV = 345, frame }) => (
  <g transform={`translate(${x} ${y}) scale(${scale})`}>
    <polygon points="-150,165 165,165 205,140 -110,140" fill="#000000" opacity={0.55} />
    <polygon points="160,-100 198,-124 198,136 160,160" fill="#0D1424" stroke="#475569" strokeWidth={4} />
    <polygon points="-160,-100 -122,-124 198,-124 160,-100" fill="#334155" stroke="#64748B" strokeWidth={3} />
    <rect x={-160} y={-100} width={320} height={260} rx={8} fill="#1E293B" stroke="#475569" strokeWidth={5} />
    {[-140, -100, -60, 60, 100, 140].map((fx, i) => <line key={i} x1={fx} y1={-80} x2={fx} y2={140} stroke="#334155" strokeWidth={8} />)}
    {[-80, 0, 80].map((bx, i) => (
      <g key={i} transform={`translate(${bx} -100)`}>
        <polygon points="-16,0 16,0 8,-90 -8,-90" fill="#94A3B8" stroke="#334155" strokeWidth={3} />
        <circle cx={0} cy={-98} r={12} fill="#F59E0B" opacity={0.7 + 0.3 * Math.sin(frame * 0.3 + i)} />
        <line x1={0} y1={-100} x2={bx * 1.5} y2={-160} stroke="#F59E0B" strokeWidth={4} strokeDasharray="6 4" />
      </g>
    ))}
    <rect x={-95} y={36} width={190} height={44} rx={6} fill="#080E1B" stroke="#F59E0B" strokeWidth={2.5} />
    <text x={0} y={65} textAnchor="middle" fill="#F59E0B" fontFamily={MONO_FONT} fontSize={18} fontWeight={700}>{voltageKV} kV STEP-DOWN</text>
  </g>
);

export const NuclearSMRVessel2D: React.FC<{
  x: number; y: number; scale?: number; cherenkovGlow?: boolean; frame: number; progress: number;
}> = ({ x, y, scale = 1, cherenkovGlow = true, frame, progress }) => (
  <g transform={`translate(${x} ${y}) scale(${scale})`}>
    <ellipse cx={16} cy={186} rx={138} ry={22} fill="#000000" opacity={0.55} />
    <path d="M 120 -80 L 148 -98 L 148 162 L 120 180 Z" fill="#0B1120" stroke="#475569" strokeWidth={4} />
    <path d="M -120 -80 Q -120 -220 0 -220 Q 120 -220 120 -80 L 120 180 L -120 180 Z" fill="#1E293B" stroke="#475569" strokeWidth={6} />
    <rect x={-75} y={-30} width={150} height={160} rx={12} fill="#0284C7" stroke="#38BDF8" strokeWidth={4} />
    {cherenkovGlow && <rect x={-65} y={-20} width={130} height={140} rx={8} fill="#00F0FF" opacity={(0.75 + 0.25 * Math.sin(frame * 0.2)) * 0.85} />}
    {[-32, 0, 32].map((rx, i) => <rect key={i} x={rx - 8} y={-110 + Math.sin(frame * 0.1) * 18 * Math.min(1, progress * 1.5)} width={16} height={110} rx={4} fill="#FACC15" stroke="#713F12" strokeWidth={2} />)}
  </g>
);

export const TechnicalCallout2D: React.FC<{
  x: number; y: number; text: string; subtext?: string; color?: string; localTime: number; delaySec?: number; arrowTo?: [number, number];
}> = ({ x, y, text, subtext, color = "#00F0FF", localTime, delaySec = 0, arrowTo }) => {
  const { fps } = useVideoConfig();
  if (localTime < delaySec) return null;
  const pop = spring({ frame: Math.max(0, Math.round((localTime - delaySec) * fps)), fps, config: { damping: 14, stiffness: 180 } });
  const w = Math.max(220, text.length * 14 + 32);
  return (
    <g transform={`translate(${x} ${y}) scale(${pop})`}>
      {arrowTo && <line x1={0} y1={0} x2={arrowTo[0] - x} y2={arrowTo[1] - y} stroke={color} strokeWidth={2.5} strokeDasharray="5 5" />}
      <rect x={-16} y={-26} width={w} height={subtext ? 64 : 42} rx={6} fill="#080E1B" stroke={color} strokeWidth={2.5} />
      <text x={0} y={0} fill={color} fontFamily={MONO_FONT} fontSize={19} fontWeight={700}>{text}</text>
      {subtext && <text x={0} y={24} fill="#94A3B8" fontFamily={UI_FONT} fontSize={14}>{subtext}</text>}
    </g>
  );
};

export const TitleCard2D: React.FC<{ text: string; progress: number; accentHex?: string }> = ({ text, progress, accentHex = "#00F0FF" }) => (
  <g transform={`translate(960 540) scale(${0.94 + Math.min(1, progress * 2.2) * 0.06})`}>
    <text x={0} y={10} textAnchor="middle" fill="#FFFFFF" fontFamily={UI_FONT} fontSize={84} fontWeight={700}>{text}</text>
    <line x1={-340 * Math.min(1, progress * 1.6)} y1={64} x2={340 * Math.min(1, progress * 1.6)} y2={64} stroke={accentHex} strokeWidth={7} strokeLinecap="round" />
  </g>
);

export const LineChart2D: React.FC<{
  x: number; y: number; w?: number; h?: number; label?: string; startVal?: number; endVal?: number;
  prefix?: string; suffix?: string; decimals?: number; color?: string; progress: number;
}> = ({ x, y, w = 960, h = 440, label = "SURGE", startVal = 0, endVal = 100, prefix = "", suffix = "", decimals = 0, color = "#EF4444", progress }) => {
  const drawProg = Math.min(1, progress * 1.4);
  const d = `M ${x + 40} ${y + h - 30} Q ${x + w * 0.45} ${y + h * 0.72} ${x + w - 40} ${y + 90}`;
  return (
    <g>
      <rect x={x - 12} y={y - 12} width={w + 24} height={h + 44} rx={12} fill="#080E1B" fillOpacity={0.95} stroke="#1E293B" strokeWidth={3} />
      <path d={d} fill="none" stroke={color} strokeWidth={9} strokeLinecap="round" strokeDasharray={w * 1.5} strokeDashoffset={w * 1.5 * (1 - drawProg)} />
      <text x={x + 28} y={y + 42} fill="#E2E8F0" fontFamily={UI_FONT} fontSize={26} fontWeight={700}>{label}</text>
      <text x={x + w - 28} y={y + 54} textAnchor="end" fill={color} fontFamily={MONO_FONT} fontSize={48} fontWeight={700}>{formatNumber(startVal + (endVal - startVal) * drawProg, decimals, prefix, suffix)}</text>
    </g>
  );
};

export const BarChart2D: React.FC<{
  x: number; y: number; w?: number; h?: number;
  bars: { label: string; value: number; prefix?: string; suffix?: string; decimals?: number; color?: string }[]; progress: number;
}> = ({ x, y, w = 960, h = 460, bars, progress }) => {
  const max = Math.max(1, ...bars.map((b) => b.value));
  const bw = Math.min(180, (w / Math.max(1, bars.length)) * 0.54);
  const grow = Math.min(1, progress * 1.55);
  return (
    <g>
      <rect x={x - 20} y={y - 20} width={w + 40} height={h + 110} rx={12} fill="#080E1B" fillOpacity={0.92} stroke="#1E293B" strokeWidth={2.5} />
      <line x1={x} y1={y + h} x2={x + w} y2={y + h} stroke="#475569" strokeWidth={4} />
      {bars.map((b, i) => {
        const bh = Math.max(16, (b.value / max) * (h - 90) * grow);
        const gap = w / Math.max(1, bars.length);
        const bx = x + i * gap + (gap - bw) / 2;
        const col = b.color || "#00F0FF";
        return (
          <g key={i}>
            <polygon points={`${bx + bw},${y + h - bh} ${bx + bw + 18},${y + h - bh - 12} ${bx + bw + 18},${y + h - 12} ${bx + bw},${y + h}`} fill="#060A12" stroke={col} strokeWidth={2} />
            <rect x={bx} y={y + h - bh} width={bw} height={bh} rx={4} fill={col} />
            <text x={bx + bw / 2} y={y + h - bh - 18} textAnchor="middle" fill={col} fontFamily={MONO_FONT} fontSize={30} fontWeight={700}>{formatNumber(b.value * grow, b.decimals ?? 0, b.prefix ?? "", b.suffix ?? "")}</text>
            <text x={bx + bw / 2} y={y + h + 44} textAnchor="middle" fill="#E2E8F0" fontFamily={UI_FONT} fontSize={22} fontWeight={700}>{b.label}</text>
          </g>
        );
      })}
    </g>
  );
};

export const BalanceScale2D: React.FC<{
  x: number; y: number; leftLabel: string; rightLabel: string; tiltDeg?: number; leftColor?: string; rightColor?: string; progress: number;
}> = ({ x, y, leftLabel, rightLabel, tiltDeg = 15, leftColor = "#10B981", rightColor = "#EF4444", progress }) => {
  const tilt = tiltDeg * Math.min(1, progress * 1.5);
  return (
    <g transform={`translate(${x} ${y})`}>
      <line x1={-250} y1={tilt} x2={250} y2={-tilt} stroke="#94A3B8" strokeWidth={12} strokeLinecap="round" />
      <polygon points="0,-10 -32,170 32,170" fill="#334155" />
      <rect x={-275} y={tilt + 14} width={190} height={68} rx={8} fill={leftColor} />
      <text x={-180} y={tilt + 55} textAnchor="middle" fill="#FFFFFF" fontFamily={UI_FONT} fontSize={20} fontWeight={700}>{leftLabel}</text>
      <rect x={85} y={-tilt + 14} width={190} height={68} rx={8} fill={rightColor} />
      <text x={180} y={-tilt + 55} textAnchor="middle" fill="#FFFFFF" fontFamily={UI_FONT} fontSize={20} fontWeight={700}>{rightLabel}</text>
    </g>
  );
};

export const Microchip2D: React.FC<{
  x: number; y: number; scale?: number; color?: string; cracked?: boolean; overheating?: boolean; frame: number; progress: number;
}> = ({ x, y, scale = 1, color = "#00F0FF", overheating = false, frame }) => (
  <g transform={`translate(${x} ${y}) scale(${scale})`}>
    <polygon points="120,-120 146,-138 146,102 120,120" fill="#060A12" stroke={overheating ? "#EF4444" : color} strokeWidth={3} />
    <polygon points="-120,-120 -94,-138 146,-138 120,-120" fill="#1E293B" stroke={overheating ? "#EF4444" : color} strokeWidth={3} />
    <rect x={-120} y={-120} width={240} height={240} rx={8} fill="#090E17" stroke={overheating ? "#EF4444" : color} strokeWidth={5} />
    <rect x={-80} y={-80} width={160} height={160} rx={6} fill={overheating ? "#EF4444" : color} opacity={0.75 + 0.25 * Math.sin(frame * 0.25)} />
    <text x={0} y={8} textAnchor="middle" fill="#060A12" fontFamily={MONO_FONT} fontSize={22} fontWeight={700}>BLACKWELL</text>
  </g>
);

export const PowerPylon2D: React.FC<{ x: number; y: number; scale?: number; accentHex?: string; frame: number }> = ({ x, y, scale = 1, accentHex = "#F59E0B", frame }) => (
  <g transform={`translate(${x} ${y}) scale(${scale})`}>
    <polygon points="-80,180 -20,-180 20,-180 80,180" fill="none" stroke="#94A3B8" strokeWidth={6} />
    <line x1={-120} y1={-80} x2={120} y2={-80} stroke="#94A3B8" strokeWidth={8} />
    <circle cx={-120} cy={-70} r={12} fill={accentHex} opacity={0.7 + 0.3 * Math.sin(frame * 0.3)} />
    <circle cx={120} cy={-70} r={12} fill={accentHex} opacity={0.7 + 0.3 * Math.sin(frame * 0.3)} />
  </g>
);

export const BatteryBank2D: React.FC<{ x: number; y: number; scale?: number; accentHex?: string; frame: number; progress: number }> = ({ x, y, scale = 1, accentHex = "#10B981", frame, progress }) => (
  <g transform={`translate(${x} ${y}) scale(${scale})`}>
    <polygon points="140,-90 168,-108 168,72 140,90" fill="#0B1120" stroke="#475569" strokeWidth={3} />
    <polygon points="-140,-90 -112,-108 168,-108 140,-90" fill="#334155" stroke="#64748B" strokeWidth={3} />
    <rect x={-140} y={-90} width={280} height={180} rx={8} fill="#1E293B" stroke="#475569" strokeWidth={4} />
    <rect x={-110} y={-60} width={220 * Math.min(1, progress * 1.5)} height={120} rx={6} fill={accentHex} opacity={0.8 + 0.2 * Math.sin(frame * 0.15)} />
  </g>
);

export const SplitScreen3Panel: React.FC<{ progress: number; panel1: React.ReactNode; panel2: React.ReactNode; panel3: React.ReactNode }> = ({ progress, panel1, panel2, panel3 }) => (
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
import { BlueprintStamp2D, StatCounter2D } from "./CartoonKit2D";
import type { CartoonPlan, Transition2D } from "../types";

function computeTransitionTransform(transition: Transition2D, enterProg: number, width: number, height: number): { transform?: string; opacity: number } {
  const p = Math.max(0, Math.min(1, enterProg));
  const ease = p * p * (3 - 2 * p);
  switch (transition) {
    case "slide_left": return { transform: `translateX(${(1 - ease) * width}px)`, opacity: 1 };
    case "slide_up": return { transform: `translateY(${(1 - ease) * height}px)`, opacity: 1 };
    case "wipe_right": return { transform: `translateX(${-(1 - ease) * width}px)`, opacity: 1 };
    case "zoom_dissolve": return { transform: `scale(${0.92 + 0.08 * ease})`, opacity: ease };
    case "flash_cut":
    default: return { opacity: Math.min(1, p * 2.5) };
  }
}

export const CartoonStage2D: React.FC<{ plan: CartoonPlan }> = ({ plan }) => {
  const frame = useCurrentFrame();
  const { width, height, fps } = useVideoConfig();
  const tSec = frame / fps;
  const isVertical = height > width;
  const transSec = 0.22;

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
  const activeStyle = inTransition ? computeTransitionTransform(activeScene.transition, enterProg, width, height) : { opacity: 1 };
  const flashOpacity = inTransition && activeScene.transition === "flash_cut" ? interpolate(enterProg, [0, 0.35, 1], [0.85, 0.4, 0], { extrapolateRight: "clamp" }) : 0;

  const vb = isVertical ? "0 0 1080 1920" : "0 0 1920 1080";
  const showHudOverlays = activeScene.backdropTheme !== "black_title_card";
  const stampTrigger = activeScene.stampTriggerSec ?? activeScene.localPeakTimes[0] ?? 0.65;

  return (
    <AbsoluteFill style={{ backgroundColor: "#04070E", overflow: "hidden" }}>
      {inTransition && prevScene && PrevComp && (
        <AbsoluteFill>
          <PrevComp frame={frame} localFrame={Math.max(0, frame - Math.round(prevScene.startSec * fps))} localTime={tSec - prevScene.startSec} durationSec={Math.max(0.1, prevScene.endSec - prevScene.startSec)} progress={1} peakTimes={prevScene.localPeakTimes} accentHex={prevScene.accentHex} backdropTheme={prevScene.backdropTheme} cameraMove={prevScene.cameraMove} chapterTag={prevScene.chapterTag || "01 // CORE TO GRID"} isVertical={isVertical} />
        </AbsoluteFill>
      )}
      {ActiveComp && (
        <AbsoluteFill style={activeStyle}>
          <ActiveComp frame={frame} localFrame={Math.max(0, frame - Math.round(activeScene.startSec * fps))} localTime={timeIntoScene} durationSec={activeDur} progress={activeProgress} peakTimes={activeScene.localPeakTimes} accentHex={activeScene.accentHex} backdropTheme={activeScene.backdropTheme} cameraMove={activeScene.cameraMove} chapterTag={activeScene.chapterTag || "01 // CORE TO GRID"} isVertical={isVertical} />
        </AbsoluteFill>
      )}
      {showHudOverlays && (activeScene.statCounter || activeScene.stampText) && (
        <AbsoluteFill style={{ pointerEvents: "none" }}>
          <svg viewBox={vb} style={{ width: "100%", height: "100%", display: "block" }}>
            {activeScene.statCounter && (
              <StatCounter2D x={isVertical ? 540 : 1580} y={isVertical ? 1720 : 815} w={isVertical ? 820 : 540} label={activeScene.statCounter.label} startVal={activeScene.statCounter.startVal} endVal={activeScene.statCounter.endVal} prefix={activeScene.statCounter.prefix} suffix={activeScene.statCounter.suffix} decimals={activeScene.statCounter.decimals ?? 0} color={activeScene.statCounter.color || activeScene.accentHex} localTime={timeIntoScene} triggerSec={activeScene.statCounter.triggerSec ?? 0.15} />
            )}
            {activeScene.stampText && (
              <BlueprintStamp2D x={isVertical ? 540 : 980} y={isVertical ? 410 : 175} text={activeScene.stampText} color={activeScene.stampColor || "#EF4444"} localTime={timeIntoScene} triggerSec={stampTrigger} />
            )}
          </svg>
        </AbsoluteFill>
      )}
      {flashOpacity > 0 && <AbsoluteFill style={{ backgroundColor: "#FFFFFF", opacity: flashOpacity, pointerEvents: "none" }} />}
    </AbsoluteFill>
  );
};
'''

FILES["src/generated/scenes/Scene_01.tsx"] = r'''
import React from "react";
import { SceneBackdrop2D, Camera2D, DataHall25D, TelemetryHUD2D } from "../../components/CartoonKit2D";
import type { Scene2DProps } from "../../types";

export const Scene_01: React.FC<Scene2DProps> = (props) => {
  const { frame, localTime, progress, peakTimes, accentHex, backdropTheme, cameraMove, chapterTag, isVertical } = props;
  const vb = isVertical ? "0 0 1080 1920" : "0 0 1920 1080";
  return (
    <svg viewBox={vb} style={{ width: "100%", height: "100%", display: "block" }}>
      <SceneBackdrop2D theme={backdropTheme} frame={frame} accentHex={accentHex} chapterTag={chapterTag} />
      <Camera2D move={cameraMove} progress={progress} frame={frame} peakTimes={peakTimes} localTime={localTime}>
        <DataHall25D accentHex={accentHex} frame={frame} progress={progress} isVertical={isVertical} />
        <TelemetryHUD2D
          x={isVertical ? 120 : 1310}
          y={isVertical ? 160 : 120}
          w={isVertical ? 840 : 540}
          title="DATA HALL TELEMETRY"
          metrics={[
            { label: "CAMPUS POWER", value: "1,000", unit: "MW", barPct: 95 },
            { label: "RACK DENSITY", value: "600", unit: "kW", alert: true, barPct: 90 },
            { label: "TOTAL CAPEX", value: "$100", unit: "B", barPct: 84 },
            { label: "COOLANT INLET", value: "18.0", unit: "C", barPct: 45 },
          ]}
          progress={progress}
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
  totalDurationSec: 5,
  bpm: 105,
  emphasisPeaksSec: [0.4, 2.8],
  scenes: [
    {
      id: "scene_01",
      componentName: "Scene_01",
      chapterTag: "01 // 1-GIGAWATT DATA HALL",
      visualConcept: "2.5D Isometric Data Hall + Right Telemetry HUD",
      visualSpec: "2.5D racks on left 65%, telemetry HUD right 30%, labeled cooling loops bottom",
      titleText: "",
      stampText: "600 KW HEAT",
      stampColor: "#EF4444",
      stampTriggerSec: 1.2,
      statCounter: { label: "FACILITY EFFICIENCY", startVal: 1.48, endVal: 1.12, suffix: " PUE", decimals: 2, color: "#00F0FF", triggerSec: 0.2 },
      backdropTheme: "isometric_blueprint",
      cameraMove: "push_in",
      transition: "flash_cut",
      sfx: "impact",
      accentHex: "#00F0FF",
      startSec: 0,
      endSec: 5,
      localPeakTimes: [0.4, 2.8],
    },
  ],
};
'''

FILES["src/generated/GeneratedTimeline.tsx"] = r'''
import React from "react";
import { AbsoluteFill } from "remotion";
import { CartoonStage2D } from "../components/CartoonStage2D";
import { SCENE_PLAN } from "./ScenesData";

export const GENERATED_TOTAL_FRAMES = 150;
export const GeneratedTimeline: React.FC = () => (<AbsoluteFill><CartoonStage2D plan={SCENE_PLAN} /></AbsoluteFill>);
'''

FILES["src/Main.tsx"] = r'''
import React from "react";
import { AbsoluteFill } from "remotion";
import { GeneratedTimeline } from "./generated/GeneratedTimeline";

export const Main: React.FC = () => (
  <AbsoluteFill style={{ backgroundColor: "#04070E" }}>
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
  const totalFrames = Math.max(60, GENERATED_TOTAL_FRAMES || Math.round(SCENE_PLAN.totalDurationSec * SCENE_PLAN.fps));
  return <Composition id="Main" component={Main} durationInFrames={totalFrames} fps={SCENE_PLAN.fps || 30} width={SCENE_PLAN.width || 1920} height={SCENE_PLAN.height || 1080} />;
};
'''

FILES["src/index.ts"] = r'''
import { registerRoot } from "remotion";
import { RemotionRoot } from "./Root";

registerRoot(RemotionRoot);
'''

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
        options: ["0", "30"]
      force_workers:
        description: "Parallel workers (auto = up to 20)"
        required: false
        default: "auto"
        type: choice
        options: ["auto", "4", "10", "20"]
      trim_silence:
        description: "Trim pauses >0.65s?"
        required: false
        default: "false"
        type: choice
        options: ["false", "true"]
      include_bgm:
        description: "Include calm background music?"
        required: false
        default: "true"
        type: choice
        options: ["true", "false"]

concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: false

jobs:
  plan_and_prepare:
    runs-on: ubuntu-latest
    timeout-minutes: 45
    outputs:
      has_input: ${{ steps.check_input.outputs.has_input }}
      chunks_json: ${{ steps.chunk_plan.outputs.chunks_json }}

    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - run: |
          if [ -f setup_factory.py ]; then python setup_factory.py --no-git; fi
      - id: check_input
        run: |
          shopt -s nullglob nocaseglob
          files=(input/*.mp3 input/*.wav input/*.m4a input/*.aac input/*.flac input/*.mp4)
          echo "has_input=$([ ${#files[@]} -gt 0 ] && echo true || echo false)" >> $GITHUB_OUTPUT
      - if: steps.check_input.outputs.has_input == 'true'
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          cache: "pip"
      - if: steps.check_input.outputs.has_input == 'true'
        uses: actions/setup-node@v4
        with:
          node-version: "22"
      - if: steps.check_input.outputs.has_input == 'true'
        run: |
          sudo apt-get update
          sudo apt-get install -y ffmpeg libnss3 libdbus-1-3 libatk1.0-0 libgbm1 libxrandr2 libxkbcommon0 libxfixes3 libxcomposite1 libxdamage1 libatk-bridge2.0-0 libpango-1.0-0 libcairo2 libcups2 libasound2t64 || sudo apt-get install -y libasound2
          pip install -r requirements.txt
          npm install --no-audit --no-fund
          npx remotion browser ensure
      - name: Step 1 - Transcribe & Emphasis Peaks
        if: steps.check_input.outputs.has_input == 'true'
        env:
          INPUT_FOLDER: "input"
          TRIM_SILENCE: ${{ github.event.inputs.trim_silence || 'false' }}
          PREVIEW_SECONDS: ${{ github.event.inputs.preview_seconds || '0' }}
        run: python scripts/analyze_audio.py
      - name: Step 2 - Multi-Provider AI Blueprint Illustrator
        if: steps.check_input.outputs.has_input == 'true'
        env:
          INPUT_FOLDER: "input"
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
          OPENROUTER_API_KEY: ${{ secrets.OPENROUTER_API_KEY }}
          GROQ_API_KEY: ${{ secrets.GROQ_API_KEY }}
          VIDEO_FORMAT: "long_16_9"
        run: python scripts/generate_scenes.py
      - name: Step 3 - Validate Scenes
        if: steps.check_input.outputs.has_input == 'true'
        run: python scripts/validate_scenes.py
      - name: Step 4 - Master Audio, BGM & 5 SFX
        if: steps.check_input.outputs.has_input == 'true'
        env:
          INCLUDE_BGM: ${{ github.event.inputs.include_bgm || 'true' }}
        run: python scripts/mix_audio.py
      - name: Step 5 - Smoke Test & Bundle
        if: steps.check_input.outputs.has_input == 'true'
        run: |
          npx remotion still src/index.ts Main work/frame0_smoke.png --frame=0
          npx remotion bundle src/index.ts --public-dir public --out-dir build_bundle
      - name: Step 6 - Plan Workers
        id: chunk_plan
        if: steps.check_input.outputs.has_input == 'true'
        env:
          FORCE_WORKERS: ${{ github.event.inputs.force_workers || 'auto' }}
        run: python scripts/plan_chunks.py
      - if: steps.check_input.outputs.has_input == 'true'
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
      - uses: actions/checkout@v4
      - run: |
          if [ -f setup_factory.py ]; then python setup_factory.py --no-git; fi
      - uses: actions/download-artifact@v4
        with:
          name: prepared-long
      - uses: actions/setup-node@v4
        with:
          node-version: "22"
      - run: |
          sudo apt-get update
          sudo apt-get install -y ffmpeg libnss3 libdbus-1-3 libatk1.0-0 libgbm1 libxrandr2 libxkbcommon0 libxfixes3 libxcomposite1 libxdamage1 libatk-bridge2.0-0 libpango-1.0-0 libcairo2 libcups2 libasound2t64 || sudo apt-get install -y libasound2
          npm install --no-audit --no-fund
          npx remotion browser ensure
          mkdir -p out
          npx remotion render build_bundle Main out/chunk_${{ matrix.chunk.idx }}.mp4 --frames=${{ matrix.chunk.start }}-${{ matrix.chunk.end }} --muted --concurrency=2 --codec=h264 --pixel-format=yuv420p --crf=20 --x264-preset=veryfast
      - uses: actions/upload-artifact@v4
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
      - uses: actions/checkout@v4
      - run: |
          if [ -f setup_factory.py ]; then python setup_factory.py --no-git; fi
      - uses: actions/download-artifact@v4
        with:
          name: prepared-long
      - uses: actions/download-artifact@v4
        with:
          pattern: long-chunk-*
          path: chunks
          merge-multiple: true
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: |
          sudo apt-get update && sudo apt-get install -y ffmpeg
          python scripts/stitch_chunks.py
        env:
          VIDEO_FORMAT: "long_16_9"
      - uses: actions/upload-artifact@v4
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
    timeout-minutes: 30
    outputs:
      has_input: ${{ steps.check_input.outputs.has_input }}
      chunks_json: ${{ steps.chunk_plan.outputs.chunks_json }}
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - run: |
          if [ -f setup_factory.py ]; then python setup_factory.py --no-git; fi
      - id: check_input
        run: |
          shopt -s nullglob nocaseglob
          files=(input_short/*.mp3 input_short/*.wav input_short/*.m4a)
          echo "has_input=$([ ${#files[@]} -gt 0 ] && echo true || echo false)" >> $GITHUB_OUTPUT
      - if: steps.check_input.outputs.has_input == 'true'
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - if: steps.check_input.outputs.has_input == 'true'
        uses: actions/setup-node@v4
        with:
          node-version: "22"
      - if: steps.check_input.outputs.has_input == 'true'
        run: |
          sudo apt-get update
          sudo apt-get install -y ffmpeg libnss3 libdbus-1-3 libatk1.0-0 libgbm1 libxrandr2 libxkbcommon0 libxfixes3 libxcomposite1 libxdamage1 libatk-bridge2.0-0 libpango-1.0-0 libcairo2 libcups2 libasound2t64 || sudo apt-get install -y libasound2
          pip install -r requirements.txt
          npm install --no-audit
          npx remotion browser ensure
      - if: steps.check_input.outputs.has_input == 'true'
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
      - if: steps.check_input.outputs.has_input == 'true'
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
      - run: |
          if [ -f setup_factory.py ]; then python setup_factory.py --no-git; fi
      - uses: actions/download-artifact@v4
        with:
          name: prepared-short
      - uses: actions/setup-node@v4
        with:
          node-version: "22"
      - run: |
          sudo apt-get update
          sudo apt-get install -y ffmpeg libnss3 libdbus-1-3 libatk1.0-0 libgbm1 libxrandr2 libxkbcommon0 libxfixes3 libxcomposite1 libxdamage1 libatk-bridge2.0-0 libpango-1.0-0 libcairo2 libcups2 libasound2t64 || sudo apt-get install -y libasound2
          npm install --no-audit
          npx remotion browser ensure
          mkdir -p out
          npx remotion render build_bundle Main out/chunk_${{ matrix.chunk.idx }}.mp4 --frames=${{ matrix.chunk.start }}-${{ matrix.chunk.end }} --muted --concurrency=2
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
      - run: |
          if [ -f setup_factory.py ]; then python setup_factory.py --no-git; fi
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
    print(f"[setup_factory] Unpacking {len(FILES)} CoreToGrid v5.2 files in {ROOT}...")
    for orphan in ("src/components/Continuous3DWorld.tsx", "src/components/HudOverlay.tsx", "src/components/StudioKit.tsx"):
        p = ROOT / orphan
        if p.exists():
            p.unlink()
            print(f"  - Removed legacy file: {orphan}")
    for old_dir in ("src/scenes", "src/utils", "src/three"):
        d = ROOT / old_dir
        if d.exists():
            shutil.rmtree(d, ignore_errors=True)
            print(f"  - Removed legacy dir: {old_dir}")

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
        print("\n[setup_factory] Not a git repo; unpacked files locally.")
        return

    git("add", ".")
    if git("diff", "--cached", "--quiet", check=False).returncode != 0:
        git("commit", "-m", "Upgrade v5.2: Elite 2.5D UI + 5 SFX + 45s Multi-Provider AI")
    if git("push", check=False).returncode != 0:
        git("push", "-u", "origin", "HEAD")
    print("\n[setup_factory] SUCCESS! CoreToGrid v5.2 is live on GitHub.")


if __name__ == "__main__":
    write_all_files()
    if "--no-git" not in sys.argv:
        try:
            run_git_push()
        except subprocess.CalledProcessError as exc:
            print(f"[setup_factory] Git notice: ({exc}).")
            sys.exit(exc.returncode)
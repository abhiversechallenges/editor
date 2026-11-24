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

# Track models temporarily returning 503 during this process so later batches don't waste 10s each time
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

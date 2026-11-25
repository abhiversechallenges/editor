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

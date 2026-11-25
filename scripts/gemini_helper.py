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

# Priority 1 & 2: Gemini 4 Hydrogen -> Gemini 3.8 Flash
PRO_LADDER = [
    ("gemini-4-hydrogen", "high", 65536, True),
    ("gemini-3.8-flash", "low", 32768, True),
]

FLASH_LADDER = [
    ("gemini-4-hydrogen", "low", 65536, True),
    ("gemini-3.8-flash", None, 32768, True),
]

# Priority 3: OpenRouter Free Tier (requires ZDR OFF in openrouter.ai/settings/privacy)
OPENROUTER_FREE_MODELS = [
    "nvidia/nemotron-3-ultra-550b-a55b:free",
    "nvidia/nemotron-3.5-super-vl:free",
    "baidu/ernie-5.5-flash-preview:free",
    "openrouter/free",
]

# Priority 4: Groq Free Tier
GROQ_FREE_MODELS = [
    "openai/gpt-oss-120b",
    "qwen/qwen3.8-27b",
]

_COOLDOWN_UNTIL: dict[str, float] = {}


def get_client() -> Optional[genai.Client]:
    api_key = (os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY") or "").strip()
    if not api_key:
        return None
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
        final_prompt += "\n\nCRITICAL: Return ONLY a valid raw JSON object. No markdown fences or extra text."

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
        "User-Agent": "OpenAI/Python",
    }
    if extra_headers:
        headers.update(extra_headers)

    req = urllib.request.Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as err:
        body = err.read().decode("utf-8", errors="ignore")[:220]
        raise RuntimeError(f"HTTP {err.code}: {body}") from err

    content = data["choices"][0]["message"]["content"]
    if not content or not content.strip():
        raise RuntimeError(f"Empty response from {model}")
    return clean_json_text(content) if json_mode else content


def _try_openrouter(prompt: str, json_mode: bool) -> Optional[str]:
    or_key = (os.environ.get("OPENROUTER_API_KEY") or "").strip()
    if not or_key:
        return None
    for model in OPENROUTER_FREE_MODELS:
        try:
            print(f"[ai_router] Priority 3 -> OpenRouter ({model})...", flush=True)
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
            time.sleep(1.5)
    return None


def _try_groq(prompt: str, json_mode: bool) -> Optional[str]:
    groq_key = (os.environ.get("GROQ_API_KEY") or "").strip()
    if not groq_key:
        return None
    for model in GROQ_FREE_MODELS:
        try:
            print(f"[ai_router] Priority 4 -> Groq ({model})...", flush=True)
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
            time.sleep(1.5)
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
                if key in dead_models or (pass_num == 1 and _COOLDOWN_UNTIL.get(model_name, 0) > now):
                    continue

                config_kwargs: dict[str, Any] = {
                    "max_output_tokens": min(cap, max_output_tokens),
                }
                if "gemini-4" not in model_name:
                    config_kwargs["temperature"] = temperature
                if thinking_lvl:
                    config_kwargs["thinking_config"] = types.ThinkingConfig(thinking_level=thinking_lvl)
                if json_mode and supports_json:
                    config_kwargs["response_mime_type"] = "application/json"

                config = types.GenerateContentConfig(**config_kwargs)

                try:
                    print(f"[ai_router] Priority -> {model_name} (think={thinking_lvl or 'off'})...", flush=True)
                    response = client.models.generate_content(
                        model=model_name,
                        contents=prompt_str,
                        config=config,
                    )
                    text = response.text or ""
                    if not text.strip():
                        raise RuntimeError(f"Empty response from {model_name}")
                    print(f"[ai_router] Success with {model_name} ({len(text)} chars).", flush=True)
                    return clean_json_text(text) if json_mode else text
                except APIError as exc:
                    last_error = exc
                    msg = str(exc).lower()
                    if any(k in msg for k in ("404", "403", "400", "not found", "unsupported", "limit: 0")):
                        print(f"[ai_router] {model_name} unsupported ({exc}); skipping.", flush=True)
                        dead_models.add(key)
                    elif "429" in msg or "quota" in msg or "exhausted" in msg or "503" in msg:
                        _COOLDOWN_UNTIL[model_name] = time.time() + 65.0
                        print(f"[ai_router] {model_name} rate-limited (429/503); switching immediately...", flush=True)
                        time.sleep(1.5)
                    else:
                        time.sleep(2)
                except Exception as exc:
                    last_error = exc
                    time.sleep(2)

        or_res = _try_openrouter(prompt_str, json_mode)
        if or_res:
            return or_res

        groq_res = _try_groq(prompt_str, json_mode)
        if groq_res:
            return groq_res

        if pass_num == 1:
            _COOLDOWN_UNTIL.clear()
            print("[ai_router] All 4 tiers busy; waiting 20s before retry pass...", flush=True)
            time.sleep(20)

    raise RuntimeError(f"All tiers (Hydrogen -> 3.8 Flash -> OpenRouter -> Groq) failed. Last error: {last_error}")


def parse_json_strict(raw: str) -> Any:
    return json.loads(clean_json_text(raw))

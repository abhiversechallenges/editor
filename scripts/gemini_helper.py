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

# Priority 1 & 2: Gemini (fast thinking + 25s fail-safe)
PRO_LADDER = [
    ("gemini-4-hydrogen", "low", 65536, True),
    ("gemini-3.8-flash", None, 32768, True),
]

FLASH_LADDER = [
    ("gemini-4-hydrogen", "low", 65536, True),
    ("gemini-3.8-flash", None, 32768, True),
]

# Priority 3A: Fast OpenRouter models (~200 tok/s, 45s timeout)
OPENROUTER_FAST_MODELS = [
    "baidu/ernie-5.5-flash-preview:free",
    "openrouter/free",
]

# Priority 3B: Groq Ultra-Fast models (~500 tok/s, 45s timeout)
GROQ_FREE_MODELS = [
    "openai/gpt-oss-120b",
    "qwen/qwen3.8-27b",
]

# Priority 4: Heavy OpenRouter backup models (90s timeout)
OPENROUTER_HEAVY_MODELS = [
    "nvidia/nemotron-3.5-super-vl:free",
    "nvidia/nemotron-3-ultra-550b-a55b:free",
]

_COOLDOWN_UNTIL: dict[str, float] = {}


def get_client() -> Optional[genai.Client]:
    api_key = (os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY") or "").strip()
    if not api_key:
        return None
    first_key = [k.strip() for k in api_key.split(",") if k.strip()][0]
    return genai.Client(
        api_key=first_key,
        http_options=types.HttpOptions(timeout=25_000),  # 25s max wait so Gemini never stalls
    )


def _strip_think(raw: str) -> str:
    return re.sub(r"<think>[\s\S]*?</think>", "", raw or "").strip()


def clean_json_text(raw: str) -> str:
    text = _strip_think(raw)
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
    text = _strip_think(raw)
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
    timeout_sec: int,
    extra_headers: Optional[dict[str, str]] = None,
) -> str:
    final_prompt = prompt
    if json_mode:
        final_prompt += "\n\nCRITICAL: Return ONLY one valid raw JSON object starting with { and ending with }. No markdown fences or extra text."

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

    req = urllib.request.Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )
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
        json.loads(cleaned)  # Verify valid JSON before accepting!
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
        # 1. Gemini Hydrogen -> 3.8 Flash (skips for 3 mins on 429/503)
        if client is not None:
            now = time.time()
            for model_name, thinking_lvl, cap, supports_json in ladder:
                key = f"{model_name}:{thinking_lvl}"
                if key in dead_models or _COOLDOWN_UNTIL.get(model_name, 0) > now:
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

        # 2. Fast OpenRouter (Ernie 5.5 Flash / auto free)
        fast_or = _try_openrouter_list(OPENROUTER_FAST_MODELS, "Fast Tier", prompt_str, json_mode, timeout_sec=45)
        if fast_or:
            return fast_or

        # 3. Groq Ultra-Fast (GPT-OSS 120B / Qwen 3.8 27B)
        groq_res = _try_groq(prompt_str, json_mode)
        if groq_res:
            return groq_res

        # 4. Heavy OpenRouter Backup (Nemotron 3.5 / 3 Ultra 550B)
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

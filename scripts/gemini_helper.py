import json
import os
import re
import time
from typing import Any, Optional

from google import genai
from google.genai import types
from google.genai.errors import APIError

# Prioritize Gemini 4 Hydrogen with Extra Thinking (xhigh), falling back safely to high & 3.8/3.5
PRO_MODEL_CHAIN = [
    ("gemini-4-hydrogen", "xhigh"),
    ("gemini-4-hydrogen", "high"),
    ("gemini-3.8-flash", "high"),
    ("gemini-3.5-flash-lite", "high"),
]

FLASH_MODEL_CHAIN = [
    ("gemini-4-hydrogen", "xhigh"),
    ("gemini-4-hydrogen", "high"),
    ("gemini-3.5-flash-lite", "high"),
    ("gemini-3.8-flash", "high"),
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
    max_output_tokens: int = 65536,
    temperature: float = 0.4,
) -> str:
    chain = PRO_MODEL_CHAIN if role == "pro" else FLASH_MODEL_CHAIN
    last_error: Optional[Exception] = None

    for model_name, thinking_lvl in chain:
        # Gemini 4 shares output limit with thinking tokens, so keep full 65,536 budget for xhigh
        token_cap = 65536 if model_name.startswith("gemini-4") else max_output_tokens
        config_kwargs: dict[str, Any] = {
            "max_output_tokens": token_cap,
            "thinking_config": types.ThinkingConfig(thinking_level=thinking_lvl),
        }
        if json_mode:
            config_kwargs["response_mime_type"] = "application/json"

        config = types.GenerateContentConfig(**config_kwargs)

        for attempt in range(2):
            try:
                print(
                    f"[gemini_helper] Calling {model_name} (thinking={thinking_lvl}, attempt {attempt + 1})...",
                    flush=True,
                )
                response = client.models.generate_content(
                    model=model_name,
                    contents=contents,
                    config=config,
                )
                text = response.text or ""
                if not text.strip():
                    raise RuntimeError(f"Empty response from {model_name} ({thinking_lvl})")
                return clean_json_text(text) if json_mode else text
            except APIError as exc:
                last_error = exc
                msg = str(exc).lower()
                if any(
                    k in msg
                    for k in ("404", "403", "not found", "permission", "restricted", "limit: 0", "unsupported")
                ):
                    print(f"[gemini_helper] {model_name} ({thinking_lvl}) unavailable ({exc}); switching...", flush=True)
                    break
                if attempt == 0:
                    print(f"[gemini_helper] {model_name} rate/transient error ({exc}); retrying in 8s...", flush=True)
                    time.sleep(8)
            except Exception as exc:
                last_error = exc
                if attempt == 0:
                    print(f"[gemini_helper] {model_name} error ({exc}); retrying in 5s...", flush=True)
                    time.sleep(5)

    raise RuntimeError(f"All Gemini models failed. Last error: {last_error}")


def parse_json_strict(raw: str) -> Any:
    return json.loads(clean_json_text(raw))

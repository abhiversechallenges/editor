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

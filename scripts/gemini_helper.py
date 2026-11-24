import json
import os
import re
import time
from typing import Any, Optional

from google import genai
from google.genai import types
from google.genai.errors import APIError

# Gemini 4 Hydrogen at HIGH thinking (Google's default: score 51 vs 54 at xhigh,
# finishes in ~20-45s instead of xhigh's 10-21 minute hang per request)
PRO_MODEL_CHAIN = [
    ("gemini-4-hydrogen", "high"),
    ("gemini-4-hydrogen", "medium"),
    ("gemini-3.8-flash", "high"),
    ("gemini-3.5-flash-lite", "high"),
]

FLASH_MODEL_CHAIN = [
    ("gemini-4-hydrogen", "high"),
    ("gemini-4-hydrogen", "medium"),
    ("gemini-3.5-flash-lite", "high"),
    ("gemini-3.8-flash", "high"),
]


def get_client() -> genai.Client:
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError(
            "Missing GEMINI_API_KEY secret. Add it in GitHub Repo -> Settings -> Secrets -> Actions."
        )
    return genai.Client(
        api_key=api_key,
        http_options=types.HttpOptions(timeout=600_000),  # 10 min read timeout in ms
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
    chain = PRO_MODEL_CHAIN if role == "pro" else FLASH_MODEL_CHAIN
    last_error: Optional[Exception] = None

    for model_name, thinking_lvl in chain:
        token_cap = 65536 if model_name.startswith("gemini-4") else max_output_tokens
        config_kwargs: dict[str, Any] = {
            "max_output_tokens": token_cap,
            "thinking_config": types.ThinkingConfig(
                thinking_level=thinking_lvl,
                include_thoughts=True,
            ),
        }
        if json_mode:
            config_kwargs["response_mime_type"] = "application/json"

        config = types.GenerateContentConfig(**config_kwargs)

        for attempt in range(2):
            try:
                print(
                    f"[gemini_helper] Streaming {model_name} (thinking={thinking_lvl}, attempt {attempt + 1})...",
                    flush=True,
                )
                output_parts: list[str] = []
                thought_chunks = 0
                stream = client.models.generate_content_stream(
                    model=model_name,
                    contents=contents,
                    config=config,
                )
                for chunk in stream:
                    cands = getattr(chunk, "candidates", None) or []
                    if not cands:
                        continue
                    content = getattr(cands[0], "content", None)
                    parts = getattr(content, "parts", None) or []
                    for part in parts:
                        ptext = getattr(part, "text", None)
                        if not ptext:
                            continue
                        if getattr(part, "thought", False):
                            thought_chunks += 1
                            if thought_chunks % 5 == 1:
                                print("  [thinking...]", flush=True)
                        else:
                            output_parts.append(ptext)

                text = "".join(output_parts)
                if not text.strip():
                    raise RuntimeError(f"Empty stream response from {model_name} ({thinking_lvl})")
                print(f"[gemini_helper] Completed {model_name} ({len(text)} chars).", flush=True)
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

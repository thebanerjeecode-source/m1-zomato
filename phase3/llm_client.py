from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Optional

import httpx


@dataclass(frozen=True)
class LLMConfig:
    base_url: str
    api_key: str
    model: str
    timeout_s: float = 45.0


def load_llm_config() -> Optional[LLMConfig]:
    base_url = os.environ.get("PHASE3_LLM_BASE_URL")
    api_key = os.environ.get("PHASE3_LLM_API_KEY")
    model = os.environ.get("PHASE3_LLM_MODEL")
    if not base_url or not api_key or not model:
        return None
    return LLMConfig(base_url=base_url.rstrip("/"), api_key=api_key, model=model)


def chat_completions(cfg: LLMConfig, system_prompt: str, user_prompt: str) -> str:
    """
    OpenAI-compatible Chat Completions request.
    Expected endpoint: {base_url}/chat/completions
    """
    url = f"{cfg.base_url}/chat/completions"
    headers = {
        "Authorization": f"Bearer {cfg.api_key}",
        "Content-Type": "application/json",
    }
    payload: dict[str, Any] = {
        "model": cfg.model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.2,
    }

    with httpx.Client(timeout=cfg.timeout_s) as client:
        resp = client.post(url, headers=headers, json=payload)
        resp.raise_for_status()
        data = resp.json()

    # Standard shape: choices[0].message.content
    try:
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        raise RuntimeError(f"Unexpected LLM response format: {e}") from e


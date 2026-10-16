"""Model backends for the pure CORSIKA Agent web UI.

The web server is provider-neutral: credentials are injected only through
environment variables and are never accepted through the web page.
"""

from __future__ import annotations

import os
from typing import Dict

STUDIO_MODELS: Dict[str, str] = {
    "deepseek-flash": "DeepSeek V4.1 Flash",
    "deepseek-v4-pro": "DeepSeek V4 Pro",
}

LEGACY_MODEL_ALIASES: Dict[str, str] = {
    "qwen3.6-flash": "deepseek-flash",
    "qwen3.6-plus": "deepseek-v4-pro",
    "deepseek-v4-flash": "deepseek-flash",
}


class AgentError(RuntimeError):
    """A session or configuration error surfaced to the web UI."""


def normalize_studio_model(model: str) -> str:
    return LEGACY_MODEL_ALIASES.get(model, model)


def _model_environment(model: str) -> Dict[str, str]:
    model = normalize_studio_model(model)
    if model not in STUDIO_MODELS:
        raise AgentError(f"Unsupported model: {model}")
    environment = os.environ.copy()
    # Human-only credentials must never leak into an OpenCode process.
    environment.pop("MUON_HUMAN_USERNAME", None)
    environment.pop("MUON_HUMAN_PASSWORD", None)
    api_key = environment.get("DEEPSEEK_API_KEY")
    if api_key:
        environment["OPENAI_API_KEY"] = api_key
    environment["OPENAI_BASE_URL"] = environment.get(
        "DEEPSEEK_BASE_URL", "https://api.deepseek.com"
    )
    environment["OPENAI_MODEL"] = model
    return environment


def available_backends() -> Dict[str, str]:
    return dict(STUDIO_MODELS)

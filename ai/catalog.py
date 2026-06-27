from collections import OrderedDict


PROVIDERS = OrderedDict({
    "groq": {
        "label": "Groq",
        "key_var": "GROQ_API_KEY",
        "model_var": "GROQ_MODEL",
        "default_model": "llama-3.3-70b-versatile",
        "models": [
            ("llama-3.3-70b-versatile", "Llama 3.3 70B Versatile"),
        ],
    },
    "openai": {
        "label": "OpenAI",
        "key_var": "OPENAI_API_KEY",
        "model_var": "OPENAI_MODEL",
        "default_model": "gpt-4.1",
        "models": [
            ("gpt-4.1", "GPT-4.1"),
            ("gpt-4.1-mini", "GPT-4.1 Mini"),
            ("gpt-4o", "GPT-4o"),
            ("gpt-4o-mini", "GPT-4o Mini"),
        ],
    },
    "github-copilot": {
        "label": "GitHub Copilot",
        "key_var": "OPENAI_API_KEY",
        "model_var": "OPENAI_MODEL",
        "default_model": "gpt-4.1",
        "models": [
            ("gpt-4.1", "GPT-4.1"),
            ("gpt-4.1-mini", "GPT-4.1 Mini"),
            ("gpt-4o", "GPT-4o"),
        ],
    },
    "claude": {
        "label": "Anthropic",
        "key_var": "CLAUDE_API_KEY",
        "model_var": "CLAUDE_MODEL",
        "default_model": "claude-3-5-sonnet-latest",
        "models": [
            ("claude-3-5-sonnet-latest", "Claude 3.5 Sonnet"),
            ("claude-3-7-sonnet-latest", "Claude 3.7 Sonnet"),
            ("claude-sonnet-4-latest", "Claude Sonnet 4"),
        ],
    },
    "gemini": {
        "label": "Google",
        "key_var": "GEMINI_API_KEY",
        "model_var": "GEMINI_MODEL",
        "default_model": "gemini-2.5-pro",
        "models": [
            ("gemini-2.5-pro", "Gemini 2.5 Pro"),
            ("gemini-2.5-flash", "Gemini 2.5 Flash"),
            ("gemini-1.5-pro", "Gemini 1.5 Pro"),
        ],
    },
})


def provider_label(provider_key: str) -> str:
    return PROVIDERS[provider_key]["label"]


def provider_key_var(provider_key: str) -> str:
    return PROVIDERS[provider_key]["key_var"]


def provider_model_var(provider_key: str) -> str:
    return PROVIDERS[provider_key]["model_var"]


def provider_default_model(provider_key: str) -> str:
    return PROVIDERS[provider_key]["default_model"]


def provider_models(provider_key: str) -> list[tuple[str, str]]:
    return list(PROVIDERS[provider_key]["models"])


def model_label(provider_key: str, model_id: str) -> str:
    for model_key, label in PROVIDERS[provider_key]["models"]:
        if model_key == model_id:
            return label
    return model_id


# ── shared helpers for key-state checks ───────────────────────────

import os
import sys
from pathlib import Path


def _catalog_env_path() -> Path:
    if getattr(sys, 'frozen', False):
        p = Path(os.environ.get("APPDATA", Path.home())) / "FloatingAI" / ".env"
        p.parent.mkdir(parents=True, exist_ok=True)
        if not p.exists():
            bundled = Path(sys._MEIPASS) / '.env'
            if bundled.exists():
                p.write_text(bundled.read_text(encoding="utf-8"), encoding="utf-8")
        return p
    return Path(__file__).resolve().parent.parent / '.env'


def _catalog_read_env() -> dict[str, str]:
    env = _catalog_env_path()
    if not env.exists():
        return {}
    result = {}
    for line in env.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        result[k.strip()] = v.strip()
    return result


BACKENDS = {
    key: {"var": info["key_var"], "label": info["label"]}
    for key, info in PROVIDERS.items()
}


def any_key_configured() -> bool:
    env = _catalog_read_env()
    for info in BACKENDS.values():
        if env.get(info["var"]):
            return True
    return False

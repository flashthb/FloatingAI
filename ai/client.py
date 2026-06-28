import os
from typing import Optional
from openai import OpenAI
import httpx
from . import _util, groq_backend
from .catalog import PROVIDERS, provider_default_model, provider_model_var
from config import settings


_openai_clients: dict[str, OpenAI] = {}
_httpx_clients: dict[str, httpx.Client] = {}


def _get_openai_client(api_key: str, base_url: str) -> OpenAI | None:
    cache_key = f"{api_key}::{base_url}"
    if cache_key not in _openai_clients:
        try:
            _openai_clients[cache_key] = OpenAI(api_key=api_key, base_url=base_url)
        except Exception:
            return None
    return _openai_clients[cache_key]


def _get_httpx_client(base_url: str) -> httpx.Client:
    if base_url not in _httpx_clients:
        _httpx_clients[base_url] = httpx.Client(timeout=60)
    return _httpx_clients[base_url]


def _postprocess(text: str, max_chars: int = settings.MAX_CHARACTERS) -> str:
    """Normaliza el texto y lo muestra en una sola línea (sin saltos)."""
    if not text:
        return ""
    text = text.strip()
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    if not lines:
        return ""
    result = " ".join(lines)
    if len(result) > max_chars:
        result = result[: max_chars - 1] + "…"
    return result


def get_short_answer(prompt: str, model: Optional[str] = None, history: Optional[list[dict]] = None) -> str:
    """Usa el proveedor activo o auto-fallback."""
    active = os.getenv("ACTIVE_BACKEND") or "auto"

    def _model_for(provider_key: str) -> str:
        return model or os.getenv(provider_model_var(provider_key)) or provider_default_model(provider_key)

    def _build_messages(history: list[dict]) -> list[dict]:
        system = {"role": "system", "content": "Respond in the same language as the user. Be very brief and direct, maximum 3 lines."}
        return [system] + history

    def _call_openai_like(base_url: str, api_key_env: str, model_id: str) -> Optional[str]:
        api_key = os.getenv(api_key_env)
        if not api_key:
            return None
        client = _get_openai_client(api_key, base_url)
        if client is None:
            return None
        try:
            messages = _build_messages(history) if history else [
                {"role": "system", "content": "Respond in the same language as the user. Be very brief and direct, maximum 3 lines."},
                {"role": "user", "content": prompt},
            ]
            resp = client.chat.completions.create(
                model=model_id,
                messages=messages,
                max_tokens=150,
                temperature=0.3,
            )
            return resp.choices[0].message.content
        except Exception:
            return None

    def _call_gemini(model_id: str) -> Optional[str]:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            return None
        try:
            client = _get_httpx_client("https://generativelanguage.googleapis.com")
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_id}:generateContent?key={api_key}"
            if history:
                contents = [{"role": m["role"], "parts": [{"text": m["content"]}]} for m in history]
            else:
                contents = [{"role": "user", "parts": [{"text": prompt}]}]
            payload = {
                "contents": contents,
                "generationConfig": {"maxOutputTokens": 150, "temperature": 0.3},
            }
            resp = client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data["candidates"][0]["content"]["parts"][0]["text"]
        except Exception:
            return None

    def _call_claude(model_id: str) -> Optional[str]:
        api_key = os.getenv("CLAUDE_API_KEY")
        if not api_key:
            return None
        try:
            client = _get_httpx_client("https://api.anthropic.com")
            url = "https://api.anthropic.com/v1/messages"
            headers = {
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            }
            if history:
                messages = [{"role": m["role"], "content": m["content"]} for m in history]
            else:
                messages = [{"role": "user", "content": prompt}]
            payload = {
                "model": model_id,
                "max_tokens": 150,
                "messages": messages,
            }
            resp = client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            parts = data.get("content", [])
            if parts:
                return parts[0].get("text")
            return None
        except Exception:
            return None

    if active == "groq":
        result = groq_backend.get_short_answer_groq(prompt, _model_for("groq"), history=history)
        return _postprocess(result) if result is not None else _postprocess(_util.simulate_answer(prompt))

    if active in PROVIDERS and active != "auto":
        if active in ("openai", "github-copilot"):
            result = _call_openai_like("https://api.openai.com/v1", "OPENAI_API_KEY", _model_for("openai"))
            return _postprocess(result) if result is not None else _postprocess(_util.simulate_answer(prompt))
        if active == "claude":
            result = _call_claude(_model_for("claude"))
            return _postprocess(result) if result is not None else _postprocess(_util.simulate_answer(prompt))
        if active == "gemini":
            result = _call_gemini(_model_for("gemini"))
            return _postprocess(result) if result is not None else _postprocess(_util.simulate_answer(prompt))
        return _postprocess(_util.simulate_answer(prompt))

    # auto: intenta Groq y luego cae a local
    result = groq_backend.get_short_answer_groq(prompt, _model_for("groq"), history=history)
    if result is not None:
        return _postprocess(result)

    return _postprocess(_util.simulate_answer(prompt))

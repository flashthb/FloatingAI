"""Backend para Groq (gratuito, OpenAI-compatible, rápido).

Requiere variable de entorno GROQ_API_KEY con el token de
https://console.groq.com
"""
import os
from openai import OpenAI
from ai.catalog import provider_default_model

_clients: dict[str, OpenAI] = {}


def _get_client(api_key: str, base_url: str) -> OpenAI | None:
    cache_key = f"{api_key}::{base_url}"
    if cache_key not in _clients:
        try:
            _clients[cache_key] = OpenAI(api_key=api_key, base_url=base_url)
        except Exception:
            return None
    return _clients[cache_key]


def get_short_answer_groq(prompt: str, model: str | None = None, history: list[dict] | None = None) -> str | None:
    """Llama a Groq. Devuelve None si no hay clave."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return None
    client = _get_client(api_key, "https://api.groq.com/openai/v1")
    if client is None:
        return None

    system = (
        "Eres un asistente que responde de forma muy breve y directa. "
        "Responde en un máximo de 3 líneas, sin explicaciones adicionales."
    )
    try:
        if history:
            messages = [{"role": "system", "content": system}] + history
        else:
            messages = [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ]
        resp = client.chat.completions.create(
            model=model or os.getenv("GROQ_MODEL") or provider_default_model("groq"),
            messages=messages,
            max_tokens=150,
            temperature=0.3,
        )
        return resp.choices[0].message.content
    except Exception as e:
        return f"(error Groq) {e}"

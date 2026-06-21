"""Cliente que prueba backends de IA en orden:

1. Groq (si GROQ_API_KEY configurada, gratuito y rápido)
2. Simulador local (si no hay clave configurada)
"""
from typing import Optional
from . import _util, groq_backend
from config import settings


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


def get_short_answer(prompt: str, model: Optional[str] = None) -> str:
    """Prueba Groq → Simulador."""
    # 1 – Groq (gratuito, rápido)
    result = groq_backend.get_short_answer_groq(prompt)
    if result is not None:
        return _postprocess(result)

    # 2 – Simulador local
    return _postprocess(_util.simulate_answer(prompt))

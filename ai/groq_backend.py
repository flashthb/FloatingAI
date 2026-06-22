"""Backend para Groq (gratuito, OpenAI-compatible, rápido).

Requiere variable de entorno GROQ_API_KEY con el token de
https://console.groq.com
"""
import os
from ai.catalog import provider_default_model


def get_short_answer_groq(prompt: str, model: str | None = None) -> str | None:
    """Llama a Groq. Devuelve None si no hay clave."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return None
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key, base_url="https://api.groq.com/openai/v1")
    except Exception:
        return None

    system = (
        "Eres un asistente que responde de forma muy breve y directa. "
        "Responde en un máximo de 3 líneas, sin explicaciones adicionales."
    )
    try:
        resp = client.chat.completions.create(
            model=model or os.getenv("GROQ_MODEL") or provider_default_model("groq"),
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            max_tokens=150,
            temperature=0.3,
        )
        return resp.choices[0].message.content
    except Exception as e:
        return f"(error Groq) {e}"

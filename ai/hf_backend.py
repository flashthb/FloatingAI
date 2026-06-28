"""Backend para Hugging Face Inference API (gratuito con token).

Requiere variable de entorno HF_API_KEY con un token gratuito de
huggingface.co (Settings -> Access Tokens).
"""
import os
import httpx
from config import settings


def get_short_answer_hf(prompt: str) -> str | None:
    """Llama a Hugging Face Inference API y devuelve texto o None si falla."""
    token = os.getenv('HF_API_KEY')
    if not token:
        return None

    model = settings.HF_MODEL
    url = f"https://api-inference.huggingface.co/models/{model}"
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": 150,
            "temperature": 0.2,
            "return_full_text": False,
        },
    }

    try:
        resp = httpx.post(url, headers=headers, json=payload, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        if isinstance(data, list) and len(data) > 0:
            text = data[0].get("generated_text", "")
            return text.strip()
        if isinstance(data, dict) and "error" in data:
            return None
        return None
    except Exception:
        return None

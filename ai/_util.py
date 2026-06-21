"""Utilidades internas para el módulo AI (simulador)."""
import textwrap


def simulate_answer(prompt: str) -> str:
    """Genera una respuesta simulada y breve para desarrollo sin clave."""
    if not prompt or not prompt.strip():
        return "Escribe una pregunta breve."
    # Respuesta: eco reducido + sugerencia
    first = prompt.strip().split('\n', 1)[0]
    # Keep it short
    answer = f"Simulado: {first[:120]}"
    return answer

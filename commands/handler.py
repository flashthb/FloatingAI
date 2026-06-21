"""Módulo de comandos internos del launcher.

Comandos disponibles:
  /help         — Muestra esta ayuda
  /close        — Cierra la aplicación
  /models       — Muestra los backends y su estado
  /key <bk> <k> — Guarda la clave de un backend en .env
  /remove <bk>  — Elimina la clave de un backend del .env
  /model <bk>   — Define el backend activo (groq, openai, gemini, claude)
"""
import os
import sys
from pathlib import Path
from PySide6.QtCore import QTimer

ENV_PATH = Path(__file__).resolve().parent.parent / '.env'

BACKENDS = {
    "groq":   {"var": "GROQ_API_KEY",   "label": "Groq"},
    "openai": {"var": "OPENAI_API_KEY",  "label": "OpenAI"},
    "gemini": {"var": "GEMINI_API_KEY",  "label": "Gemini"},
    "claude": {"var": "CLAUDE_API_KEY",  "label": "Claude"},
}

ACTIVE_BACKEND = None  # None = auto


# ── lectura / escritura de .env ─────────────────────────────────

def _read_env() -> dict[str, str]:
    if not ENV_PATH.exists():
        return {}
    result = {}
    for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        result[k.strip()] = v.strip()
    return result


def _write_env(data: dict[str, str]) -> None:
    lines = [f"{k}={v}" for k, v in data.items() if v]
    ENV_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


# ── ayuda ────────────────────────────────────────────────────────

def _help() -> str:
    return (
        "Comandos disponibles:\n"
        "  /help              — Esta ayuda\n"
        "  /close             — Cerrar la app\n"
        "  /models            — Ver backends y su estado\n"
        "  /key <bk> <clave>  — Guardar clave de un backend\n"
        "  /remove <bk>       — Eliminar clave de un backend\n"
        "  /model <bk>        — Elegir backend activo\n\n"
        "Backends: groq, openai, gemini, claude"
    )


# ── /models ──────────────────────────────────────────────────────

def _models() -> str:
    env = _read_env()
    lines = ["Backends disponibles:"]
    for key, info in BACKENDS.items():
        configured = info["var"] in env and env[info["var"]]
        status = "✅ activo" if configured else "❌ sin clave"
        marker = " → activo" if ACTIVE_BACKEND == key else ""
        lines.append(f"  {info['label']:8s}  {status}{marker}")
    lines.append(f"\nActivo: {ACTIVE_BACKEND or 'auto'}")
    return "\n".join(lines)


# ── /key ─────────────────────────────────────────────────────────

def _key(args: list[str]) -> str:
    if len(args) < 2:
        return "Uso: /key <backend> <clave>\nEj: /key groq gsk_..."
    backend = args[0].lower()
    if backend not in BACKENDS:
        return f"Backend desconocido: {backend}. Usa /models para ver los disponibles."
    secret = " ".join(args[1:])
    var = BACKENDS[backend]["var"]

    env = _read_env()
    env[var] = secret
    _write_env(env)
    os.environ[var] = secret

    return f"✅ Clave de {BACKENDS[backend]['label']} guardada."


# ── /remove ──────────────────────────────────────────────────────

def _remove(args: list[str]) -> str:
    if not args:
        return "Uso: /remove <backend>\nEj: /remove groq"
    backend = args[0].lower()
    if backend not in BACKENDS:
        return f"Backend desconocido: {backend}."
    var = BACKENDS[backend]["var"]

    env = _read_env()
    removed = env.pop(var, None)
    _write_env(env)
    os.environ.pop(var, None)

    if removed:
        return f"🗑️ Clave de {BACKENDS[backend]['label']} eliminada."
    return f"No había clave configurada para {BACKENDS[backend]['label']}."


# ── /model ───────────────────────────────────────────────────────

def _model(args: list[str]) -> str:
    global ACTIVE_BACKEND
    if not args:
        return f"Backend activo: {ACTIVE_BACKEND or 'auto'}"
    backend = args[0].lower()
    if backend == "auto":
        ACTIVE_BACKEND = None
        return "Modo automático (prueba todos los backends con clave)."
    if backend not in BACKENDS:
        return f"Backend desconocido: {backend}. Opciones: {', '.join(BACKENDS)}"
    ACTIVE_BACKEND = backend
    return f"✅ Backend activo cambiado a {BACKENDS[backend]['label']}."


# ── punto de entrada ─────────────────────────────────────────────

def execute(cmd_str: str, app) -> str:
    """Ejecuta un comando (texto que empieza por /) y devuelve texto a mostrar."""
    parts = cmd_str.strip().split()
    if not parts:
        return ""
    cmd = parts[0].lower()
    args = parts[1:]

    if cmd == "/help":
        return _help()
    if cmd in ("/close", "/quit"):
        QTimer.singleShot(100, app.quit)
        return "Cerrando..."
    if cmd == "/models":
        return _models()
    if cmd == "/key":
        return _key(args)
    if cmd == "/remove":
        return _remove(args)
    if cmd == "/model":
        return _model(args)
    # /clear implícito — se limpia solo al enviar
    return (
        f"Comando desconocido: {cmd}\n"
        "Escribe /help para ver los comandos disponibles."
    )


def any_key_configured() -> bool:
    """Devuelve True si al menos un backend tiene clave configurada."""
    env = _read_env()
    for info in BACKENDS.values():
        if env.get(info["var"]):
            return True
    return False


COMMAND_LIST = [
    "/help", "/close", "/models",
    "/key groq ...", "/key openai ...", "/key gemini ...", "/key claude ...",
    "/remove groq", "/remove openai", "/remove gemini", "/remove claude",
    "/model groq", "/model openai", "/model auto",
]

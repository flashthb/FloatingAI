"""Configuración básica del launcher.

No se almacenan claves en ficheros. La clave de OpenAI se lee desde la variable
de entorno OPENAI_API_KEY.
"""

HOTKEY = '<ctrl>+<shift>+<space>'
WINDOW_WIDTH = 680
WINDOW_HEIGHT = 200
MODEL = 'gpt-3.5-turbo'
HF_MODEL = 'HuggingFaceH4/zephyr-7b-beta'
MAX_LINES = 5
MAX_CHARACTERS = 600

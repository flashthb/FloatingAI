# FloatingAI

Desktop AI assistant for Windows. Press Ctrl+Shift+Space anywhere to open a frameless input window, type your question, and get an AI response. Esc to close. Runs in the system tray.

Supports Groq, OpenAI, Claude, and Gemini. Built with PySide6, packaged as a single portable .exe with PyInstaller. Settings window lets you pick fonts, configure API keys, select provider and model, and enable auto-start with Windows.

![Launcher](screenshots/launcher.png)
![Settings](screenshots/settings.png)
![Settings - API](screenshots/settings_api.png)

## Download

Download `FloatingAI.exe` from [Releases](https://github.com/flashthb/FloatingAI/releases), run it. No installation.

Get an API key from [Groq](https://console.groq.com), [OpenAI](https://platform.openai.com), [Anthropic](https://console.anthropic.com), or [Google](https://aistudio.google.com), then right-click the tray icon → Settings → API.

## Run from source

```bash
git clone https://github.com/flashthb/FloatingAI.git
cd FloatingAI
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

## Build .exe

```bash
pip install pyinstaller
pyinstaller --noconsole --onefile --name FloatingAI --add-data "assets/fonts;assets/fonts" main.py
```

Output: `dist\FloatingAI.exe`.

## Structure

```
main.py                 Entry point, system tray, hotkey, fonts
ui/                     launcher_window.py, settings_window.py
ai/                     client.py, groq_backend.py, catalog.py, worker.py
hotkeys/listener.py     Global hotkey wrapper
config/settings.py      Constants
assets/fonts/           Bundled .ttf fonts
```

## License

MIT

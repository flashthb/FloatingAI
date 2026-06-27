# FloatingAI

A lightweight, always-on-top desktop AI assistant for Windows. Built with PySide6.

Press **Ctrl+Shift+Space** anywhere to ask a question — it appears as a clean, frameless overlay. Runs in your system tray, ready when you need it.

## Features

- **Global hotkey** — Ctrl+Shift+Space opens the input window from anywhere
- **Multiple AI providers** — Groq, OpenAI, Claude, Gemini
- **Conversation history** — the window keeps context while open (resets on close)
- **Custom fonts** — pick from bundled fonts (IBM Plex Mono, Fira Code, JetBrains Mono, etc.)
- **Minimalist design** — dark squared theme, frameless, drop shadow, fade animations
- **System tray** — runs in background, never in your way
- **Single-instance** — only one instance runs at a time (even on autostart)
- **Auto-start** — register to launch with Windows
- **No installation** — just download the .exe and run
- **Portable** — all settings persist in `%APPDATA%\FloatingAI\.env`

## Screenshots

![Launcher](screenshots/launcher.png)
*The main input window, shown on global hotkey*

![Settings](screenshots/settings.png)
*Settings window with Design and API tabs*

## Installation

### Option A — Download the executable (recommended)

1. Go to the [Releases](https://github.com/yourusername/FloatingAI/releases) page
2. Download `FloatingAI.exe`
3. Run it — no installation required
4. Get a free API key from [Groq](https://console.groq.com), [OpenAI](https://platform.openai.com), [Anthropic](https://console.anthropic.com), or [Google](https://aistudio.google.com)
5. Right-click the tray icon → **Settings** → **API** → add your key

### Option B — Run from source

```bash
git clone https://github.com/yourusername/FloatingAI.git
cd FloatingAI
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

### Option C — Build your own .exe

```bash
pip install pyinstaller
pyinstaller --noconsole --onefile --name FloatingAI --add-data "assets/fonts;assets/fonts" main.py
# Output: dist\FloatingAI.exe
```

## Usage

| Action | Result |
|--------|--------|
| `Ctrl+Shift+Space` | Open the input window |
| Type + `Enter` | Send a question to the AI |
| `Esc` | Close the window (history is cleared) |
| Click outside | Window fades away |
| Tray icon → **Open** | Show the input window |
| Tray icon → **Settings** | Configure fonts, API keys, providers |
| Tray icon → **Quit** | Exit the application |

### How it works

- The window is **frameless and always-on-top** so it appears instantly
- The AI response appears in the window below the input field
- **Conversation history is maintained** while the window is open — you can ask follow-up questions
- When you close the window, history resets — each session is fresh

### Changing the AI provider

1. Open **Settings** → **API** tab
2. Select a provider from the dropdown (only providers with configured keys are shown)
3. Select the model
4. Click **Test** to verify your API key works

## Configuration

All settings are stored in:

- **Source mode**: `./.env` (project root)
- **Executable mode**: `%APPDATA%\FloatingAI\.env`

Settings persist between sessions. You can edit the file directly or use the Settings UI.

### Available settings

| Variable | Default | Purpose |
|----------|---------|---------|
| `GROQ_API_KEY` | — | Groq API key |
| `OPENAI_API_KEY` | — | OpenAI / GitHub Copilot API key |
| `CLAUDE_API_KEY` | — | Anthropic API key |
| `GEMINI_API_KEY` | — | Google API key |
| `ACTIVE_BACKEND` | `auto` | Provider to use: `groq`, `openai`, `claude`, `gemini`, or `auto` |
| `APP_FONT` | `IBM Plex Mono` | Font for the UI |
| `GROQ_MODEL` | `llama-3.3-70b-versatile` | Groq model override |
| `OPENAI_MODEL` | `gpt-4.1` | OpenAI model override |
| `CLAUDE_MODEL` | `claude-sonnet-4-20250514` | Claude model override |
| `GEMINI_MODEL` | `gemini-2.5-flash` | Gemini model override |

## Building from source

```bash
pip install -r requirements.txt

# For development
python main.py

# For distribution
pyinstaller --noconsole --onefile --name FloatingAI --add-data "assets/fonts;assets/fonts" main.py
```

The executable will be at `dist\FloatingAI.exe`. All fonts are bundled inside — no extra files needed.

## Requirements

- Windows 10 or 11 (64-bit)
- Python 3.12+ (if running from source)
- An API key from at least one AI provider

## Tech stack

- **Python 3.12** + **PySide6** (Qt 6) for the GUI
- **pynput** for global hotkey listening
- **openai** / **httpx** for AI backend calls
- **PyInstaller** for distribution

## Project structure

```
main.py              Entry point, system tray, hotkey, fonts
ui/launcher_window.py   Frameless input window
ui/settings_window.py   Settings dialog (Design + API)
ai/client.py            AI dispatch logic
ai/groq_backend.py      Groq provider implementation
ai/catalog.py           Provider/model registry
ai/worker.py            Background AI worker (QRunnable)
ai/_util.py             Local fallback (no API key)
hotkeys/listener.py     Global hotkey wrapper
config/settings.py      Constants
assets/fonts/           Bundled .ttf fonts
```

## License

MIT

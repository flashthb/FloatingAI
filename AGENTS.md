# AGENTS.md

## What this is

PySide6 desktop launcher for Windows. Not a library. Run with `python main.py`. No tests, no linter, no typecheck.

## Structure

```
main.py              Entry point, system tray, hotkey, app font
config/settings.py   Constants (hotkey, window size, max chars)
ui/launcher_window.py   Main frameless window (input + response)
ui/settings_window.py   Settings QDialog (Design + API tabs)
ai/catalog.py        Provider/model registry, BACKENDS, any_key_configured()
ai/client.py         AI dispatch (active provider or fallback chain)
ai/groq_backend.py   Groq API call (OpenAI-compatible)
ai/worker.py         QRunnable for background AI calls
ai/_util.py          Local simulator fallback
hotkeys/listener.py  pynput GlobalHotKeys wrapper
assets/fonts/        Local .ttf files loaded at startup
.env                 Runtime config (keys, font, active backend/model)
```

## Run

```bash
python main.py
```

## Config

`.env` is the source of truth. Read at startup by `_load_env()` in `main.py`. Keys:
- `GROQ_API_KEY`, `OPENAI_API_KEY`, `GEMINI_API_KEY`, `CLAUDE_API_KEY`
- `APP_FONT` (e.g. `Fira Code`)
- `ACTIVE_BACKEND` (e.g. `groq`, `openai`, `claude`, `gemini`, or absent for auto)
- `GROQ_MODEL`, `OPENAI_MODEL`, `CLAUDE_MODEL`, `GEMINI_MODEL`

`.env` is gitignored. `_read_env()` / `_write_env()` exist in both `ai/catalog.py` and `ui/settings_window.py` — they are duplicates by design (avoid circular imports).

## QSS + font rules

- Use separate `font-size` + `font-family` properties, NOT the `font:` shorthand. Qt QSS parser chokes on comma-separated font families in the shorthand → causes `QFont::setPointSize: Point size <= 0 (-1)` warning.
- Font names must match exactly what `QFontDatabase.families()` returns. Variable fonts in `assets/fonts/` use `%5Bwght%5D` literal characters in filenames (URL-encoded brackets), not `[wght]`.
- All explicit `QFont` objects use `setHintingPreference(QFont.PreferFullHinting)` — not `setStyleStrategy(QFont.PreferAntialias)`.

## QComboBox popup bug

Frameless + translucent windows cause combo popups to sometimes not close on click. Current mitigation in `settings_window.py`:
1. `view.setAttribute(Qt.WA_TranslucentBackground, False)` on view and popup window
2. `combo.activated.connect(lambda _, c=combo: QTimer.singleShot(0, c.hidePopup))`
3. `view.clicked.connect(...)` same pattern
4. `hidePopup()` at end of `_on_provider_changed` / `_on_model_changed`

If adding more combos, copy this exact pattern.

## Signal order in SettingsWindow

`_load_state()` MUST be called BEFORE connecting signals (`currentTextChanged`, `currentIndexChanged`). Otherwise the combo populates → signal fires → writes wrong value to `.env`. Current order in `__init__`:
1. `_build_ui()`
2. `_apply_styles()`
3. `_load_state()`
4. connect signals

When repopulating combos in `_load_state` or handlers, use `blockSignals(True/False)`.

## AI backend dispatch

`ai/client.py: get_short_answer()` reads `ACTIVE_BACKEND` and `*_MODEL` env vars. Groq is the only fully implemented backend. OpenAI, Claude, and Gemini call their APIs directly via `openai` or `httpx` but are guarded by key presence. Fallback is always `ai/_util.py: simulate_answer()`.

The provider/model catalog lives in `ai/catalog.py`. `PROVIDERS` dict is the single source for labels, env var names, default models, and model lists.

## Platform notes

- Windows only (pynput GlobalHotKeys, Windows system tray)
- `Qt.Tool` flag on main window prevents it from stealing taskbar focus
- `WA_TranslucentBackground` on main window + settings window — affects shadow rendering and QComboBox behavior

import os
import sys
import winreg
from pathlib import Path
from PySide6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QComboBox, QLineEdit, QStackedWidget, QScrollArea,
    QFrame, QApplication, QCheckBox,
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtGui import QFont, QFontDatabase
from ai.catalog import (
    PROVIDERS, BACKENDS,
    provider_default_model, provider_models, provider_model_var,
)

ENV_PATH_HOME = Path(os.environ.get("APPDATA", Path.home())) / "FloatingAI" / ".env"


def _env_path() -> Path:
    if getattr(sys, 'frozen', False):
        ENV_PATH_HOME.parent.mkdir(parents=True, exist_ok=True)
        if not ENV_PATH_HOME.exists():
            bundled = Path(sys._MEIPASS) / '.env'
            if bundled.exists():
                ENV_PATH_HOME.write_text(bundled.read_text(encoding="utf-8"), encoding="utf-8")
        return ENV_PATH_HOME
    return Path(__file__).resolve().parent.parent / '.env'

_AUTOSTART_REG_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
_AUTOSTART_REG_NAME = "FloatingAI"


def _autostart_command() -> str:
    if getattr(sys, 'frozen', False):
        return f'"{sys.executable}"'
    python = Path(sys.executable)
    pythonw = python.parent / "pythonw.exe"
    if pythonw.exists():
        python = pythonw
    script = str(Path(__file__).resolve().parent.parent / "main.py")
    return f'"{python}" "{script}"'


def _autostart_is_enabled() -> bool:
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, _AUTOSTART_REG_KEY, 0, winreg.KEY_READ)
        winreg.QueryValueEx(key, _AUTOSTART_REG_NAME)
        winreg.CloseKey(key)
        return True
    except FileNotFoundError:
        return False


def _autostart_set(enabled: bool) -> None:
    if enabled:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, _AUTOSTART_REG_KEY, 0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, _AUTOSTART_REG_NAME, 0, winreg.REG_SZ, _autostart_command())
        winreg.CloseKey(key)
    else:
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, _AUTOSTART_REG_KEY, 0, winreg.KEY_SET_VALUE)
            winreg.DeleteValue(key, _AUTOSTART_REG_NAME)
            winreg.CloseKey(key)
        except FileNotFoundError:
            pass


def _read_env() -> dict[str, str]:
    env = _env_path()
    if not env.exists():
        return {}
    result = {}
    for line in env.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        result[k.strip()] = v.strip()
    return result


def _write_env(data: dict[str, str]) -> None:
    env = _env_path()
    lines = [f"{k}={v}" for k, v in data.items() if v]
    env.write_text("\n".join(lines) + "\n", encoding="utf-8")


PREFERRED_FONTS = [
    "IBM Plex Mono",
    "Fira Code",
    "Cascadia Code",
    "JetBrains Mono",
    "Consolas",
    "Cascadia Mono",
]


_TEST_ENDPOINTS = {
    "groq":    ("https://api.groq.com/openai/v1/models", "Bearer"),
    "openai":  ("https://api.openai.com/v1/models", "Bearer"),
    "deepseek":("https://api.deepseek.com/models", "Bearer"),
}


class KeyTester(QThread):
    finished = Signal(str, str)  # backend_key, message

    def __init__(self, backend_key: str, api_key: str):
        super().__init__()
        self.backend_key = backend_key
        self.api_key = api_key

    def run(self):
        import httpx

        ep = _TEST_ENDPOINTS.get(self.backend_key)
        if not ep:
            self.finished.emit(self.backend_key, "N/A")
            return

        url, auth_type = ep
        try:
            resp = httpx.get(
                url,
                headers={"Authorization": f"{auth_type} {self.api_key}"},
                timeout=10,
            )
            if resp.status_code == 200:
                self.finished.emit(self.backend_key, "✓")
            elif resp.status_code == 401:
                self.finished.emit(self.backend_key, "✗ invalid key")
            else:
                self.finished.emit(self.backend_key, f"✗ HTTP {resp.status_code}")
        except Exception as e:
            self.finished.emit(self.backend_key, f"✗ {type(e).__name__}")


class SettingsWindow(QDialog):
    def __init__(self, parent=None, app=None, launcher=None):
        super().__init__(parent)
        self._app = app
        self._launcher = launcher

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(760, 560)

        self._build_ui()
        self._apply_styles()
        self._load_state()
        self.font_combo.currentTextChanged.connect(self._on_font_changed)
        self.provider_combo.currentIndexChanged.connect(self._on_provider_changed)
        self.model_combo.currentIndexChanged.connect(self._on_model_changed)
        for combo in (self.font_combo, self.provider_combo, self.model_combo):
            view = combo.view()
            view.setAttribute(Qt.WA_TranslucentBackground, False)
            view.window().setAttribute(Qt.WA_TranslucentBackground, False)
            combo.activated.connect(lambda _, c=combo: QTimer.singleShot(0, c.hidePopup))
            view.clicked.connect(lambda _, c=combo: QTimer.singleShot(0, c.hidePopup))

    def _build_ui(self):
        self.container = QFrame()
        self.container.setObjectName("settingsContainer")

        outer = QVBoxLayout(self)
        outer.setContentsMargins(12, 12, 12, 12)
        outer.addWidget(self.container)

        inner = QVBoxLayout(self.container)
        inner.setContentsMargins(0, 0, 0, 0)
        inner.setSpacing(0)

        # ── title bar ──
        title_bar = QWidget()
        title_bar.setObjectName("settingsTitleBar")
        title_row = QHBoxLayout(title_bar)
        title_row.setContentsMargins(16, 10, 10, 10)
        title_row.setSpacing(0)

        title_label = QLabel("Settings")
        title_label.setObjectName("settingsTitleLabel")

        close_btn = QPushButton("✕")
        close_btn.setObjectName("settingsCloseBtn")
        close_btn.setFixedSize(28, 28)
        close_btn.clicked.connect(self.close)

        title_row.addWidget(title_label)
        title_row.addStretch()
        title_row.addWidget(close_btn)
        inner.addWidget(title_bar)

        # ── body ──
        body = QWidget()
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)

        # sidebar
        sidebar = QWidget()
        sidebar.setObjectName("settingsSidebar")
        sidebar.setFixedWidth(140)
        side_layout = QVBoxLayout(sidebar)
        side_layout.setContentsMargins(12, 20, 12, 20)
        side_layout.setSpacing(4)

        self._nav_btns = []
        for name in ("Design", "API"):
            btn = QPushButton(name)
            btn.setObjectName("navBtn")
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            self._nav_btns.append(btn)
            side_layout.addWidget(btn)
        side_layout.addStretch()

        self._nav_btns[0].setChecked(True)
        self._nav_btns[0].clicked.connect(lambda: self._switch_page(0))
        self._nav_btns[1].clicked.connect(lambda: self._switch_page(1))

        # stack
        self.stack = QStackedWidget()
        self.stack.setObjectName("settingsStack")

        self.stack.addWidget(self._build_design_page())
        self.stack.addWidget(self._build_api_page())

        body_layout.addWidget(sidebar)
        body_layout.addWidget(self.stack)
        inner.addWidget(body)

    # ── design page ──────────────────────────────────────────

    def _build_design_page(self) -> QWidget:
        page = QWidget()
        page.setObjectName("settingsPage")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(16)

        title = QLabel("Font")
        title.setObjectName("sectionTitle")
        layout.addWidget(title)

        self.font_combo = QComboBox()
        self.font_combo.setObjectName("fontCombo")
        self.font_combo.setMinimumWidth(220)

        db = QFontDatabase()
        available = set(db.families())
        for f in PREFERRED_FONTS:
            if f in available:
                self.font_combo.addItem(f)
        # ensure the saved font is always present in the combo
        saved = _read_env().get("APP_FONT")
        if saved and self.font_combo.findText(saved) < 0:
            self.font_combo.addItem(saved)

        layout.addWidget(self.font_combo)

        info = QLabel("Changes apply immediately to the main window.")
        info.setObjectName("hintLabel")
        layout.addWidget(info)

        layout.addSpacing(12)

        startup_title = QLabel("Startup")
        startup_title.setObjectName("sectionTitle")
        layout.addWidget(startup_title)

        self.autostart_check = QCheckBox("Open on system startup")
        self.autostart_check.setObjectName("autostartCheck")
        self.autostart_check.setChecked(_autostart_is_enabled())
        self.autostart_check.toggled.connect(self._on_autostart_toggled)
        layout.addWidget(self.autostart_check)

        startup_hint = QLabel("Adds FloatingAI to Windows startup via registry.")
        startup_hint.setObjectName("hintLabel")
        layout.addWidget(startup_hint)

        layout.addStretch()
        return page

    # ── api page ─────────────────────────────────────────────

    def _build_api_page(self) -> QWidget:
        page = QWidget()
        page.setObjectName("settingsPage")

        outer = QVBoxLayout(page)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setObjectName("settingsScroll")

        content = QWidget()
        content.setObjectName("settingsPage")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(16)

        selector_card = QFrame()
        selector_card.setObjectName("apiSelectorCard")
        selector_layout = QVBoxLayout(selector_card)
        selector_layout.setContentsMargins(18, 18, 18, 18)
        selector_layout.setSpacing(12)

        provider_label = QLabel("Provider")
        provider_label.setObjectName("sectionTitle")
        selector_layout.addWidget(provider_label)

        self.provider_combo = QComboBox()
        self.provider_combo.setObjectName("providerCombo")
        self.provider_combo.setMinimumHeight(36)
        self.provider_combo.setMinimumWidth(380)
        selector_layout.addWidget(self.provider_combo)

        model_label = QLabel("Submodel")
        model_label.setObjectName("sectionTitle")
        selector_layout.addWidget(model_label)

        self.model_combo = QComboBox()
        self.model_combo.setObjectName("modelCombo")
        self.model_combo.setMinimumHeight(36)
        self.model_combo.setMinimumWidth(380)
        selector_layout.addWidget(self.model_combo)

        api_hint = QLabel("Only providers with a saved key are shown. Choose a provider first, then its model.")
        api_hint.setObjectName("hintLabel")
        api_hint.setWordWrap(True)
        selector_layout.addWidget(api_hint)

        layout.addWidget(selector_card)

        # separator
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("background: #2a2a2a; max-height: 1px;")
        layout.addWidget(sep)

        # keys
        keys_label = QLabel("API Keys")
        keys_label.setObjectName("sectionTitle")
        layout.addWidget(keys_label)

        keys_subtitle = QLabel("Save a key to unlock the provider and its submodels.")
        keys_subtitle.setObjectName("hintLabel")
        keys_subtitle.setWordWrap(True)
        layout.addWidget(keys_subtitle)

        self._key_widgets = {}
        for key, info in BACKENDS.items():
            row = self._key_row(key, info)
            self._key_widgets[key] = row
            layout.addWidget(row["widget"])

        layout.addStretch()
        scroll.setWidget(content)
        outer.addWidget(scroll)
        return page

    def _key_row(self, backend_key: str, info: dict) -> dict:
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        dot = QLabel("●")
        dot.setObjectName("statusDot")
        dot.setFixedWidth(16)

        name = QLabel(info["label"])
        name.setObjectName("keyName")
        name.setFixedWidth(96)

        inp = QLineEdit()
        inp.setObjectName("keyInput")
        inp.setPlaceholderText("Paste your API key...")
        inp.setEchoMode(QLineEdit.Password)
        inp.setMinimumHeight(30)

        save_btn = QPushButton("Save")
        save_btn.setObjectName("keySaveBtn")
        save_btn.setCursor(Qt.PointingHandCursor)
        save_btn.setMinimumHeight(30)

        remove_btn = QPushButton("Remove")
        remove_btn.setObjectName("keyRemoveBtn")
        remove_btn.setCursor(Qt.PointingHandCursor)
        remove_btn.setMinimumHeight(30)

        status_label = QLabel("")
        status_label.setObjectName("keyStatusLabel")
        status_label.setFixedWidth(14)

        env = _read_env()
        var = info["var"]
        if env.get(var):
            inp.setText(env[var])
            dot.setStyleSheet("color: #4ade80; font-size: 10px;")
        else:
            dot.setStyleSheet("color: #555555; font-size: 10px;")

        def on_save():
            val = inp.text().strip()
            if not val:
                return
            save_btn.setEnabled(False)
            save_btn.setText("...")
            status_label.setText("…")
            status_label.setStyleSheet("color: #888888;")
            tester = KeyTester(backend_key, val)
            if not hasattr(self, '_testers'):
                self._testers = {}
            self._testers[backend_key] = tester
            tester.finished.connect(
                lambda bk, msg: self._on_save_result(bk, msg, val)
            )
            tester.finished.connect(lambda bk, _: self._testers.pop(bk, None))
            tester.start()

        def on_remove():
            env = _read_env()
            env.pop(var, None)
            _write_env(env)
            os.environ.pop(var, None)
            inp.clear()
            dot.setStyleSheet("color: #555555; font-size: 10px;")
            status_label.setText("")

        save_btn.clicked.connect(on_save)
        remove_btn.clicked.connect(on_remove)

        layout.addWidget(dot)
        layout.addWidget(name)
        layout.addWidget(inp)
        layout.addWidget(save_btn)
        layout.addWidget(remove_btn)
        layout.addWidget(status_label)

        # force antialiasing on labels
        f = name.font()
        f.setHintingPreference(QFont.PreferFullHinting)
        name.setFont(f)

        return {
            "widget": widget,
            "dot": dot,
            "inp": inp,
            "save_btn": save_btn,
            "status": status_label,
            "var": var,
        }

    def _on_save_result(self, backend_key: str, message: str, key_val: str):
        row = self._key_widgets.get(backend_key)
        if not row:
            return
        label = row["status"]
        save_btn = row["save_btn"]
        inp = row["inp"]
        dot = row["dot"]

        save_btn.setEnabled(True)
        save_btn.setText("Save")

        if message == "✓":
            env = _read_env()
            env[row["var"]] = key_val
            _write_env(env)
            os.environ[row["var"]] = key_val
            dot.setStyleSheet("color: #4ade80; font-size: 10px;")
            inp.setEchoMode(QLineEdit.Password)
            label.setText("✓")
            label.setStyleSheet("color: #4ade80;")
            self._load_state()
        else:
            label.setText("✗")
            label.setStyleSheet("color: #ff5555;")
            label.setToolTip(message)

    # ── slots ────────────────────────────────────────────────

    def _switch_page(self, index: int):
        for i, btn in enumerate(self._nav_btns):
            btn.setChecked(i == index)
        self.stack.setCurrentIndex(index)

    def _on_font_changed(self, font_name: str):
        if not font_name or not self._app:
            return
        env = _read_env()
        env["APP_FONT"] = font_name
        _write_env(env)
        os.environ["APP_FONT"] = font_name
        f = QFont(font_name, 10)
        f.setHintingPreference(QFont.PreferFullHinting)
        self._app.setFont(f)
        if self._launcher:
            self._launcher.update_font(font_name)
        # re-apply own stylesheet so settings window uses the new font too
        self._apply_styles(font_name)

    def _on_provider_changed(self, idx: int):
        provider = self.provider_combo.currentData()
        env = _read_env()
        if provider == "auto":
            env.pop("ACTIVE_BACKEND", None)
            os.environ.pop("ACTIVE_BACKEND", None)
        else:
            env["ACTIVE_BACKEND"] = provider
            os.environ["ACTIVE_BACKEND"] = provider
        _write_env(env)
        self._populate_model_combo(provider, env)
        QTimer.singleShot(0, self.provider_combo.hidePopup)

    def _on_model_changed(self, idx: int):
        provider = self.provider_combo.currentData()
        if not provider or provider == "auto":
            return
        model_id = self.model_combo.currentData()
        if not model_id:
            return
        env = _read_env()
        env[provider_model_var(provider)] = model_id
        _write_env(env)
        os.environ[provider_model_var(provider)] = model_id
        QTimer.singleShot(0, self.model_combo.hidePopup)

    def _on_autostart_toggled(self, checked: bool):
        _autostart_set(checked)

    # ── load ─────────────────────────────────────────────────

    def _populate_provider_combo(self, env: dict[str, str]) -> None:
        self.provider_combo.blockSignals(True)
        self.provider_combo.clear()
        self.provider_combo.addItem("Auto (first available)", "auto")
        for key, info in PROVIDERS.items():
            if env.get(info["key_var"]):
                self.provider_combo.addItem(info["label"], key)

        preferred = env.get("ACTIVE_BACKEND", "auto")
        idx = self.provider_combo.findData(preferred)
        if idx < 0:
            idx = 0
        self.provider_combo.setCurrentIndex(idx)
        self.provider_combo.blockSignals(False)

    def _populate_model_combo(self, provider: str, env: dict[str, str]) -> None:
        self.model_combo.blockSignals(True)
        self.model_combo.clear()

        if not provider or provider == "auto":
            self.model_combo.addItem("Choose a provider first", "")
            self.model_combo.setEnabled(False)
            self.model_combo.blockSignals(False)
            return

        models = provider_models(provider)
        for model_id, label in models:
            self.model_combo.addItem(label, model_id)

        current = env.get(provider_model_var(provider)) or provider_default_model(provider)
        idx = self.model_combo.findData(current)
        if idx < 0:
            self.model_combo.addItem(current, current)
            idx = self.model_combo.count() - 1

        self.model_combo.setCurrentIndex(idx)
        self.model_combo.setEnabled(True)
        self.model_combo.blockSignals(False)

    def _load_state(self):
        # block signals so setCurrentIndex doesn't trigger _on_font_changed
        self.font_combo.blockSignals(True)

        env = _read_env()
        loaded = env.get("APP_FONT") or "IBM Plex Mono"
        idx = self.font_combo.findText(loaded)
        if idx >= 0:
            self.font_combo.setCurrentIndex(idx)

        self._populate_provider_combo(env)
        provider = self.provider_combo.currentData()
        self._populate_model_combo(provider, env)

        self.font_combo.blockSignals(False)

    # ── styles ───────────────────────────────────────────────

    def _apply_styles(self, font_name: str = None):
        if font_name is None:
            env = _read_env()
            font_name = env.get("APP_FONT") or "Fira Code"
        # build the font stack with the user's chosen font first
        font_stack = f'"{font_name}", "Cascadia Code", "Consolas", monospace'

        self.setStyleSheet(f"""
            #settingsContainer {{
                background: #161618;
                border-radius: 4px;
            }}
            #settingsTitleBar {{
                background: #1a1a1c;
                border-bottom: 1px solid #2a2a2a;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }}
            #settingsTitleLabel {{
                font-size: 14px; font-family: {font_stack};
                color: #e0e0e0;
            }}
            #settingsCloseBtn {{
                background: transparent;
                border: none;
                color: #777777;
                font-size: 14px; font-family: {font_stack};
                border-radius: 4px;
            }}
            #settingsCloseBtn:hover {{
                background: #2a2a2a;
                color: #ffffff;
            }}
            #settingsSidebar {{
                background: #111111;
                border-right: 1px solid #2a2a2a;
            }}
            #navBtn {{
                background: transparent;
                border: none;
                border-radius: 4px;
                padding: 8px 12px;
                font-size: 13px; font-family: {font_stack};
                color: #999999;
                text-align: left;
            }}
            #navBtn:hover {{
                background: #1e1e1e;
                color: #cccccc;
            }}
            #navBtn:checked {{
                background: #222222;
                color: #ffffff;
            }}
            #settingsStack {{
                background: #161618;
            }}
            #settingsPage {{
                background: #161618;
            }}
            #apiSelectorCard {{
                background: #18181b;
                border: 1px solid #2a2a2a;
                border-radius: 4px;
            }}
            .sectionTitle {{
                font-size: 13px; font-family: {font_stack};
                color: #aaaaaa;
            }}
            #fontCombo, #providerCombo, #modelCombo {{
                background: #1a1a1c;
                border: 1px solid #333333;
                border-radius: 2px;
                padding: 6px 8px;
                font-size: 13px; font-family: {font_stack};
                color: #e0e0e0;
                selection-background-color: #404040;
            }}
            #fontCombo:focus, #providerCombo:focus, #modelCombo:focus {{
                border: 1px solid #ffffff;
            }}
            #fontCombo::drop-down, #providerCombo::drop-down, #modelCombo::drop-down {{
                border: none;
                width: 20px;
            }}
            #fontCombo QAbstractItemView, #providerCombo QAbstractItemView, #modelCombo QAbstractItemView {{
                background: #111111;
                border: 1px solid #242424;
                color: #cccccc;
                selection-background-color: #222222;
                font-size: 13px; font-family: {font_stack};
            }}
            #keyName {{
                font-size: 13px; font-family: {font_stack};
                color: #cccccc;
            }}
            #keyInput {{
                background: #1a1a1c;
                border: 1px solid #333333;
                border-radius: 2px;
                padding: 6px 10px;
                font-size: 12px; font-family: {font_stack};
                color: #e0e0e0;
                selection-background-color: #404040;
            }}
            #keyInput:focus {{
                border: 1px solid #ffffff;
            }}
            #keySaveBtn {{
                background: #1e1e1e;
                border: 1px solid #333333;
                border-radius: 2px;
                padding: 6px 14px;
                font-size: 12px; font-family: {font_stack};
                color: #cccccc;
            }}
            #keySaveBtn:hover {{
                background: #2a2a2a;
                border: 1px solid #555555;
                color: #ffffff;
            }}
            #keyRemoveBtn {{
                background: transparent;
                border: 1px solid #333333;
                border-radius: 2px;
                padding: 6px 14px;
                font-size: 12px; font-family: {font_stack};
                color: #aa5555;
            }}
            #keyRemoveBtn:hover {{
                background: #2a1a1a;
                border: 1px solid #883333;
                color: #ff6666;
            }}
            #hintLabel {{
                font-size: 11px; font-family: {font_stack};
                color: #555555;
            }}
            #autostartCheck {{
                font-size: 13px; font-family: {font_stack};
                color: #cccccc;
                spacing: 8px;
            }}
            #autostartCheck::indicator {{
                width: 16px;
                height: 16px;
                border: 1px solid #555555;
                border-radius: 3px;
                background: #1a1a1c;
            }}
            #autostartCheck::indicator:checked {{
                background: #4ade80;
                border-color: #4ade80;
            }}
        """)
        for w in self.findChildren(QLabel):
            if w.objectName() == "sectionTitle":
                w.setStyleSheet(f"font-size: 13px; font-family: {font_stack}; color: #aaaaaa;")

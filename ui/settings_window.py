import os
from pathlib import Path
from PySide6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QComboBox, QLineEdit, QStackedWidget,
    QFrame, QApplication,
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont, QFontDatabase
from commands import handler as cmd

ENV_PATH = Path(__file__).resolve().parent.parent / '.env'


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


PREFERRED_FONTS = [
    "Fira Code",
    "Cascadia Code",
    "JetBrains Mono",
    "IBM Plex Mono",
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
        self.setFixedSize(580, 380)

        self._build_ui()
        self._apply_styles()
        self._load_state()
        self.font_combo.currentTextChanged.connect(self._on_font_changed)
        self.active_combo.currentIndexChanged.connect(self._on_active_backend_changed)

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

        layout.addStretch()
        return page

    # ── api page ─────────────────────────────────────────────

    def _build_api_page(self) -> QWidget:
        page = QWidget()
        page.setObjectName("settingsPage")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(12)

        # active backend
        active_label = QLabel("Primary Backend")
        active_label.setObjectName("sectionTitle")
        layout.addWidget(active_label)

        self.active_combo = QComboBox()
        self.active_combo.setObjectName("activeBackendCombo")
        self.active_combo.addItem("Auto (first available)", "auto")
        for key, info in cmd.BACKENDS.items():
            self.active_combo.addItem(info["label"], key)
        layout.addWidget(self.active_combo)

        # separator
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("background: #2a2a2a; max-height: 1px;")
        layout.addWidget(sep)

        # keys
        keys_label = QLabel("API Keys")
        keys_label.setObjectName("sectionTitle")
        layout.addWidget(keys_label)

        self._key_widgets = {}
        for key, info in cmd.BACKENDS.items():
            row = self._key_row(key, info)
            self._key_widgets[key] = row
            layout.addWidget(row["widget"])

        layout.addStretch()
        return page

    def _key_row(self, backend_key: str, info: dict) -> dict:
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        dot = QLabel("●")
        dot.setObjectName("statusDot")
        dot.setFixedWidth(16)

        name = QLabel(info["label"])
        name.setObjectName("keyName")
        name.setFixedWidth(80)

        inp = QLineEdit()
        inp.setObjectName("keyInput")
        inp.setPlaceholderText("Paste your API key...")
        inp.setEchoMode(QLineEdit.Password)

        save_btn = QPushButton("Save")
        save_btn.setObjectName("keySaveBtn")
        save_btn.setCursor(Qt.PointingHandCursor)

        remove_btn = QPushButton("Remove")
        remove_btn.setObjectName("keyRemoveBtn")
        remove_btn.setCursor(Qt.PointingHandCursor)

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
        f.setStyleStrategy(QFont.PreferAntialias)
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
        f.setStyleStrategy(QFont.PreferAntialias)
        self._app.setFont(f)
        if self._launcher:
            self._launcher.update_font(font_name)
        # re-apply own stylesheet so settings window uses the new font too
        self._apply_styles(font_name)

    def _on_active_backend_changed(self, idx: int):
        backend = self.active_combo.currentData()
        env = _read_env()
        if backend == "auto":
            env.pop("ACTIVE_BACKEND", None)
            os.environ.pop("ACTIVE_BACKEND", None)
        else:
            env["ACTIVE_BACKEND"] = backend
            os.environ["ACTIVE_BACKEND"] = backend
        _write_env(env)

    # ── load ─────────────────────────────────────────────────

    def _load_state(self):
        # block signals so setCurrentIndex doesn't trigger _on_font_changed
        self.font_combo.blockSignals(True)
        self.active_combo.blockSignals(True)

        env = _read_env()
        loaded = env.get("APP_FONT") or "Fira Code"
        idx = self.font_combo.findText(loaded)
        if idx >= 0:
            self.font_combo.setCurrentIndex(idx)

        active = env.get("ACTIVE_BACKEND", "auto")
        idx = self.active_combo.findData(active)
        if idx >= 0:
            self.active_combo.setCurrentIndex(idx)

        self.font_combo.blockSignals(False)
        self.active_combo.blockSignals(False)

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
            .sectionTitle {{
                font-size: 13px; font-family: {font_stack};
                color: #aaaaaa;
            }}
            #fontCombo, #activeBackendCombo {{
                background: #1a1a1c;
                border: 1px solid #333333;
                border-radius: 2px;
                padding: 6px 8px;
                font-size: 13px; font-family: {font_stack};
                color: #e0e0e0;
                selection-background-color: #404040;
            }}
            #fontCombo:focus, #activeBackendCombo:focus {{
                border: 1px solid #ffffff;
            }}
            #fontCombo::drop-down, #activeBackendCombo::drop-down {{
                border: none;
                width: 20px;
            }}
            #fontCombo QAbstractItemView, #activeBackendCombo QAbstractItemView {{
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
                padding: 5px 8px;
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
                padding: 5px 14px;
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
                padding: 5px 14px;
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
        """)
        for w in self.findChildren(QLabel):
            if w.objectName() == "sectionTitle":
                w.setStyleSheet(f"font-size: 13px; font-family: {font_stack}; color: #aaaaaa;")

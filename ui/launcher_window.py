from PySide6.QtWidgets import (
    QWidget, QLineEdit, QTextEdit, QVBoxLayout, QHBoxLayout,
    QApplication, QFrame, QGraphicsDropShadowEffect,
)
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QThreadPool
from PySide6.QtGui import QKeyEvent, QFont
from config import settings
from ai.worker import AIWorker
from ai.catalog import any_key_configured


INNER_MARGIN = 10


class LauncherWindow(QWidget):
    """Ventana principal del launcher.

    Frameless, always-on-top, con sombra y fade animado.
    """
    def __init__(self, app=None):
        super().__init__()
        self._app = app
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setFixedSize(settings.WINDOW_WIDTH, settings.WINDOW_HEIGHT)

        self.threadpool = QThreadPool.globalInstance()
        self._waiting = False
        self._fade_anim = None
        self._history: list[dict] = []

        self._build_ui()
        self._apply_styles()
        self._apply_shadow()

    def _build_ui(self):
        self.container = QFrame()
        self.container.setObjectName("container")

        self.input = QLineEdit()
        self.input.setPlaceholderText("Pregunta...")
        self.input.returnPressed.connect(self._on_enter)

        self.response = QTextEdit()
        self.response.setReadOnly(True)
        self.response.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.response.setObjectName("response")

        inner = QVBoxLayout(self.container)
        inner.setContentsMargins(INNER_MARGIN, INNER_MARGIN, INNER_MARGIN, INNER_MARGIN)
        inner.setSpacing(0)
        inner.addWidget(self.input)
        inner.addWidget(self.response)

        outer = QHBoxLayout(self)
        outer.setContentsMargins(12, 12, 12, 12)
        outer.addWidget(self.container)

    def _apply_styles(self):
        self.setStyleSheet("""
            #container {
                background: #161618;
                border-radius: 4px;
            }
            QLineEdit {
                background: #1a1a1c;
                border: 1px solid #555555;
                border-radius: 2px;
                padding: 8px 12px;
                font-size: 13px;
                line-height: 16px;
                color: #e0e0e0;
                selection-background-color: #404040;
                outline: none;
            }
            QLineEdit:focus {
                border: 1px solid #ffffff;
            }
            QLineEdit:disabled {
                color: #555555;
            }
            QLineEdit::placeholder {
                color: #555555;
            }
            #response {
                background: #161618;
                border: none;
                border-top: 1px solid #2a2a2a;
                padding: 8px 10px;
                font-size: 13px;
                line-height: 16px;
                color: #c0c0c8;
                selection-background-color: #404040;
            }
        """)

    def update_font(self, font_name: str):
        f = QFont(font_name, 13)
        f.setHintingPreference(QFont.PreferFullHinting)
        self.input.setFont(f)
        f2 = QFont(font_name, 13)
        f2.setHintingPreference(QFont.PreferFullHinting)
        self.response.setFont(f2)
        self.input.setFocus()

    def _apply_shadow(self):
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(30)
        shadow.setColor(Qt.black)
        shadow.setOffset(0, 3)
        self.container.setGraphicsEffect(shadow)



    def _fade_to(self, target_opacity: float, duration: int, on_finished=None):
        if self._fade_anim:
            self._fade_anim.stop()
        self._fade_anim = QPropertyAnimation(self, b"windowOpacity")
        self._fade_anim.setStartValue(self.windowOpacity())
        self._fade_anim.setEndValue(target_opacity)
        self._fade_anim.setDuration(duration)
        self._fade_anim.setEasingCurve(QEasingCurve.OutCubic)
        if on_finished:
            self._fade_anim.finished.connect(on_finished)
        self._fade_anim.start()

    def show_centered(self):
        screen = QApplication.primaryScreen()
        g = screen.availableGeometry()
        x = g.x() + (g.width() - self.width()) // 2
        y = g.y() + (g.height() - self.height()) // 2
        self.move(x, y)
        self.setWindowOpacity(0.0)
        self.show()
        self.raise_()
        self.activateWindow()
        self.input.setFocus()
        self._fade_to(1.0, 150)

    def hide_and_clear(self):
        self._fade_to(0.0, 100, on_finished=self._really_hide)

    def _really_hide(self):
        self.input.clear()
        self.response.clear()
        self._history.clear()
        self.hide()
        self.setWindowOpacity(1.0)

    def toggle_visibility(self):
        if self.isVisible():
            self.hide_and_clear()
        else:
            self.show_centered()

    def _on_enter(self):
        if self._waiting:
            return
        text = self.input.text().strip()
        if not text:
            return
        self.input.clear()

        if not any_key_configured():
            self.response.setPlainText(
                "No hay claves de API configuradas.\n"
                "Abre Settings → Añade una clave de API en la sección API."
            )
            QTimer.singleShot(0, self.input.setFocus)
            return

        self._set_waiting(True)
        self.response.setPlainText("...")

        self._history.append({"role": "user", "content": text})
        worker = AIWorker(text, list(self._history))
        worker.signals.finished.connect(self._on_answer)
        worker.signals.error.connect(self._on_error)
        self.threadpool.start(worker)

    def _on_answer(self, text: str):
        self._set_waiting(False)
        self._history.append({"role": "assistant", "content": text})
        self.response.setPlainText(text)
        QTimer.singleShot(0, self.input.setFocus)

    def _on_error(self, msg: str):
        self._set_waiting(False)
        self.response.setPlainText(f"Error: {msg}")
        QTimer.singleShot(0, self.input.setFocus)

    def _set_waiting(self, v: bool):
        self._waiting = v
        self.input.setDisabled(v)

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key_Escape:
            self.hide_and_clear()
        else:
            super().keyPressEvent(event)

    def focusOutEvent(self, event):
        QTimer.singleShot(100, self._hide_if_necessary)
        super().focusOutEvent(event)

    def _hide_if_necessary(self):
        if not self.isActiveWindow() and not self.container.hasFocus():
            self.hide_and_clear()

import os
import sys
import signal
from pathlib import Path
from PySide6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PySide6.QtGui import QIcon, QPixmap, QPainter, QFont, QColor, QPen, QBrush, QPainterPath, QFontDatabase
from config import settings
from hotkeys.listener import HotkeyListener
from ui.launcher_window import LauncherWindow


APP_NAME = "Flotante"


def _load_env():
    env_path = Path(__file__).parent / '.env'
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        key, _, value = line.partition('=')
        key = key.strip()
        value = value.strip()
        if key not in os.environ:
            os.environ[key] = value


def _make_icon() -> QIcon:
    """Genera un icono simple pintado con QPainter."""
    size = 64
    pix = QPixmap(size, size)
    pix.fill(QColor(0, 0, 0, 0))

    p = QPainter(pix)
    p.setRenderHint(QPainter.Antialiasing)

    # Fondo redondeado
    path = QPainterPath()
    path.addRoundedRect(4, 4, size - 8, size - 8, 8, 8)
    p.fillPath(path, QColor("#1e1e1e"))
    p.setPen(QPen(QColor("#333333"), 1.5))
    p.drawPath(path)

    # Texto ">_"
    p.setPen(QColor("#ffffff"))
    font = QFont("Fira Code", 28, QFont.Bold)
    p.setFont(font)
    p.drawText(8, 12, size - 16, size - 16, 0, ">_")

    p.end()
    return QIcon(pix)


def _load_local_fonts():
    fonts_dir = Path(__file__).parent / "assets" / "fonts"
    for path in fonts_dir.glob("*.ttf"):
        QFontDatabase.addApplicationFont(str(path))


def main():
    _load_env()
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    app = QApplication(sys.argv)
    _load_local_fonts()
    app.setFont(QFont("Fira Code", 10))
    app.setQuitOnLastWindowClosed(False)

    icon = _make_icon()
    window = LauncherWindow(app)
    window.setWindowIcon(icon)

    # System tray
    tray = QSystemTrayIcon(icon, app)
    tray.setToolTip(APP_NAME)

    menu = QMenu()
    menu.setStyleSheet("""
        QMenu {
            background: #1c1c1c;
            border: 1px solid #2a2a2a;
            border-radius: 6px;
            padding: 4px;
        }
        QMenu::item {
            padding: 6px 24px 6px 12px;
            font: 13px "Segoe UI", "Segoe UI Variable Display", sans-serif;
            color: #cccccc;
            border-radius: 4px;
        }
        QMenu::item:selected {
            background: #2a2a2a;
            color: #ffffff;
        }
        QMenu::separator {
            height: 1px;
            background: #2a2a2a;
            margin: 4px 8px;
        }
    """)

    abrir = menu.addAction("Abrir")
    menu.addSeparator()
    salir = menu.addAction("Salir")

    abrir.triggered.connect(window.show_centered)
    salir.triggered.connect(app.quit)
    tray.setContextMenu(menu)
    tray.activated.connect(
        lambda reason: window.show_centered() if reason == QSystemTrayIcon.DoubleClick else None
    )

    tray.show()

    # Hotkey
    hotkey = HotkeyListener(settings.HOTKEY)
    hotkey.activated.connect(window.toggle_visibility)
    hotkey.start()

    sys.exit(app.exec())


if __name__ == '__main__':
    main()

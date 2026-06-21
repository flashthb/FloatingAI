import threading
from pynput import keyboard
from PySide6.QtCore import QObject, Signal


class HotkeyListener(QObject):
    """Listener de atajo global usando pynput.

    Emite la señal `activated` cuando se pulsa la combinación configurada.
    """

    activated = Signal()

    def __init__(self, hotkey_string: str = '<ctrl>+space'):
        super().__init__()
        self.hotkey_string = hotkey_string
        self._listener = None
        self._thread = None

    def _on_activate(self):
        # Método llamado desde el hilo de pynput; emitimos señal Qt (thread-safe, queued)
        self.activated.emit()

    def start(self):
        """Arranca el listener en un hilo separado.

        Usamos GlobalHotKeys con start() para que maneje su propio hilo.
        """
        # Parse simple: pynput acepta combinaciones en formato '<ctrl>+space'
        mapping = {self.hotkey_string: self._on_activate}
        self._listener = keyboard.GlobalHotKeys(mapping)
        # start() crea internamente un hilo que ejecuta el listener
        self._listener.start()

    def stop(self):
        if self._listener:
            self._listener.stop()

from PySide6.QtCore import QObject, Signal, QRunnable
from .client import get_short_answer


class WorkerSignals(QObject):
    finished = Signal(str)
    error = Signal(str)


class AIWorker(QRunnable):
    """QRunnable que ejecuta la consulta a la IA en un hilo del pool.

    Emite `finished` con la respuesta o `error` con el texto del error.
    """

    def __init__(self, prompt: str, history: list[dict] | None = None):
        super().__init__()
        self.prompt = prompt
        self.history = history or []
        self.signals = WorkerSignals()

    def run(self):
        try:
            answer = get_short_answer(self.prompt, history=self.history)
            self.signals.finished.emit(answer)
        except Exception as e:
            self.signals.error.emit(str(e))

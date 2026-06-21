from PySide6.QtCore import QObject, Signal, QRunnable
from .client import get_short_answer


class WorkerSignals(QObject):
    finished = Signal(str)
    error = Signal(str)


class AIWorker(QRunnable):
    """QRunnable que ejecuta la consulta a la IA en un hilo del pool.

    Emite `finished` con la respuesta o `error` con el texto del error.
    """

    def __init__(self, prompt: str):
        super().__init__()
        self.prompt = prompt
        self.signals = WorkerSignals()

    def run(self):
        try:
            answer = get_short_answer(self.prompt)
            self.signals.finished.emit(answer)
        except Exception as e:
            self.signals.error.emit(str(e))

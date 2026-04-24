from PyQt6.QtCore import QObject, pyqtSignal


class WorkerHandler(QObject):
    """
    Gestisce il ciclo di vita dei QThread worker e lo stato di occupato della UI.

    Espone due modalità di uso:
      - start_worker(worker): per i QThread standard (Notion, Gemini, ecc.)
      - begin_external() / end_external(): per operazioni non-QThread
        come il processo Whisper multiprocessing.

    Il contatore interno garantisce che busy=False venga emesso solo quando
    TUTTE le operazioni parallele sono concluse, non alla prima che finisce.
    """

    busy_changed = pyqtSignal(bool)   # True quando almeno un'operazione è in corso
    operation_finished = pyqtSignal() # emesso quando il contatore torna a zero
    operation_error = pyqtSignal(str) # emesso da qualsiasi worker che fallisce
    log = pyqtSignal(str)             # forward del segnale log dai worker

    def __init__(self, parent=None):
        super().__init__(parent)
        self._active_workers: set = set()
        self._pending: int = 0

    # ── API pubblica ────────────────────────────────────────────────────────

    def start_worker(self, worker):
        """
        Avvia un QThread e lo traccia.
        Il worker deve avere i segnali `finished` ed `error`.
        Se ha il segnale `log`, viene automaticamente inoltrato.
        """
        self._active_workers.add(worker)
        self._increment()
        worker.finished.connect(lambda w=worker: self._on_finished(w))
        worker.error.connect(lambda msg, w=worker: self._on_error(w, msg))
        if hasattr(worker, "log"):
            worker.log.connect(self.log)
        worker.start()
        return worker

    def begin_external(self) -> None:
        """
        Riserva uno slot di occupato per un'operazione non gestita da QThread
        (es. processo Whisper). Va accoppiato con end_external().
        """
        self._increment()

    def end_external(self) -> None:
        """Rilascia lo slot riservato con begin_external()."""
        self._decrement()

    @property
    def is_busy(self) -> bool:
        return self._pending > 0

    # ── Interni ─────────────────────────────────────────────────────────────

    def _increment(self) -> None:
        self._pending += 1
        if self._pending == 1:
            self.busy_changed.emit(True)

    def _decrement(self) -> None:
        self._pending = max(0, self._pending - 1)
        if self._pending == 0:
            self.busy_changed.emit(False)
            self.operation_finished.emit()

    def _on_finished(self, worker) -> None:
        self._active_workers.discard(worker)
        self._decrement()

    def _on_error(self, worker, error_msg: str) -> None:
        self._active_workers.discard(worker)
        self.operation_error.emit(error_msg)
        self._decrement()
import multiprocessing
from pathlib import Path

from PyQt6.QtCore import QObject, pyqtSignal, QTimer

from src.GUI.Transcribe.whisperProcess import whisper_lazy_engine


class WhisperHandler(QObject):
    """
    Incapsula il processo multiprocessing di Whisper e la coda di risultati.

    Il processo viene avviato in modo lazy: solo al primo send_task(), non
    nell'__init__. Questo evita di consumare risorse se l'utente non trascrive mai.

    Emette:
      - log(str):                     messaggi di avanzamento
      - transcription_done(list):     lista di Path ai file .txt prodotti
      - error(str):                   errore fatale dal processo
    """

    log = pyqtSignal(str)
    transcription_done = pyqtSignal(list)  # list[Path]
    error = pyqtSignal(str)

    _POLL_INTERVAL_MS = 200

    def __init__(self, parent=None):
        super().__init__(parent)
        self._task_queue: multiprocessing.Queue | None = None
        self._result_queue: multiprocessing.Queue | None = None
        self._process: multiprocessing.Process | None = None
        self._current_audio: list[Path] = []

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._poll)

    # ── API pubblica ────────────────────────────────────────────────────────

    def send_task(self, audio_paths: list[Path]) -> None:
        """Invia un batch di file audio per la trascrizione."""
        self._current_audio = list(audio_paths)
        self._ensure_running()
        self._task_queue.put({"paths": self._current_audio})

    def stop(self) -> None:
        """Chiusura pulita. Da chiamare nel closeEvent della finestra padre."""
        self._timer.stop()
        if self._process and self._process.is_alive():
            self._process.terminate()
            self._process.join(timeout=2)
        self._process = None
        self._task_queue = None
        self._result_queue = None

    # ── Interni ─────────────────────────────────────────────────────────────

    def _ensure_running(self) -> None:
        """Avvia il processo solo se non è già attivo."""
        if self._process is not None and self._process.is_alive():
            return

        self._task_queue = multiprocessing.Queue()
        self._result_queue = multiprocessing.Queue()
        self._process = multiprocessing.Process(
            target=whisper_lazy_engine,
            args=(self._task_queue, self._result_queue),
            daemon=True,
        )
        self._process.start()
        self._timer.start(self._POLL_INTERVAL_MS)

    def _poll(self) -> None:
        """Controlla la coda dei risultati ad ogni tick del timer."""
        if self._result_queue is None:
            return
        while not self._result_queue.empty():
            try:
                msg = self._result_queue.get_nowait()
            except Exception:
                break

            match msg.get("type"):
                case "log":
                    self.log.emit(msg["content"])
                case "all_done":
                    self.log.emit("Trascrizione completata.")
                    txt_paths = [p.with_suffix(".txt") for p in self._current_audio]
                    self.transcription_done.emit(txt_paths)
                    self._current_audio = []
                case "error":
                    self.error.emit(msg["content"])
from PyQt6.QtCore import QThread,pyqtSignal
from faster_whisper import WhisperModel
import multiprocessing
from faster_whisper import WhisperModel
from pathlib import Path
from src.GUI.Transcribe.whisperProcess import whisper_lazy_engine

class TranscribeModelLoaderWorker (QThread):
    finished = pyqtSignal()
    error = pyqtSignal(str)
    log = pyqtSignal(str)
    progress = pyqtSignal(str)

    def __init__(self, audio_paths):
        super().__init__()
        self.audio_paths = audio_paths
        self.queue = multiprocessing.Queue()
        self.process = None

    def run(self):
        # Avvia il processo multiprocessing
        self.process = multiprocessing.Process(
            target=whisper_lazy_engine, 
            args=(self.audio_paths, self.queue)
        )
        self.process.start()

        # Ciclo di ascolto della coda
        while True:
            msg = self.queue.get() # Aspetta un messaggio dal processo
            
            if msg["type"] == "log":
                self.log.emit(msg["content"])
            elif msg["type"] == "progress":
                self.progress.emit(msg["file"])
            elif msg["type"] == "error":
                self.error.emit(msg["content"])
                break
            elif msg["type"] == "finished":
                self.finished.emit()
                break
        
        self.process.join() # Chiude il processo pulitamente




        

from PyQt6.QtCore import QThread, pyqtSignal
from src.GUI.Gen.GeminiRequestManager import GeminiRequestManager
from pathlib import Path

class GeminiSyncWorker(QThread):
    finished = pyqtSignal()      
    error = pyqtSignal(str)      
    log = pyqtSignal(str)        
    progress = pyqtSignal(int, int)

    def __init__(self, prompt: str, paths: list, pdf: bool = True, json_mode: bool = True, is_map: bool = False):
        super().__init__()
        self.prompt = prompt
        self.pdf_paths = paths
        self.pdf = pdf
        self.json_mode = json_mode
        self.is_map = is_map
        self.request_manager = GeminiRequestManager()

    def run(self):
        try:
            self.log.emit(f"Inizio generazione per {len(self.pdf_paths)} file...")
            
            totali = len(self.pdf_paths)
            completati = 0
            
            def on_file_processed(path, json_mode, is_map, response, error):
                nonlocal completati
                nome_file = Path(path).name
                
                if error:
                    self.log.emit(f"Errore per {nome_file}: {error}")
                else:
                    self.log.emit(f"Salvato con successo: {nome_file}")
                
                completati += 1
                self.progress.emit(completati, totali)
            
            # Elabora file in parallelo
            self.request_manager.process_files_parallel(
                self.pdf_paths,
                self.prompt,
                self.pdf,
                self.json_mode,
                self.is_map,
                callback=on_file_processed
            )
            
            self.log.emit("Creazione terminata!")
            self.finished.emit()
            
        except Exception as e:
            self.error.emit(str(e))
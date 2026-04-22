from PyQt6.QtCore import QThread, pyqtSignal
from src.GUI.Notion.NotionLoader import NotionLoader # Assicurati che l'import sia corretto
from pathlib import Path
class NotionSyncLoader(QThread):
    # Segnali per comunicare con la GUI
    finished = pyqtSignal()      # Dice "Ho finito!"
    error = pyqtSignal(str)      # Dice "C'è stato un errore: ..."
    log = pyqtSignal(str)        # Manda messaggi di testo alla console della GUI
    def __init__(self,answer_paths:list[Path]):
            super().__init__()
            self.answer_paths = answer_paths
    def run(self):
        try:
            loader = NotionLoader()
            totali = len(self.answer_paths)
            
            # Il ciclo for lo facciamo QUI dentro al thread!
            for index, path in enumerate(self.answer_paths, start=1):
                self.log.emit(f"[{index}/{totali}] Sincronizzazione di: {path.name}...")
                
                success = loader.load(path)
                
                if success:
                    self.log.emit(f"{path.name} caricato con successo!")
                else:
                    self.log.emit(f"{path.name} ignorato o fallito (vedi log).")
            
            self.log.emit("Tutti i caricamenti terminati!")
            self.finished.emit()
            
        except Exception as e:
            self.error.emit(str(e))
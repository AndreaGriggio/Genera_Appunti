from PyQt6.QtCore import QThread, pyqtSignal
from src.GUI.DeleteWorker import DeleteWorker
class DeleteSyncWorker(QThread):
    finished = pyqtSignal()      
    error = pyqtSignal(str)      
    log = pyqtSignal(str)        

    def __init__(self):
        super().__init__()


    def run(self):
        try:
            self.log.emit(f"Inizio pulizia")
            
            deleter = DeleteWorker()
            
            deleter.delete()
            
            self.log.emit("Pulizia completata")
            self.finished.emit()
            
        except Exception as e:
            self.error.emit(str(e))
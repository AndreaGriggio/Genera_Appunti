from PyQt6.QtCore import QThread, pyqtSignal
from src.GUI.NotionBrancher import NotionBrancher # Assicurati che l'import sia corretto
from src.GUI.FolderUpdater import FolderUpdater
from src.GUI.config import BASE_ID
class NotionSyncWorker(QThread):
    # Segnali per comunicare con la GUI
    finished = pyqtSignal()      # Dice "Ho finito!"
    error = pyqtSignal(str)      # Dice "C'è stato un errore: ..."
    log = pyqtSignal(str)        # Manda messaggi di testo alla console della GUI

    def run(self):
        """
        Questo è il codice che gira in parallelo.
        NON toccare mai elementi della GUI (bottoni, finestre) qui dentro direttamente.
        Usa i segnali.
        """
        try:
            self.log.emit("Inizio sincronizzazione con Notion...")
            
            # Istanzia la tua classe logica
            brancher = NotionBrancher()
            
            # Lancia il processo pesante
            brancher.get_notion_branching()
            updater = FolderUpdater()
            updater.update()
            
            self.log.emit("Aggiornamento completato!")
            self.finished.emit()
            
        except Exception as e:
            # Se esplode qualcosa, avvisa la GUI
            self.error.emit(str(e))
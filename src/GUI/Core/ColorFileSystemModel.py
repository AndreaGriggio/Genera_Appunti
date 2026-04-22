import json
from typing import Any
from pathlib import Path
from PyQt6.QtGui import QFileSystemModel, QColor
from PyQt6.QtCore import Qt, QModelIndex
from src.GUI.config import DATAPATH

class ColorFileSystemModel(QFileSystemModel):
    def __init__(self):
        super().__init__()
        self.loaded_history = set()
        self.created_history = set()
        self.refresh_histories()

    def refresh_histories(self):
        """Legge i JSON e aggiorna i set di dati in memoria."""
        path_loaded = Path(DATAPATH) / "history_loaded.json" # o history_notion.json, usa il tuo nome
        path_created = Path(DATAPATH) / "history_pdf.json"

        # Carica storia Notion (File completati)
        try:
            with open(path_loaded, "r", encoding="utf-8") as f:
                h_loaded = json.load(f)
                # Adatta il .replace se usi suffissi come discusso prima
                self.loaded_history = {Path(name).stem.replace("_appunti", "") for name in h_loaded}
        except (json.JSONDecodeError, FileNotFoundError):
            self.loaded_history = set()

        # Carica storia Gemini (Appunti generati ma magari non ancora su Notion)
        try:
            with open(path_created, "r", encoding="utf-8") as f:
                h_created = json.load(f)
                self.created_history = {Path(name).stem for name in h_created}
        except (json.JSONDecodeError, FileNotFoundError):
            self.created_history = set()
            
        # Forza l'aggiornamento visivo dell'albero
        self.layoutChanged.emit()

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        """Decide cosa mostrare per ogni cella, inclusi i colori."""
        # Intercettiamo il colore del testo (ForegroundRole)
        if role == Qt.ItemDataRole.ForegroundRole:
            if not self.isDir(index): # Coloriamo solo i file, non le cartelle
                file_name = self.fileName(index)
                stem = Path(file_name).stem
                
                # Logica dei colori:
                if stem in self.loaded_history:
                    return QColor("#2E8B57") # Verde (SeaGreen) - Finito su Notion
                elif stem in self.created_history:
                    return QColor("#DAA520") # Arancione (Goldenrod) - Passato da Gemini
                    
        # Per tutto il resto, usa il comportamento standard
        return super().data(index, role)
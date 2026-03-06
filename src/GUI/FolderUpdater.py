from pathlib import Path
import json
import os
# Assicurati che l'import di DATAPATH sia corretto nel tuo progetto
from src.GUI.config import DATAPATH 

class FolderUpdater:
    def __init__(self):
        # Il file JSON si trova dentro DATAPATH
        self.json_path = Path(DATAPATH) / "dict_notion.json"

    def update(self):
        """Avvia l'aggiornamento delle cartelle."""
        print(f"Leggo la struttura da: {self.json_path}")
        datas = self.open_dict()
        
        if datas is not None:
            # Avvio la ricorsione partendo dalla cartella radice (DATAPATH)
            # datas è il nodo radice del JSON
            self.recursive_exploration(datas, Path(DATAPATH))
            print("\n✅ Aggiornamento cartelle completato.")
        else:
            print("❌ Errore: dict_notion.json non trovato o vuoto.")

    def recursive_exploration(self, nodo, parent_path):
        """
        Esplora ricorsivamente l'albero.
        1. Crea la cartella per il nodo corrente.
        2. Scrive il file .id.
        3. Scende nei figli.
        """
        # 1. Pulisci il nome (es. "Analisi 1/2" -> "Analisi 1-2")
        # I caratteri : e / sono vietati nei nomi di cartelle su Windows/Linux
        nome_pulito = nodo["titolo"].replace("/", "-").replace(":", " ").strip()
        
        # 2. Definisci il percorso di QUESTA cartella
        current_path = parent_path / nome_pulito
        
        # 3. Crea cartella e file ID (passiamo l'ID del nodo corrente)
        self.makedir(current_path, nodo["id"])
        
        # 4. Ricorsione: Se ha figli, esplorali passando current_path come genitore
        for child in nodo.get("children", []):
            self.recursive_exploration(child, current_path)

    def open_dict(self):
        if self.json_path.exists():
            with open(self.json_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return None

    def makedir(self, path: Path, notion_id: str):
        """
        Crea la cartella se non esiste e scrive/sovrascrive il file .id
        """
        # 1. Crea la directory fisica
        if not path.exists():
            try:
                path.mkdir(parents=True, exist_ok=True)
                print(f"📁 Creata cartella: {path.name}")
            except Exception as e:
                print(f"❌ Errore creazione {path}: {e}")
                return

        # 2. Crea il file nascosto con l'ID
        file_id_path = path / ".id"
        
        # Opzionale: scriviamo solo se l'ID è diverso o il file non esiste
        # ma per sicurezza sovrascriviamo sempre, è veloce.
        try:
            with open(file_id_path, "w", encoding="utf-8") as f:
                f.write(notion_id)
        except Exception as e:
            print(f"⚠️ Errore scrittura .id in {path.name}: {e}")

if __name__ == "__main__":
    updater = FolderUpdater()
    updater.update()
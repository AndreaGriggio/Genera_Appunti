from pathlib import Path
import json
import os
import shutil
# Assicurati che l'import di DATAPATH sia corretto nel tuo progetto
from src.GUI.config import DATAPATH 

class FolderUpdater:
    def __init__(self):
        # Il file JSON si trova dentro DATAPATH
        self.json_path = Path(DATAPATH) / "dict_notion.json"
        self.root_path = Path(DATAPATH)

    def update(self):
        print(f"Leggo la struttura da: {self.json_path}")
        datas = self.open_dict()
 
        if datas is None:
            print("❌ Errore: dict_notion.json non trovato o vuoto.")
            return
 
        # 1. Costruisce l'insieme dei percorsi validi secondo Notion
        valid_paths: set[Path] = set()
        self._collect_valid_paths(datas, self.root_path, valid_paths)
 
        # 2. Crea le cartelle mancanti e scrive i file .id
        self._recursive_exploration(datas, self.root_path)
 
        # 3. Cancella le cartelle locali che non esistono più in Notion
        self._remove_obsolete(valid_paths)
 
        print("\nAggiornamento cartelle completato.")

    def _collect_valid_paths(self, nodo: dict, parent_path: Path, valid: set[Path]):
        """
        Visita l'albero Notion e aggiunge a 'valid' tutti i percorsi
        che dovrebbero esistere su disco.
        """
        nome_pulito = self._clean_name(nodo["titolo"])
        current_path = parent_path / nome_pulito
        valid.add(current_path)
 
        for child in nodo.get("children", []):
            self._collect_valid_paths(child, current_path, valid)
    def _clean_name(self, titolo: str) -> str:
        """Pulisce il nome della cartella dai caratteri non validi su Windows."""
        return titolo.replace("/", "-").replace(":", " ").strip()
 
    def _makedir(self, path: Path, notion_id: str):
        if not path.exists():
            try:
                path.mkdir(parents=True, exist_ok=True)
                print(f"📁 Creata cartella: {path.name}")
            except Exception as e:
                print(f"Errore creazione {path}: {e}")
                return
 
        try:
            with open(path / ".id", "w", encoding="utf-8") as f:
                f.write(notion_id)
        except Exception as e:
            print(f"Errore scrittura .id in {path.name}: {e}")

    def open_dict(self):
        if self.json_path.exists():
            with open(self.json_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return None


    def _remove_obsolete(self, valid_paths: set[Path]):
        """
        Scansiona le sottocartelle dirette di DATAPATH.
        Cancella quelle (e tutto il loro contenuto) che non compaiono
        nell'insieme dei percorsi validi.
 
        Nota: controlla solo le cartelle, non i file nella root
        (history_pdf.json, dict_notion.json, ecc. devono restare).
        """
        for item in self.root_path.iterdir():
            if not item.is_dir():
                continue  # i file nella root non si toccano
 
            if item not in valid_paths:
                try:
                    shutil.rmtree(item)
                    print(f"Cartella rimossa (non più in Notion): {item.name}")
                except Exception as e:
                    print(f"Errore rimozione {item.name}: {e}")
            else:
                # Controlla ricorsivamente anche le sottocartelle
                self._remove_obsolete_recursive(item, valid_paths)
 
    def _remove_obsolete_recursive(self, current_dir: Path, valid_paths: set[Path]):
        """Rimuove ricorsivamente le sottocartelle non più in Notion."""
        for item in current_dir.iterdir():
            if not item.is_dir():
                continue
 
            if item not in valid_paths:
                try:
                    shutil.rmtree(item)
                    print(f"Sottocartella rimossa: {item.name}")
                except Exception as e:
                    print(f"Errore rimozione {item.name}: {e}")
            else:
                self._remove_obsolete_recursive(item, valid_paths)

    def _recursive_exploration(self, nodo: dict, parent_path: Path):
        nome_pulito = self._clean_name(nodo["titolo"])
        current_path = parent_path / nome_pulito
        self._makedir(current_path, nodo["id"])
 
        for child in nodo.get("children", []):
            self._recursive_exploration(child, current_path)
if __name__ == "__main__":
    updater = FolderUpdater()
    updater.update()
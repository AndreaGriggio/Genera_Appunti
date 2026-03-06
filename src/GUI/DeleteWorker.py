import os
from pathlib import Path
from src.GUI.config import DATAPATH
import json
class DeleteWorker:
    def __init__ (self):
        self.history_loaded_path = Path(DATAPATH)/"history_loaded.json"
        self.history_created_path = Path(DATAPATH )/ "history_pdf.json"
    def delete(self):

        #prendo tutti i nomi dei pdf 
        pdf_mapping =  {pdf.stem : pdf for pdf in self.get_pdfs()}

        h1,h2 = self.get_histories()

        history_set = set(h1) & set(h2)#end logica tra le due liste di nomi
        #Trovo unicamente i file che sono presenti in entrambe
        must_remove = []

        for name in pdf_mapping :#per tutti file pdf presenti
            if name in history_set:#guardo se sono già stati processati e caricati
                must_remove.append(name)

        for name in must_remove:
            pdf_path = pdf_mapping[name]
            json_path = pdf_mapping[name].with_suffix(".json")
            try:
                pdf_path.unlink()
                json_path.unlink()
                print(f"{name} eliminato")
            except Exception as e:
                print(f"Errore durante l'eliminazione di {name} : {e}")
        
        
        self.update_history(must_remove,h1,h2)

    def get_pdfs(self,root_path: str = DATAPATH) -> list[Path]:
        """
        Scansiona ricorsivamente tutte le sottocartelle di root_path 
        e restituisce una lista di oggetti Path relativi ai file .pdf.
        """
        path_root = Path(root_path)
        
        # rglob("* .pdf") cerca ricorsivamente tutti i file che terminano in .pdf
        # usiamo una list comprehension per filtrare eventuali file temporanei o nascosti
        pdf_files = [
            file for file in path_root.rglob("*.pdf") 
            if file.is_file() and not file.name.startswith("._")
        ]
        print(pdf_files)
        
        return pdf_files
    def get_histories(self)->tuple[list[str],list[str]]:

        try :
            with open(self.history_created_path, "r", encoding="utf-8") as f:
                h1 = json.load(f)
            with open(self.history_loaded_path, "r", encoding="utf-8") as f:
                h2 = json.load(f)
                
            # 1. Creiamo un set con TUTTI i nomi senza estensione dei PDF fisici
            # Questo rende la ricerca istantanea ed evita i problemi con i percorsi completi
            pdf_fisici_stems = {pdf.stem for pdf in self.get_pdfs()}
            
            # 2. Puliamo h1: prendiamo solo il nome senza estensione (Path(nome).stem)
            # e lo teniamo SOLO se esiste fisicamente tra i pdf
            h1_pulito = [Path(nome).stem for nome in h1 if Path(nome).stem in pdf_fisici_stems]
            
            # 3. Puliamo h2 per avere solo i nomi senza estensione
            h2_pulito = [Path(nome).stem for nome in h2]
            
            print("h1 : ", h1_pulito)
            print("h2 : ", h2_pulito)
            
            return h1_pulito, h2_pulito
            
        except (json.JSONDecodeError, FileNotFoundError):
            return [], []
    def update_history(self, must_remove: list[str], h1: list[str], h2: list[str]) -> None:
        # h1 e h2 a questo punto sono già stem (senza estensione), quindi
        # rileggiamo i file originali per preservare le estensioni reali
        try:
            with open(self.history_created_path, "r", encoding="utf-8") as f:
                h1_originale = json.load(f)
        except Exception:
            h1_originale = []

        try:
            with open(self.history_loaded_path, "r", encoding="utf-8") as f:
                h2_originale = json.load(f)
        except Exception:
            h2_originale = []

        must_remove_set = set(must_remove)

        h1_da_salvare = [n for n in h1_originale if Path(n).stem not in must_remove_set]
        h2_da_salvare = [n for n in h2_originale if Path(n).stem not in must_remove_set]

        with open(self.history_created_path, "w", encoding="utf-8") as f:
            json.dump(h1_da_salvare, f, indent=4)

        with open(self.history_loaded_path, "w", encoding="utf-8") as f:
            json.dump(h2_da_salvare, f, indent=4)
    def delete_specific(self, paths_to_delete: list[Path]):
        """Elimina file specifici passati dalla GUI e pulisce i log fantasma."""
        must_remove_stems = []
        
        for path in paths_to_delete:
            stem = path.stem
            must_remove_stems.append(stem)
            
            try:
                # La GUI potrebbe aver già rimosso il file fisico dal modello, 
                # ma noi puliamo i residui (JSON o TXT)
                json_path = path.with_suffix(".json")
                txt_path = path.with_suffix(".txt")
                
                if path.exists(): path.unlink()
                if json_path.exists(): json_path.unlink()
                if txt_path.exists(): txt_path.unlink()
            except Exception as e:
                print(f"⚠️ Errore durante la rimozione fisica di {stem}: {e}")
                
        # Ora aggiorno le liste rimuovendo i "fantasmi"
        h1, h2 = self.get_histories()
        self.update_history(must_remove_stems, h1, h2)
        print(f"🧹 Pulizia specifica completata per: {must_remove_stems}")
if __name__ == "__main__":
    dw = DeleteWorker()
    dw.delete()

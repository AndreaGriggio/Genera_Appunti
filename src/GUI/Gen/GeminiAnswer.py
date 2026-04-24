import os
from pathlib import Path
from src.GUI.config import DATAPATH
import json
class GeminiAnswer:
    def __init__(self):
        
        # 1. Definiamo il file della lista nera (storico)
        self.history_file = Path(DATAPATH) / "history_pdf.json"
        
        
        # Se la lista nera non esiste, creiamola vuota
        if not self.history_file.exists():
            with open(self.history_file, "w", encoding="utf-8") as f:
                json.dump([], f)

    def get_history(self) -> list:
        """Legge e restituisce la lista dei file già elaborati."""
        try:
            with open(self.history_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def add_to_history(self, pdf_filename: str):
        """Aggiunge il nome del file alla lista nera, evitando duplicati."""
        history = self.get_history()
        if pdf_filename not in history:
            history.append(pdf_filename)
            with open(self.history_file, "w", encoding="utf-8") as f:
                json.dump(history, f, indent=4)

    def save_answer(self, answer_text: str, pdf_path: str,is_json:bool = True,is_map:bool = False):
        """Salva la risposta di Gemini in un file di testo e aggiorna la blacklist."""
        path_obj = Path(pdf_path)
        nome_pdf = path_obj.stem # Prende "Appunti_Fisica" da "Appunti_Fisica.pdf"
        cartella_pdf = path_obj.parent # Prende "Appunti_Fisica" da "Appunti_Fisica.pdf"
        # Salvataggio Appunti (puoi usare .json o .txt in base a come ti risponde Gemini)
        if is_map:
            output_file = cartella_pdf /f"{nome_pdf}.mappa"
        elif is_json:
            output_file = cartella_pdf / f"{nome_pdf}.json"
        else: 
            output_file = cartella_pdf/f"{nome_pdf}.txt"
        
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(answer_text)
            
        # Aggiunta alla lista nera
        if not is_map:
            self.add_to_history(path_obj.name)
from PyQt6.QtCore import QThread, pyqtSignal
from src.GUI.GeminiAsker import GeminiAsker
from src.GUI.GeminiAnswer import GeminiAnswer # Adegua l'import
from google.genai import types
from pathlib import Path

class GeminiSyncWorker(QThread):
    PDF_SUFFIXES = {".pdf"}
    TEXT_SUFFIXES = {".txt"}

    finished = pyqtSignal()      
    error = pyqtSignal(str)      
    log = pyqtSignal(str)        
    progress = pyqtSignal(int, int) # Nuovo: Invia (File_corrente, File_totali)

    # GLI ARGOMENTI VANNO QUI
    def __init__(self, prompt: str, paths: list, pdf: bool = True, json_mode: bool = True):
        super().__init__()
        self.prompt = prompt
        self.pdf_paths = paths # È una LISTA di percorsi
        self.pdf = pdf
        self.json_mode = json_mode

    # RUN NON ACCETTA ARGOMENTI
    def run(self):
        try:
            self.log.emit(f"⏳ Inizio generazione per {len(self.pdf_paths)} file...")
            
            asker = GeminiAsker()
            answer_handler = GeminiAnswer()
            
            totali = len(self.pdf_paths)
            
            for index, path in enumerate(self.pdf_paths, start=1):
                
                nome_file = Path(path).name
                
                path_obj = Path(path)
                nome_file = path_obj.name
                suffix = path_obj.suffix.lower()

                if suffix not in GeminiSyncWorker.PDF_SUFFIXES | GeminiSyncWorker.TEXT_SUFFIXES:
                    self.log.emit(f"⏭️ [{index}/{totali}] Formato non supportato, ignorato: {nome_file}")
                    self.progress.emit(index, totali)
                    continue
 
                self.log.emit(f"📄 [{index}/{totali}] Elaborazione di: {nome_file}...")

                # 1. Chiedi a Gemini
                l = asker.ask(
                    prompt=self.prompt, 
                    path=str(path), 
                    pdf=self.pdf, 
                    is_json=self.json_mode
                )
                if not l:
                    self.log.emit(f"⚠️ Errore o modello esaurito per: {nome_file}")
                    continue
                if isinstance(l[0],types.GenerateContentResponse): response = l[0] 
                else: response = types.GenerateContentResponse()

                if isinstance(l[1],bool): self.json_mode = l[1]

                
                # 2. Salva la risposta se c'è
                if response.text:
                    answer_handler.save_answer(response.text, path,self.json_mode)
                    self.log.emit(f"✅ Salvato con successo: {nome_file}")
                else:
                    self.log.emit(f"⚠️ Errore o modello esaurito per: {nome_file}")
                
                # Aggiorna la barra di caricamento nella GUI
                self.progress.emit(index, totali)
            
            self.log.emit("🎉 Creazione  terminata!")
            self.finished.emit()
            
        except Exception as e:
            self.error.emit(str(e))
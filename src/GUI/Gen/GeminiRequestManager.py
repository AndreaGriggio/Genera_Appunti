from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Tuple
from google.genai import types
from src.GUI.Gen.GeminiAsker import GeminiAsker
from src.GUI.Gen.GeminiAnswer import GeminiAnswer
from pathlib import Path

class GeminiRequestManager:
    """Gestisce richieste parallele a Gemini API"""
    
    PDF_SUFFIXES = {".pdf"}
    TEXT_SUFFIXES = {".txt"}
    MAX_WORKERS = 3  # Configurabile
    
    def __init__(self):
        self.asker = GeminiAsker()
        self.answer_handler = GeminiAnswer()
    
    def is_supported_format(self, path: str) -> bool:
        suffix = Path(path).suffix.lower()
        return suffix in (self.PDF_SUFFIXES | self.TEXT_SUFFIXES)
    
    def process_file(self, path: str, prompt: str, pdf: bool, 
                    json_mode: bool, is_map: bool) -> Tuple[str, bool, bool, types.GenerateContentResponse]:
        """Elabora un singolo file in parallelo"""
        try:
            result = self.asker.ask(
                prompt=prompt,
                path=path,
                pdf=pdf,
                is_json=json_mode,
                gen_map=is_map
            )
            if result is None:
                raise Exception("Nessuna risposta da Gemini")
            response = result[0] if isinstance(result[0], types.GenerateContentResponse) else types.GenerateContentResponse()
            json_mode = result[1] if isinstance(result[1], bool) else json_mode
            is_map = result[2] if isinstance(result[2], bool) else is_map
            
            return path, json_mode, is_map, response
            
        except Exception as e:
            raise Exception(f"Errore elaborazione {Path(path).name}: {str(e)}")
    
    def process_files_parallel(self, paths: List[str], prompt: str, pdf: bool,
                               json_mode: bool, is_map: bool, callback=None):
        """
        Elabora più file in parallelo
        callback: funzione(path, json_mode, is_map, response, error)
        """
        with ThreadPoolExecutor(max_workers=self.MAX_WORKERS) as executor:
            futures = {
                executor.submit(self.process_file, path, prompt, pdf, json_mode, is_map): path
                for path in paths if self.is_supported_format(path)
            }
            
            for future in as_completed(futures):
                try:
                    path, updated_json, updated_map, response = future.result()
                    
                    # Salva se c'è risposta
                    if response.text:
                        self.answer_handler.save_answer(response.text, path, updated_json, updated_map)
                        callback(path, updated_json, updated_map, response, None)
                    else:
                        callback(path, updated_json, updated_map, None, "Nessuna risposta")
                        
                except Exception as e:
                    callback(futures[future], json_mode, is_map, None, str(e))
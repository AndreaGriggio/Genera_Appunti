from faster_whisper import WhisperModel
from pathlib import Path

class TranscribeWorker:
    SUPPORTED_FORMATS = {".mp3",".mp4", ".wav", ".m4a", ".ogg"}

    def __init__(self) -> None:
        self.model = WhisperModel("medium",device="cuda",compute_type="float32")
        
    def transcribe(self,file:Path)-> str| None:
        if file.suffix in [".mp3",".mp4", ".wav", ".m4a", ".ogg"]:
            print(f"Processando : {file}")
            segments , info = self.model.transcribe(str(file),language="it")
            testo = " ".join(s.text for s in segments)
            
            return testo
        else :
            print("merda non MP3")
            return None
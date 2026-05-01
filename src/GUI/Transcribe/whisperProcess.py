from faster_whisper import WhisperModel
import sys
import os
from pathlib import Path

def _get_model_path() -> str:
    """
    Restituisce il percorso del modello Whisper.
    - Se l'app è frozen (PyInstaller), cerca il modello bundlato dentro _MEIPASS.
    - Altrimenti usa il nome standard (faster-whisper scarica in ~/.cache).
    
    NOTA: il nome "light" non esiste. Modelli validi: tiny, base, small, medium, large-v2.
    Scegliamo "tiny" (75MB, italiano sufficiente per appunti universitari).
    """
    MODEL_NAME = "tiny"

    if getattr(sys, 'frozen', False):
        # App frozen: il modello è stato bundlato in _MEIPASS/faster-whisper-tiny/
        bundled_path = Path(sys._MEIPASS) / f"faster-whisper-{MODEL_NAME}"
        if bundled_path.exists():
            return str(bundled_path)
        # Fallback: se per qualche motivo non trovato, prova la cache utente
        print(f"[WARN] Modello bundlato non trovato in {bundled_path}, uso cache.")
        return MODEL_NAME
    else:
        # Sviluppo: usa la cache standard di HuggingFace
        return MODEL_NAME


def whisper_lazy_engine(task_queue, result_queue):
    """Gira in background, carica Whisper solo al primo bisogno."""
    model = None
    model_path = _get_model_path()

    while True:
        task = task_queue.get()
        if task == "STOP":
            break

        if model is None:
            result_queue.put({"type": "log", "content": "⏳ Caricamento modello Whisper..."})
            try:
                model = WhisperModel(
                    model_path,
                    device="auto",
                    compute_type="float32",
                    # Quando frozen, il modello è locale: non serve download
                    local_files_only=getattr(sys, 'frozen', False),
                )
                result_queue.put({"type": "log", "content": "Modello caricato."})
            except Exception as e:
                result_queue.put({"type": "error", "content": f"Errore caricamento modello: {e}"})
                continue

        audio_paths = task.get("paths", [])
        for file in audio_paths:
            if file.suffix.lower() not in {".mp3", ".mp4", ".wav", ".m4a", ".ogg"}:
                print(f"Formato non supportato: {file}")
                continue

            print(f"Processando: {file}")
            try:
                segments, info = model.transcribe(str(file), language="it")
                testo = " ".join(s.text for s in segments)
            except Exception as e:
                result_queue.put({"type": "error", "content": f"Errore trascrizione {file.name}: {e}"})
                continue

            output_path = file.with_suffix(".txt")
            try:
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(testo)
                print(f"Salvata trascrizione: {output_path.name}")
            except Exception as e:
                print(f"Errore salvataggio {output_path.name}: {e}")

            result_queue.put({"type": "file_done", "path": str(output_path)})

        result_queue.put({"type": "all_done"})
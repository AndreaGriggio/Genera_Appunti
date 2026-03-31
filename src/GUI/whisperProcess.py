from faster_whisper import WhisperModel
def whisper_lazy_engine(task_queue, result_queue):
    """Gira in background, ma carica Whisper solo al primo bisogno."""
    model = None # Il modello parte come nullo
    
    while True:
        task = task_queue.get() 
        if task == "STOP":
            break
            
        # CARICAMENTO PIGRO: Avviene solo qui
        if model is None:
            result_queue.put({"type": "log", "content": "⏳ Primo utilizzo: caricamento modello Whisper (1.5GB)..."})
            try:
                
                model = WhisperModel("medium", device="cuda", compute_type="float32")
                result_queue.put({"type": "log", "content": "✅ Modello caricato e pronto per questa sessione."})
            except Exception as e:
                result_queue.put({"type": "error", "content": f"Errore caricamento: {e}"})
                continue

        # Esecuzione della trascrizione (ora il modello è sicuramente in memoria)
        audio_paths = task.get("paths", [])
        for file in audio_paths:
            if file.suffix in [".mp3",".mp4", ".wav", ".m4a", ".ogg"]:
                print(f"Processando : {file}")
                segments , info = model.transcribe(str(file),language="it")
                testo = " ".join(s.text for s in segments)                
            else :
                print("merda non MP3")
                continue
            output_path = file.with_suffix(".txt")
            
            if isinstance(testo,str):
                        try : 
                            
                            with open(output_path,"w",encoding="utf-8") as f:
                                f.write(testo)
                            print(f"Salvata la trascrizione {output_path.name}")
                        except Exception as e :
                            print(f"Errore :{e}")
            result_queue.put({"type": "file_done", "path": str(output_path)})
        
        result_queue.put({"type": "all_done"})
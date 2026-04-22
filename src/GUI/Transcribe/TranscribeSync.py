from pathlib import Path
from PyQt6.QtCore import QThread, pyqtSignal
from src.GUI.Transcribe.TranscribeWorker import TranscribeWorker

class TranscribeSyncWorker(QThread):
    finished = pyqtSignal()      # Dice "Ho finito!"
    error = pyqtSignal(str)      # Dice "C'è stato un errore: ..."
    log = pyqtSignal(str)        # Manda messaggi di testo alla console della GUI

    def __init__(self,is_loaded:bool,selected_files:list[Path],worker:TranscribeWorker) -> None:
        super().__init__()
        self.worker = worker
        self.model_is_loaded = is_loaded
        self.selected_files = selected_files

    def run(self):
        """ 
        TranscribeWorker serve per analizzare un audio è richiesto l'utilizzo di cpu o GPU se presente
        Gestisce in automatico questa decisione la trascrizzione può durare parecchio tempo non chiudere l'applicazione
        """
        try:
            self.log.emit("Inizio di tracrizione ")

            if not self.model_is_loaded:
                print("Manca il worker!")
                return
            else : 
                for file in self.selected_files:
                    #Controllo per verificare se c'è lavoro da fare
                    if file.suffix.lower() in TranscribeWorker.SUPPORTED_FORMATS:

                        testo = self.worker.transcribe(file)
                    else : 
                        continue
                    if isinstance(testo,str):
                        try : 
                            output_path = file.with_suffix(".txt")
                            with open(output_path,"w",encoding="utf-8") as f:
                                f.write(testo)
                            print(f"Salvata la trascrizione {output_path.name}")
                        except Exception as e :
                            print(f"Errore :{e}")

            self.log.emit("Operazione terminata")
            self.finished.emit()
            

        except Exception as e:
            print(f"Errore {e}")
            self.error.emit("Errore o file ignorati ")


    
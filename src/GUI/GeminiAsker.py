from google.genai import Client,types,errors
from src.GUI.config import GEMINI_TOKEN,NOTION_SYSTEM_INSTRUCTION
from src.GUI.ModelManager import ModelManager
from pathlib import Path

class GeminiAsker :
    PDF_MIME  = "application/pdf"
    TEXT_MIME = "text/plain"

    def __init__(self) -> None:
        self.client = Client(api_key=GEMINI_TOKEN)
        self.manager = ModelManager()

        for mode in self.manager.models:
            if mode["available"]:
                self.current_model = mode["name"]
                break
    def ask(self, prompt: str, path: str = "", pdf: bool = False, is_json: bool = False) -> list[types.GenerateContentResponse |bool]| None:
        """
        Invia una richiesta a Gemini.
        Gestisce automaticamente il cambio modello in caso di errore 429 (Quota).
        """
        if not prompt : 
            return None
        path_obj  = Path(path) if path else None
        is_pdf    = path_obj is not None and path_obj.suffix.lower() == ".pdf"
        has_file  = path_obj is not None and path_obj.exists()
        # 1. SCELTA DEL MODELLO
        # Chiediamo al manager il miglior modello disponibile ORA
        l= self.manager.get_best_model(needs_pdf=pdf, needs_json=is_json)
        if not l:
            print("Nessun modello disponibile o risorse esaurite su tutti i modelli.")   
            return None

        #Campi di ritorno del model manager 
        #l[0] è il nome del modello
        #l[1] è se il modello supporta la creazione di json
        if isinstance(l[0],str):
            model_name = l[0] 
            if isinstance(l[1],bool):
                json=l[1]
        else :
            model_name = None
            json = False
        # Se il manager restituisce None, significa che abbiamo finito i modelli (o i tentativi)
        if model_name is None:
            print("Nessun modello disponibile o risorse esaurite su tutti i modelli.")
            return None

        print(f"Tentativo con modello: {model_name}")

        # 2. CONFIGURAZIONE
        config = self.manager.get_config(model_name, force_json=is_json,system_instruction=NOTION_SYSTEM_INSTRUCTION)

        # 3. PREPARAZIONE CONTENUTI
        contents = []
        
        if has_file:
            try:
                if is_pdf:
                    # PDF → bytes con mime type corretto
                    pdf_bytes = path_obj.read_bytes()
                    contents.append(types.Part.from_bytes(
                        data=pdf_bytes,
                        mime_type=GeminiAsker.PDF_MIME
                    ))
                else:
                    # TXT o qualsiasi altro testo → stringa diretta
                    testo = path_obj.read_text(encoding="utf-8")
                    contents.append(testo)
            except Exception as e:
                print(f"Errore caricamento file {path}: {e}")
                return None
 
        contents.append(prompt)
 
        # 4. Chiamata API
        try:
            response = self.client.models.generate_content(
                model=model_name,
                contents=contents,
                config=config
            )
            return [response, is_json]
 
        except errors.ClientError as e:
            error_code = e.code if hasattr(e, "code") else 0
 
            if error_code == 429:
                print(f"Quota esaurita per {model_name}. Cambio modello...")
                self.manager.report_error(model_name, error_code)
                return self.ask(prompt, path, is_json)
 
            elif error_code >= 500:
                print(f"Errore Server Google ({error_code}). Riprovo...")
                self.manager.report_error(model_name, error_code)
                return self.ask(prompt, path, is_json)
 
            else:
                print(f"Errore non recuperabile ({error_code}): {e}")
                return None
 
        except Exception as e:
            print(f"Errore generico imprevisto: {e}")
            return None



        
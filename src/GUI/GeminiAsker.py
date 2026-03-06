from google.genai import Client,types,errors
from src.GUI.config import GEMINI_TOKEN,NOTION_SYSTEM_INSTRUCTION
from src.GUI.ModelManager import ModelManager
from pathlib import Path

class GeminiAsker :
    def __init__(self) -> None:
        self.client = Client(api_key=GEMINI_TOKEN)
        self.manager = ModelManager()

        for mode in self.manager.models:
            if mode["available"]:
                self.current_model = mode["name"]
                break
    def ask(self, prompt: str, pdf_path: str = "", pdf: bool = False, json: bool = False) -> list[types.GenerateContentResponse |bool]| None:
        """
        Invia una richiesta a Gemini.
        Gestisce automaticamente il cambio modello in caso di errore 429 (Quota).
        """
        if prompt == "": 
            return None

        # 1. SCELTA DEL MODELLO
        # Chiediamo al manager il miglior modello disponibile ORA
        l= self.manager.get_best_model(needs_pdf=pdf, needs_json=json)
        if not l:
            print("❌ Nessun modello disponibile o risorse esaurite su tutti i modelli.")   
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
            print("❌ Nessun modello disponibile o risorse esaurite su tutti i modelli.")
            return None

        print(f"🤖 Tentativo con modello: {model_name}")

        # 2. CONFIGURAZIONE
        config = self.manager.get_config(model_name, force_json=json,system_instruction=NOTION_SYSTEM_INSTRUCTION)

        # 3. PREPARAZIONE CONTENUTI
        contents = []
        
        # Gestione PDF (Caricamento o Bytes)
        if pdf and pdf_path:
            try:
                # Opzione A: Upload tramite File API (come facevi tu)
                pdf_bytes = Path(pdf_path).read_bytes()
                pdf_part = types.Part.from_bytes(
                    data = pdf_bytes,
                    mime_type="application/pdf"
                )
                contents.append(pdf_part)
            except Exception as e:
                print(f"❌ Errore caricamento file {pdf_path}: {e}")
                return None # Se fallisce l'upload del file, è inutile interrogare il modello
        
        contents.append(prompt)

        # 4. CHIAMATA API con gestione errori semplice
        try:
            response = self.client.models.generate_content(
                model=model_name,
                contents=contents,
                config=config
            )
            return [response,json]

        except errors.ClientError as e:
            # L'errore ClientError contiene lo status code HTTP
            error_code = e.code if hasattr(e, 'code') else 0
            
            # --- CASO A: RISORSE ESAURITE (429) ---
            if error_code == 429:
                print(f"⚠️ Quota esaurita per {model_name} (Err 429). Cambio modello...")
                
                # 1. Segnala al manager che questo modello è morto
                self.manager.report_error(model_name,error_code)
                
                # 2. RICORSIONE: Riprova la stessa domanda
                # Il manager ora escluderà il modello fallito e ti darà il prossimo
                return self.ask(prompt, pdf_path, pdf, json)

            # --- CASO B: ERRORE SERVER GOOGLE (500, 503) ---
            elif error_code >= 500:
                print(f"⚠️ Errore Server Google ({error_code}). Riprovo con altro modello...")
                self.manager.report_error(model_name,error_code)
                return self.ask(prompt, pdf_path, pdf, json)

            # --- CASO C: ERRORE RICHIESTA (400) ---
            else:
                print(f"❌ Errore non recuperabile ({error_code}): {e}")
                # Se la richiesta è malformata (es. file troppo grande), inutile riprovare
                return None

        except Exception as e:
            # Errori generici di Python (es. rete staccata)
            print(f"❌ Errore generico imprevisto: {e}")
            return None



        
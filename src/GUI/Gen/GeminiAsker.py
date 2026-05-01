from google.genai import Client,types,errors
from src.GUI.config import GEMINI_TOKEN,NOTION_SYSTEM_INSTRUCTION,MENTAL_MAP_SYSTEM_INSTRUCTION
from src.GUI.Gen.ModelManager import ModelManager
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
    def ask(self, prompt: str, path: str = "", pdf: bool = False, 
        is_json: bool = False, gen_map: bool = False):
    
        MAX_ATTEMPTS = 5

        for attempt in range(MAX_ATTEMPTS):
            l = self.manager.get_best_model(needs_pdf=pdf, needs_json=is_json)
            if not l:
                print("Nessun modello disponibile.")
                return None

            model_name = l[0] if isinstance(l[0],str) else self.current_model
            json_mode = l[1] if isinstance(l[1], bool) else False

            instructions = MENTAL_MAP_SYSTEM_INSTRUCTION if gen_map else NOTION_SYSTEM_INSTRUCTION
            config = self.manager.get_config(
                model_name, 
                gen_map=gen_map,
                force_json=json_mode, 
                system_instruction=instructions
            )

            contents = []
            path_obj = Path(path) if path else None
            
            if path_obj and path_obj.exists():
                try:
                    if path_obj.suffix.lower() == ".pdf":
                        contents.append(types.Part.from_bytes(
                            data=path_obj.read_bytes(),
                            mime_type=GeminiAsker.PDF_MIME
                        ))
                    else:
                        contents.append(path_obj.read_text(encoding="utf-8"))
                except Exception as e:
                    print(f"Errore caricamento file: {e}")
                    return None

            contents.append(prompt)

            try:
                response = self.client.models.generate_content(
                    model=model_name,
                    contents=contents,
                    config=config
                )
                return [response, json_mode, gen_map]

            except errors.ClientError as e:
                error_code = e.code if hasattr(e, "code") else 0
                if error_code in (429, 500, 502, 503, 504):
                    print(f"Errore {error_code} su {model_name}, cambio modello...")
                    self.manager.report_error(model_name, error_code)
                    continue  
                else:
                    print(f"Errore non recuperabile ({error_code}): {e}")
                    return None

            except Exception as e:
                error = str(e)
                self.manager.report_error(error,-1)  
                print(f"Errore generico: {e}")
                return None

        self.manager.report_error("Tentaivi esauriti",-1)
        return None

        
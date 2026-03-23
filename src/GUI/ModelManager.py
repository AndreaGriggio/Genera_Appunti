from src.GUI.config import (FREE_MODELS,GEMINI_TOKEN,NOTION_SYSTEM_INSTRUCTION,
                            TEMPERATURE,MAX_TOKENS)
from google.genai import Client,types
from time import time
import time
from src.GUI.NotionSchema import NotionDocument
#questa classe serve puramente alla gestione delle risorse disponibili offerete dalle google api
#al momento con programmazione hardcore facciamo in modo che tenga conto solo per alcuni modelli ha le risposte disponibili o meno

class ModelManager:
    def __init__(self):
        if not GEMINI_TOKEN:
            raise ValueError("GEMINI_TOKEN non trovata nelle variabili d'ambiente.")
        
        self.client = Client(api_key=GEMINI_TOKEN)
        self.models =[m.copy() for m in FREE_MODELS]
        self.cooldowns = {}
        self.RATE_LIMIT_COOLDOWN = 60
        self._initial_api_check()
    def _initial_api_check(self):
        # Utile per scremare se google fa degli aggiornamenti allora lo noto subito
        """Controlla SOLO all'avvio se i modelli esistono nell'API (Ban Permanente)."""
        try:
            remote_models = list(self.client.models.list())
            remote_names = [str(m.name).replace("models/", "") for m in remote_models]
            
            for m in self.models:
                if m["name"] not in remote_names and f"models/{m['name']}" not in remote_names:
                    print(f"💀 Modello '{m['name']}' inesistente. Rimosso per sempre.")
                    m["available"] = False
        except Exception:
            pass

    def get_best_model(self, needs_pdf: bool = False, needs_json: bool = False) -> list[str|bool] | None:
        """
        Restituisce il miglior modello UTILIZZABILE ORA.
        """
        # 1. Aggiorna lo stato dei modelli (riattiva quelli scaduti)
        self._refresh_availability()
        l = []

        for model in self.models:
            name = model["name"]

            # CRITERI DI ESCLUSIONE
            
            # 1. Se è disabilitato permanentemente (es. non esiste)
            if not model["available"]: 
                continue
        
            # 2. Check funzionalità (PDF/JSON)
            if needs_pdf and not model["pdf"]: 
                continue
            
            # 3. Preferenza JSON
            if needs_json and model["config"]:
                l = [name,model["config"]]
                return l
        
        # Fallback: Se non trovo modelli JSON nativi, cerco qualsiasi modello disponibile
        for model in self.models:
            name = model["name"]
            if not model["available"] or name in self.cooldowns: continue
            if needs_pdf and not model["pdf"]: continue
            l = [name,model["config"]]
            return l

        return None
    def _refresh_availability(self):
        """
        Questa è la funzione che chiedevi: 
        Controlla se i modelli in pausa possono tornare attivi.
        """
        now = time.time()
        models_recovered = []

        # Creiamo una lista delle chiavi da rimuovere per non modificare il dizionario mentre lo iteriamo
        to_recover = []
        
        for model_name, unlock_time in self.cooldowns.items():
            if now >= unlock_time:
                # Il tempo è scaduto, il modello è perdonato
                to_recover.append(model_name)

        for model_name in to_recover:#rimozione dalla lista dei modelli in pausa
            
            del self.cooldowns[model_name]
            
            for model in self.models:
                if model["name"] == model_name:
                    model["available"] = True
                    print(f"♻️  Il modello {model_name} è tornato disponibile!")

                    break

    def report_error(self, model_name: str, error_code: int):
        """
        Gestisce l'errore segnalato dal Worker.
        - 429 (Too Many Requests): Pausa temporanea (60s).
        - Altro (404, ecc): Ban permanente.
        """
        if error_code == 429:
            print(f"⏳ Modello {model_name} in pausa per {self.RATE_LIMIT_COOLDOWN}s (Rate Limit).")
            # Imposta il timestamp nel futuro quando sarà sbloccato
            self.cooldowns[model_name] = time.time() + self.RATE_LIMIT_COOLDOWN

            for model in self.models:
                if model["name"] == model_name:
                    model["available"] = False
                    break
        else:
            print(f"❌ Modello {model_name} rotto (Err {error_code}). Disabilitato permanentemente.")
            # Trova il modello e settalo available=False per sempre
            for m in self.models:
                if m["name"] == model_name:
                    m["available"] = False
                    break

    def get_config(self, model_name: str, force_json: bool = False, system_instruction: str = " ") -> types.GenerateContentConfig:
        """
        Restituisce la configurazione ottimizzata.
        Accetta 'system_instruction' per passare il prompt di ruolo.
        """
        model_info = next((m for m in self.models if m["name"] == model_name), None)#Se troviamo un modello con quel nome lo prendiamo altrimenti None
        
        if not model_info:
            return types.GenerateContentConfig()#Quando None torniamo zero configurazioni

        # --- CASO 1: GEMINI (Supporto JSON Nativo + Config Avanzata) ---
        if model_info["config"]:
            if force_json:
                print(f"⚙️ {model_name}: Configuro JSON Mode per Appunti temp = {TEMPERATURE}.")
                return types.GenerateContentConfig(
                    temperature=TEMPERATURE,        # La tua scelta ottima per appunti tecnici
                    top_p=0.95,             # Standard per diversità
                    max_output_tokens=MAX_TOKENS, # Massimo output possibile
                    response_mime_type="application/json", # Forza JSON
                    response_schema=NotionDocument,
                    system_instruction=system_instruction  # Inserisce il tuo prompt qui
                )
            else:
                # Configurazione standard per chat generica
                print(f"⚙️ {model_name}: Configuro Chat Standard.")
                return types.GenerateContentConfig(
                    temperature=TEMPERATURE,
                    system_instruction=system_instruction
                )
        
        # --- CASO 2: GEMMA (Solo Testo, parametri limitati) ---
        # Gemma via API spesso crasha se gli passi system_instruction o mime_type json
        print(f"⚙️ {model_name}: Configurazione Base (Gemma).")
        return types.GenerateContentConfig(
            temperature=TEMPERATURE,
            max_output_tokens=MAX_TOKENS
            # Niente system_instruction o json qui per sicurezza su Gemma
        )
    def mark_unavailable(self,model_name : str):
        for model in self.models:
            if model["name"]==model_name:
                model["available"] = False
        
    
if __name__ == "__main__":
    manager = ModelManager()


    for model in manager.models:
        print("name:", model["name"])
        print("available:", model["available"])
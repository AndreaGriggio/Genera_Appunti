def lancia_prompt():
    """
    Scrive un prompt a partire da un file di testo e lo invia al modello di linguaggio.
    file_path deve essere un percorso completo al file di testo.

    Args:
        prompt (str): Il prompt da scrivere nel file.
        file_path (str): Il percorso del file in cui scrivere il prompt.
    """
    
  
        try :
            scrivi_prompt_da_testo(file_path)
        except TokenLimitExceededError as e :
            print(e)
    for prompt in TEXT_PATH.rglob("*.json"):
        with open(prompt,"r", encoding='utf-8') as prompt_file:#apro il file prompt base
                    contenuto_prompt = json.load(prompt_file)#carico il contenuto in una variabile
        token = calcola_token(contenuto_prompt["messages"][1]["content"])
        try : 
            if(token < TOKEN_LIMIT):
                print(f"Elaborando su modello {contenuto_prompt['model']}: {prompt} " )
                print(f"Nr. approx token : {token}")
                
                url = "http://localhost:11434/api/chat"

                data = {
                    **contenuto_prompt,
                    "stream": False
                    }
                response = requests.post(url, json=data, timeout=180)
                response.raise_for_status()

                percorso_branch_json = sottrai_path(prompt,TEXT_PATH)


                percorso_json = RISPOSTE_PATH/percorso_branch_json.with_suffix(".json")

                salva_json_in(response.json(),percorso_json)

                print(f"Risposta salvata in : {percorso_json}")
        except TokenLimitExceededError as e :
            print(e)        

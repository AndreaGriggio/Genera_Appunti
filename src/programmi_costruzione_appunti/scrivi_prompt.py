from .config import TOKEN_LIMIT,PROMPT_PATH,TEXT_PATH,RISPOSTE_PATH,DATA_PATH
import json
from .utils import sottrai_path,num_predict_rc,calcola_token,salva_json_in
from pathlib import Path
from .TokenLimit import TokenLimitExceededError
from .branch_explorer import esplora_txt
import requests




def taglia_testo(testo: str, max_token: int = 600) -> list[str]:
    parole = testo.split()
    chunks = []
    corrente = []

    for p in parole:
        corrente.append(p)
        testo_corrente = " ".join(corrente)
        if calcola_token(testo_corrente) > max_token:
            # togli ultima parola per non sforare
            corrente.pop()
            chunks.append(" ".join(corrente))
            corrente = [p]  # riparti con la parola corrente

    if corrente:
        chunks.append(" ".join(corrente))

    return chunks







def scrivi_prompt_da_testo(file_path : Path):
    """
    Scrive un prompt in un file di testo.

    Args:
        prompt (str): Il prompt da scrivere nel file.
        file_path (str): Il percorso del file in cui scrivere il prompt.
    """
    with open(file_path, 'r', encoding='utf-8') as file:
        testo = file.read()


    numero_token = calcola_token(testo)
    with open(PROMPT_PATH,"r", encoding='utf-8') as prompt_file:#apro il file prompt basesrc/data/prompt_base.json
        prompt = json.load(prompt_file)#carico il contenuto in una variabile

    prompt["messages"][1]["content"] = testo#modifico il contenuto del messaggio user
    prompt["num_predict"] = num_predict_rc(numero_token)#imposto il numero di token di risposta a meta del totale
    

    prompt_path = file_path.with_suffix(".json")
    with open(prompt_path,"w", encoding='utf-8') as prompt_file:#apro il file prompt base in scrittura
        json.dump(prompt, prompt_file, indent=4, ensure_ascii=False)#scrivo il nuovo prompt nel file di destinazione
        
    print(f"Nr. approx token : {numero_token}")#stampo il numero di token approssimativo

def dividi_testi(path: Path):
    with open(path, "r", encoding="utf-8") as f:
        testo = f.read()

    chunks = taglia_testo(testo, max_token=600)

    if len(chunks) == 1:
        return

    for i, c in enumerate(chunks):
        new_path = path.parent / f"{path.stem}_{i}.txt"
        with open(new_path, "w", encoding="utf-8") as f:
            f.write(c)

    path.unlink()




def lancia_prompt():
    """
    Scrive un prompt a partire da un file di testo e lo invia al modello di linguaggio.
    file_path deve essere un percorso completo al file di testo.

    Args:
        prompt (str): Il prompt da scrivere nel file.
        file_path (str): Il percorso del file in cui scrivere il prompt.
    """
    for text in esplora_txt():
        dividi_testi(text)
    for file_path in esplora_txt():
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



    # Implementa la logica per lanciare il prompt con il modello di linguaggio
if __name__ == "__main__":
    lancia_prompt()

from .config import TOKEN_PER_PAROLA,PDF_PATH,BACKUP_PATH
import math
from pathlib import Path
import json

import os

def calcola_token(testo):
    numero_parole = len(testo.split())
    numero_token = numero_parole * TOKEN_PER_PAROLA
    return numero_token

def salva_testo_in(testo_completo, percorso_file_testo):    
    with open(percorso_file_testo, 'w', encoding='utf-8') as file_testo:
        print(f"Salvataggio del testo in: {percorso_file_testo}\n")
        file_testo.write(testo_completo)
        file_testo.close()

def salva_json_in(json_completo : dict,percorso_file_json : Path):
        with open(percorso_file_json, "w", encoding="utf-8") as f:
            json.dump(json_completo, f, indent=4, ensure_ascii=False)

def num_predict_rc(
    in_tokens: int,
    max_out: int = 1500,
    min_out: int = 150,
    y_min: float = 0.50,        # ~35% del massimo anche con input piccoli
    x_half: int = 1200,         # a ~1200 token input sei a metà della dinamica utile
    context_limit: int = 32768, # Qwen 7B-ish; adegua al tuo modello
    margin: int = 256           # margine per system + header
) -> int:
    # costante di tempo dalla mezza-saturazione
    tau = x_half / math.log(2)

    # curva "carica RC": y in (y_min, 1)
    y = y_min + (1 - y_min) * (1 - math.exp(-max(in_tokens, 0) / tau))

    # token d'uscita proposti prima del guardrail contesto
    out_raw = int(round(y * max_out))

    # guardrail sul context window
    ctx_guard = max(min_out, context_limit - in_tokens - margin)

    # clamp finale
    return max(min_out, min(out_raw, ctx_guard))

def sottrai_path(longerPath : Path,shorterPath : Path):
    a = Path(longerPath).resolve()
    b = Path(shorterPath).resolve()

    try : 
        c = a.relative_to(b)
        return c
    except Exception as e:
        print(f"il file scelto ha questo problema : {e}")

def backup_data():
    """
    Crea una copia di backup di tutti i file PDF nella cartella data/pdf
    all'interno della cartella BACKUP_PATH, mantenendo la struttura.
    """
    pdf_root = PDF_PATH
    backup_root = BACKUP_PATH

    for file in pdf_root.glob("**/*.pdf"):
        if file.is_file():

            # ottieni la parte relativa del file rispetto a PDF_PATH
            relative = sottrai_path(file, pdf_root)  # esempio: "analisi/limiti/es1.pdf"

            # percorso reale del backup
            backup_path = backup_root / relative

            # crea tutte le cartelle necessarie

            # copia il file
            with open(file, "rb") as original, open(backup_path, "wb") as backup:
                backup.write(original.read())

            print(f"Backup creato: {backup_path}")

def restore_data():
    """ Ripristina le informazioni contenute all'interno di backupPDF su pdf"""
    backup_root = BACKUP_PATH
    pdf_root = PDF_PATH

    for file in backup_root.glob("**/*.pdf"):
        if file.is_file():

            # ottieni la parte relativa del file rispetto a PDF_PATH
            relative = sottrai_path(file, backup_root)  # esempio: "analisi/limiti/es1.pdf"

            # percorso reale del backup
            pdf_path = pdf_root / relative

            # crea tutte le cartelle necessarie

            # copia il file
            with open(file, "rb") as restore, open(pdf_path, "wb") as to_be_restored:
                to_be_restored.write(restore.read())

            print(f"Restore eseguito: {pdf_path}")


    
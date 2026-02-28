import os
from pathlib import Path
import re
from .config import INFO_BRANCH_PATH,RISPOSTE_PATH,PDF_PATH,BACKUP_PATH,TEXT_PATH
import sys
import json

def pulisci_nome(raw_name):
    """
    Pulisce il nome:
    - toglie lo spazio finale
    - toglie un eventuale ' (id: ...)'
    - opzionale: toglie numerazione iniziale tipo '1.' '0.' ecc.
    """
    name = raw_name

    # Se c'è "(id:" tieni solo la parte prima
    if "(id:" in name:
        name = name.split("(id:", 1)[0]

    name = name.strip()

    return name



def crea_cartelle_da_notions(nodo: dict, base_dir: str = "."):
    """
    Crea una struttura di cartelle seguendo un albero di pagine Notion.
    Il nodo deve avere struttura:
    {
        "id": "...",
        "titolo": "...",
        "livello": int,
        "children": [...]
    }
    """
    print(nodo)
    base = Path(base_dir)
    nome_cartella = pulisci_nome(nodo["titolo"])
    dir_path = base / nome_cartella

    # crea la cartella
    dir_path.mkdir(parents=True, exist_ok=True)
    print("Creata cartella:", dir_path)

    # ricorsione: crea i figli dentro questa cartella
    for child in nodo.get("children", []):
        crea_cartelle_da_notions(child, dir_path)


def BranchUpdater():
    #Carica i dati
    with open(INFO_BRANCH_PATH, "r", encoding="utf-8") as f:
        dati = json.load(f)
    
    crea_cartelle_da_notions(dati, PDF_PATH)

    crea_cartelle_da_notions(dati, TEXT_PATH)

    crea_cartelle_da_notions(dati, RISPOSTE_PATH)

    crea_cartelle_da_notions(dati,BACKUP_PATH)

if __name__ == "__main__":
    # Cambia questi se necessario
    BranchUpdater()
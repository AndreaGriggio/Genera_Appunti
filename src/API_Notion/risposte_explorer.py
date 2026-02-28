from .config import RISPOSTE_PATH
from pathlib import Path
def esplora_json():
    """Trova tutti i file PDF nella directory data/pdf e nelle sue sotto directory.
    
    Returns:
        list: Una lista di percorsi ai file PDF trovati.
    """
    dir = RISPOSTE_PATH
    files = []

    for file in dir.glob("**/*.json"):
        files.append(file)
    return files
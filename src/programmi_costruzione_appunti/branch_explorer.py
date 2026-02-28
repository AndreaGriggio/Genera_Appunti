import os 

from pathlib import Path
from .config import PDF_PATH,TEXT_PATH

def esplora_pdf():
    """Trova tutti i file PDF nella directory data/pdf e nelle sue sotto directory.
    
    Returns:
        list: Una lista di percorsi ai file PDF trovati.
    """
    dir = PDF_PATH
    files = []

    for file in dir.glob("**/*.pdf"):
        files.append(file)

    return files
def esplora_txt():
    """Trova tutti i file txt nella directory data/testi e nelle sue sotto directory.
    
    Returns:
        list: Una lista di percorsi ai file testi trovati.
    """
    dir = TEXT_PATH
    files = []

    for file in dir.glob("**/*.txt"):
        files.append(file)

    return files
def elimina_txt():
    """Elimina tutti i file txt nella directory data/testi e nelle sue sotto directory.
    
    Returns:
        None"""
    dir = TEXT_PATH

    for file in dir.glob("**/*.txt"):
        os.remove(file)
        print(f"Eliminato: {file}")

def elimina_pdf():
    """Elimina tutti i file PDF nella directory data/pdf e nelle sue sotto directory.
    
    Returns:
        None"""
    dir = PDF_PATH

    for file in dir.glob("**/*.pdf"):
        os.remove(file)
        print(f"Eliminato: {file}")

if __name__ == "__main__":
    print(elimina_txt())
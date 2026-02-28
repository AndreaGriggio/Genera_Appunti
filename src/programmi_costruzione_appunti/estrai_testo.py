from PyPDF2 import PdfReader, PdfWriter
from pathlib import Path
from .config import PDF_PATH, TEXT_PATH
from .branch_explorer import esplora_pdf
from .utils import sottrai_path,salva_testo_in
import os


def estrai_testo_da_pdf(percorso_file_pdf:Path):

    percorso_file_pdf = Path(str(percorso_file_pdf).strip())
    # Apri il file PDF in modalità lettura binaria
    with open(percorso_file_pdf, 'rb') as file_pdf:
        print(f"Estrazione del testo da: {percorso_file_pdf}\n")
        reader = PdfReader(file_pdf)

        testo_completo = ""

        # Itera attraverso tutte le pagine del PDF
        try :
            for pagina in reader.pages:
                testo_completo += pagina.extract_text() + "\n"
        except Exception as e:
            print(f"Errore durante l'estrazione del testo: {e}\n")
    
    percorso_branch_testo = sottrai_path(percorso_file_pdf,PDF_PATH)
    print(f"il percorso è {percorso_branch_testo}")

    percorso_testo = TEXT_PATH / percorso_branch_testo.with_suffix(".txt")
    salva_testo_in(testo_completo, percorso_testo)
    # Scrivi il testo estratto in un file di testo



    


if __name__ == "__main__":

    percorso_txt = TEXT_PATH
    #Inzio elaborazione dei file pdf
    print("Inizio elaborazione dei file PDF...\n")

    #Rinomino tutti i file 
    for file in esplora_pdf():#raccolgo quelli con estensione pdf
        print(f"{file}\n")#li stampo
        file = Path.resolve(file)
        os.rename(file, file.parent / file.name.format().replace(" ","_"))#rinomino sostituendo gli spazi con underscore
    
    #inizio estrazione testo
    print(PDF_PATH)
    for file in esplora_pdf():
        print(f" {file}\n")#stampa
        estrai_testo_da_pdf(file)#chiamata funzione estrai testo
        

    

#percorso_testo = Path("documento_txt.txt").absolute()

#estrai_testo_da_pdf(percorso_pdf, percorso_testo)
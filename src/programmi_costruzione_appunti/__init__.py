import os
from pathlib import Path
from .config import PDF_PATH, TEXT_PATH
from .estrai_testo import estrai_testo_da_pdf
from .scrivi_prompt import lancia_prompt,taglia_testo
from .branch_explorer import esplora_pdf,esplora_txt
from PyPDF2 import PdfReader,PdfWriter
if __name__ == "__main__":
    percorso_txt = TEXT_PATH
    #Inzio elaborazione dei file pdf
    print("Inizio elaborazione dei file PDF...\n")
    
    #Rinomino tutti i file 
    for file in PDF_PATH.glob("*.pdf"):#raccolgo quelli con estensione pdf
        print(f"{file}\n")#li stampo
        os.rename(file, PDF_PATH / file.name.format().replace(" ","_"))#rinomino sostituendo gli spazi con underscore
    
    #inizio estrazione testo
    for file in PDF_PATH.glob("*.pdf"):
        print(f" {file}\n")#stampa
        estrai_testo_da_pdf(file, percorso_txt)#chiamata funzione estrai testo

    for file in percorso_txt.glob("*.txt"):
          lancia_prompt(file)

def taglia_pdf(file_path : Path):
    reader = PdfReader(file_path)
    total_pages = len(reader.pages)

    print(f"PDF totale: {total_pages} pagine")

    folder = file_path.parent
    base_name = file_path.stem
    print(f"il nome del percorso è {folder}")
    print(f"Il nome del file è : {base_name}")
    start = 0
    file_index = 1

    while start < total_pages:
        end = min(start + 20, total_pages)
        writer = PdfWriter()

        for i in range(start, end):
            writer.add_page(reader.pages[i])

        # Questa è la parte importante
        output_name = f"{base_name}{file_index}"
        output_path = (folder / output_name).with_suffix(".pdf")
        
        print(f"output name : {output_name}")
        print(f"output path : {output_path}")

        with open(output_path, "wb") as f:
            writer.write(f)

        print(f"Creato: {output_path}")

        file_index += 1
        start += 20

    print("Divisione completata.")


def estrai_txt_da_pdf_e_lancia_prompt():

    #Inzio elaborazione dei file pdf
    print("Inizio elaborazione dei file PDF...\n")

    #Rinomino tutti i file 
    files = esplora_pdf()
    
    #inizio estrazione testo
    for file in files:
        print(f" {file}\n")#stampa
        estrai_testo_da_pdf(file)#chiamata funzione estrai testo


    lancia_prompt()


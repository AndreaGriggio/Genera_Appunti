from programmi_costruzione_appunti import config
from src.programmi_costruzione_appunti.estrai_testo import estrai_testo_da_pdf



import os 

if __name__ == "__main__":

    percorso_txt = config.TEXT_PATH
    #Inzio elaborazione dei file pdf
    print("Inizio elaborazione dei file PDF...\n")
    
    #Rinomino tutti i file 
    for file in config.PDF_PATH.glob("*.pdf"):#raccolgo quelli con estensione pdf
        print(f"{file}\n")#li stampo
        os.rename(file, config.PDF_PATH / file.name.format().replace(" ","_"))#rinomino sostituendo gli spazi con underscore
    
    #inizio estrazione testo
    for file in config.PDF_PATH.glob("*.pdf"):
        print(f" {file}\n")#stampa
        estrai_testo_da_pdf(file, percorso_txt)#chiamata funzione estrai testo
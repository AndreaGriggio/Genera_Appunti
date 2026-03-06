from google import genai
from google.genai import types
from google.genai.types import ContentListUnionDict
import os
from pathlib import Path
#Cose da fare
# 1. Trovare il modo di personalizzare il modello
PDF_PATH = Path.cwd() / "src" / "API_LLM_Google" / "prova.pdf"#Percorso dei file pdf
print(PDF_PATH)


SYSTEM_INSTRUCTION = """
    Sei un assistente universitario esperto e preciso.
    Il tuo compito è creare appunti tecnici per Notion in una struttura JSON 
    perfettamente formattata per essere importata in Notion.
    
    Regole:
    1. All'interno di "content", usa la sintassi Markdown supportata da Notion:
       - Usa "### " per i titoli di sezione.
       - Usa "- " per le liste puntate.
       - Usa "\\[ ... \\]" per le equazioni LaTeX.
       - Usa "|" per le descrizioni.
       - Usa "```" per i blocchi di codice.
       - Usa "\\newpage" per cambiare pagina

    2. Non inventare informazioni, attieniti al testo fornito.
    """
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
configurazione = types.GenerateContentConfig(
        temperature=0.2,        # <--- TEMPERATURA (0.0 = Robotico/Preciso, 1.0 = Creativo/Casuale)
                                # Per appunti universitari, tieni basso (0.1 - 0.3).
        
        top_p=0.95,             # Parametro standard per la diversità del testo
        max_output_tokens=8192, # Lunghezza massima della risposta
        response_mime_type="application/json", # <--- FORZA L'OUTPUT JSON (Fondamentale)
        
        system_instruction=SYSTEM_INSTRUCTION  # <--- INSERIMENTO DEL RUOLO
    )
strcontent = str(PDF_PATH)
file = client.files.upload(file = strcontent)
print(file)
risposta = client.models.generate_content(model = 'models/gemini-2.5-flash',contents = [file,'Potresti spiearmi il contenuto del file caricato?'], config=configurazione)
print(risposta.text)
from pathlib import Path
import json
import os
from .SubPage import SubPage
from .utils import text_to_rich_text
from .config import NOTION_TOKEN,DATA_PATH
from .risposte_explorer import esplora_json
from notion_client import Client
""" Programma per creare subpages partendo da risposte utilizzando qwend 2.5"""

def inserisci_appunti():
    notion = Client(auth=NOTION_TOKEN)
    risposte = leggi_risposte()

    with open(DATA_PATH/"dict_notion.json", "r", encoding="utf-8") as f:
        albero = json.load(f)
    previous_parent_name = None
    previous_page_id = None
    crea_sub = True

    #Itero tra le risposte lette generate dal modello
    for risposta in risposte:
        nome_file = Path(risposta["file"]).resolve().parent.name#Risolvo il nome della cartella file /risposte/segnali/<file>.json -> segnali
        print(f"Elaborando la risposta : {nome_file}")
        testo = risposta["data"]#tiro fuori il testo dalla rispota
        subpages = crea_subpages(testo)#Crea le subpages partendo dal testo

        if previous_parent_name == nome_file:#controllo se la risposta precedente è nella stessa cartella
            #flag per capire se una pagina deve essere creata
            #print(f"Subpages : {subpages}")
            page_id = previous_page_id
        else :
            crea_sub = True
            try:
                page_id = trova_id(nome_file, albero)
            except KeyError as e:
                page_id = crea_pagina_fallback(notion, nome_file, None)
                #print(f"nome assente nel database : {e}")
                #print(f"Impossibile salvare : {risposta['file']}")

        

        for subpage in subpages:
            if crea_sub:
                page_id = carica_su_notion(page_id, subpage, notion, crea_sub)
                crea_sub = False
            else:
                carica_su_notion(page_id, subpage, notion, crea_sub)

        previous_parent_name = nome_file
        previous_page_id = page_id
def ordina_risposte(risposte: list[dict])->list[dict]:
    risposte.sort(key=lambda x: Path(x["file"]).resolve().parent)
    return risposte

def crea_pagina_fallback(notion: Client, titolo: str, parent_id: str | None = None) -> str:
    """
    Crea una pagina in Notion.
    - Se parent_id è noto -> crea la pagina sotto quel parent.
    - Se parent_id è None -> crea la pagina nel workspace (pagina di primo livello).
    Ritorna l'ID della nuova pagina.
    """

    if parent_id is not None:
        parent = {"page_id": parent_id}

    else:
        # Fallback: crea la pagina direttamente nel workspace dell'integrazione
        parent = {"type": "workspace", "workspace": True}

    page = notion.pages.create(
        parent=parent,
        properties={
            "title": {
                "title": [
                    {
                        "text": {
                            "content": titolo
                        }
                    }
                ]
            }
        }
    )

    return page["id"]

def trova_id(titolo: str, data, debug: bool = False) -> str | None:
    if isinstance(data, list):
        for nodo in data:
            if debug:
                print(f"sto cercando in {nodo.get('titolo')}")
            result = trova_id(titolo, nodo, debug=debug)
            if result is not None:
                return result
        return None

    if isinstance(data, dict):
        if debug:
            print(f"sto cercando in {data.get('titolo')}")
        if data.get("titolo") == titolo:
            return data.get("id")

        for child in data.get("children", []):
            result = trova_id(titolo, child, debug=debug)
            if result is not None:
                return result

        return None

    return None



def carica_su_notion(page_id: str, content: SubPage,notion: Client,crea_sub : bool):
    """
    Crea una sottopagina in Notion dentro page_id e ci inserisce:
        - titolo
        - descrizione
        - contenuto (testo / equazioni latex)
    """
    #print(f"Il titolo è : {content.titolo}")
    #print(f"Il contenuto è : {content.contenuto}")

    # 1️⃣ CREA LA SUBPAGE
    if crea_sub :
        nuova_pagina = notion.pages.create(
        parent={"page_id": page_id},
        properties={
            "title": [
                {
                    "type": "text",
                    "text":  {"content" : content.get_titolo()}
                    }
                ]
            }
        )
         
        nuova_id = nuova_pagina["id"]
        if content.get_contenuto():
            notion.blocks.children.append(
            block_id=nuova_id,
            children=content.get_contenuto()
        )
    else :
        nuova_id = page_id
        titolo = content.get_titolo()
        title_block = {
            "object": "block",
            "type": "heading_3",
            "heading_3": {
                "rich_text": 
                         text_to_rich_text(titolo) 
                ,
                "is_toggleable": False
            }
        }
        content.get_contenuto().insert(0, title_block)

        if content.get_contenuto():
            notion.blocks.children.append(
                block_id=nuova_id,
                children=content.get_contenuto()
            )
    #print(f"Creata subpage: {content.get_titolo()} (id: {nuova_id})")
    #print(content.get_contenuto())

    # invio i blocchi in Notion
   
    return nuova_id



def leggi_risposte() ->list[dict]:
    """ Serve per leggere la caretella risposte"""
    testi = []

    for file in esplora_json():
        with open(file, "r", encoding="utf-8") as f:
            data = json.load(f)
            testi.append({"file":file,"data":data["message"]["content"]})
    return testi
def elimina_risposte():
    """Elimina tutti i file PDF nella directory data/pdf e nelle sue sotto directory.
    
    Returns:
        None"""

    for file in esplora_json():
        os.remove(file)
        print(f"Eliminato: {file}")
        
def crea_subpages(testo:str)->list[SubPage]:
    indici = separa_sub_pages(testo)
    subpages = []

    for i  in range(len(indici)-1):
        subpages.append(SubPage(testo[indici[i]:indici[i+1]]))
    
    if indici:
            subpages.append(SubPage(testo[indici[-1]:]))
    return subpages


def separa_sub_pages(testo: str) -> list[int]:
    indici = []
    i = 0

    while True:
        pos = trova_titolo(testo, i)
        if pos == -1:
            break
        indici.append(pos)   # se vuoi dopo '### ' fai: pos + 4
        i = pos + 4          # ricomincia la ricerca dopo questo titolo

    return indici


def trova_titolo(testo:str,indice:int):
    return testo.find("### ",indice)

if __name__ == "__main__":
    inserisci_appunti()
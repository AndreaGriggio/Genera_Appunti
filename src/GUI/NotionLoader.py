
import os 
from pathlib import Path
from src.GUI.config import DATAPATH,NOTION_TOKEN
from src.GUI.NotionParser import NotionParser
from notion_client import Client


import json
# L'obbiettivo della classe è gestire il caricamente delle risposte non caricate
# Quindi dipende dalla risposta di Gemini
class NotionLoader:
    def __init__(self):
        self.parser = NotionParser()
        self.client = Client(auth=NOTION_TOKEN)
        self.history = Path(DATAPATH) / "history_loaded.json"
        
        # Crea il file history_loaded.json se non esiste
        if not self.history.exists():
            with open(self.history, "w", encoding="utf-8") as f:
                json.dump([], f)
                
        self.content = None
        self.is_json = False
        self.is_txt = False
    
    def load(self,answer_path:Path)->bool:
        
        if not answer_path: #Se nullo ritorno False impossibile caricare
            print("Il file non esiste")
            return False
        
        answer_path = self.change_suffix_json(answer_path)

        if answer_path.exists(): #Se non esiste ritorno False impossibile caricare
            self.is_json = True
            self.is_txt = False
        
        else:
            answer_path = self.change_suffix_txt(answer_path)

            if answer_path.exists(): #Se non esiste ritorno False impossibile caricare
                self.is_txt = True
                self.is_json = False
            else :
                return False


    
        risposta_name = answer_path.name #prendo il nome della risposta da caricare


        storia  = self.get_history()

        for name in storia: #Se sta già all'interno delle risposte processate allora non si processa
            if name == risposta_name:
                print("Gia caricata!")
                return False
            
        self.content = self.get_file(answer_path)

        if self.content is None:
            print("Problemi nel caricamento della risposta")
            return False
        
        page_title ,blocks = self.parser.parse(self.content, self.is_json)     

        if not blocks:
            print("Problemi nel parsing della risposta")
            return False   
        
        id = self.get_notion_id(answer_path.parent)
        if not id:
            print(f"❌ Impossibile trovare l'ID della pagina Notion per {risposta_name}.")
            return False

        success = self.create_page_and_upload(id, page_title, blocks)


        if success:
            self.update_history(risposta_name)
            print(f"✅ File {risposta_name} caricato con successo!")
            return True
            
        return False
    

    def change_suffix_json(self,name:Path)->Path:
        return name.with_suffix(".json")
    def change_suffix_txt(self,name:Path)->Path:
        return name.with_suffix(".txt")
    def get_history(self)->list[str]:
        try:
            with open(self.history, "r", encoding="utf-8") as f:
                l = json.load(f)
                return l
        except (json.JSONDecodeError, FileNotFoundError):
            return []
            
    def update_history(self,name:str):
        l = self.get_history()
        if name not in l:
            l.append(name)
            
            with open(self.history, "w", encoding="utf-8") as f:
                json.dump(l, f, indent=4)
        
        
    def get_notion_id(self, folder_path: Path) -> str | None:
        """Cerca il file .id nella cartella e ne estrae il contenuto."""
        id_file = folder_path / ".id"
        if id_file.exists():
            with open(id_file, "r", encoding="utf-8") as f:
                return f.read().strip()
        return None
    def get_file(self,answer_path:Path)->str:
        with open(answer_path, "r", encoding="utf-8") as f:
            return f.read()
    def create_page_and_upload(self, parent_id: str, title: str, blocks: list) -> bool:
        """Crea una nuova pagina figlia e vi inietta i blocchi a gruppi di 100."""
        try:
            # A) CREAZIONE PAGINA
            new_page = self.client.pages.create(
                parent={"page_id": parent_id},
                properties={
                    "title": {
                        "title": [{"type": "text", "text": {"content": title}}]
                    }
                }
            )
            
            new_page_id = new_page["id"]
            
            # B) CARICAMENTO BLOCCHI
            # Cicla i blocchi a fette di 100 (limite imposto da Notion)
            for i in range(0, len(blocks), 100):
                chunk = blocks[i:i + 100]
                self.client.blocks.children.append(
                    block_id=new_page_id,
                    children=chunk
                )
            return True
            
        except Exception as e:
            print(f"❌ Errore durante la creazione della pagina o l'upload dei blocchi: {e}")
            return False
if __name__ == "__main__":
    loader = NotionLoader()
    percorso = Path.cwd()/"src"/"GUI"/"Data"/"Corsi Università"/"Secondo Anno"/"Sistemi operativi"/"OS_L0-Introduction_appunti.json"
    print(percorso)
    if percorso.exists():
        loader.load(percorso)



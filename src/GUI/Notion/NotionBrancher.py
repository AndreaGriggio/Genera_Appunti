import json
import time #utilizzo solamente in time.sleep()
import threading
from pathlib import Path
from notion_client import Client
from notion_client.errors import APIResponseError
from concurrent.futures import ThreadPoolExecutor,as_completed
from src.GUI.config import DATAPATH, BASE_ID, NOTION_TOKEN

# Quante chiamate API girano contemporaneamente.
# Con threading.Thread non c'è più un pool fisso, quindi non c'è deadlock.
# Il semaforo limita solo le richieste HTTP verso Notion.
MAX_CONCURRENT_REQUESTS = 4
MAX_THREADS = 20


class NotionBrancher:
    def __init__(self):
        self.NOTION_TOKEN = NOTION_TOKEN
        self.BASE_ID = BASE_ID

        if not self.BASE_ID:
            self.BASE_ID = "2a68f1dee7b6807789d1ebd7e3a87fb0"

        if not self.NOTION_TOKEN:
            raise ValueError("NOTION_API_KEY non trovata nelle variabili d'ambiente.")

        self.client = Client(auth=self.NOTION_TOKEN)

        # Semaforo: al massimo MAX_CONCURRENT_REQUESTS thread fanno una
        # chiamata API contemporaneamente. Gli altri aspettano fuori dal
        # blocco "with self._sem" senza occupare risorse.
        # A differenza del pool fisso, i thread possono aspettare il
        # semaforo senza bloccare altri thread — niente deadlock.
        self._sem = threading.Semaphore(MAX_CONCURRENT_REQUESTS)
        self._executor = ThreadPoolExecutor(max_workers=MAX_THREADS)

    # ── API helpers ───────────────────────────────────────────────────────────

    def _safe_api_call(self, func, **kwargs):
        """Retry esponenziale per 429/5xx. Thread-safe: solo variabili locali."""
        tentativi = 0
        while tentativi < 5:
            try:
                return func(**kwargs)#è una funzione passata come oggetto
            #ritorna il risultato della funzione passata a safe_api_call
            except APIResponseError as e:
                if e.status in [500, 502, 503, 504, 429]:
                    wait = 2 ** tentativi
                    print(f"Errore Notion {e.status}. Riprovo tra {wait}s...")
                    time.sleep(wait)
                    tentativi += 1
                else:
                    raise
        raise Exception("Impossibile contattare Notion dopo vari tentativi.")

    def _get_child_pages(self, page_id: str) -> list[dict]:
        """
        Ritorna i figli diretti di una pagina.
        Il semaforo viene acquisito qui: è l'unico posto dove
        tocchiamo la rete, quindi è l'unico posto da limitare.
        """
        children = []
        cursor = None#serve per dire se una pagina a tantissimi blocchi
        #testo , equazioni, codice

        while True:
            params = {"block_id": page_id}
            if cursor:
                params["start_cursor"] = cursor

            # Il semaforo garantisce che al massimo MAX_CONCURRENT_REQUESTS
            # thread siano dentro questo blocco contemporaneamente.
            # Gli altri aspettano qui senza bloccare nient'altro.
            with self._sem:#viene decrementato è come un pool di thread che possono partire allo stesso momento 
                #se = 0 non partono thread nuovi e si aspetta quando un thread finisce stem++
                res = self._safe_api_call(self.client.blocks.children.list, **params)

            for b in res.get("results", []):
                if b["type"] == "child_page": #serve per ignorare tutti i blocchi contenuti nella risposta
                    children.append({
                        "id":           b["id"],
                        "titolo":       b["child_page"].get("title", "Senza Titolo"),
                        "has_children": b.get("has_children", False),
                    })

            if not res.get("has_more"):#se non ci sono altri blocchi si esce dal while sopra
                break
            cursor = res.get("next_cursor")#se ci sono più di 100 blocchi allora si prende il nuovo cursor e si ripete la richiesta

        return children

    # ── Cuore: thread diretti + semaforo ─────────────────────────────────────

    def _esplora(self, page_id: str, titolo: str, livello: int) -> dict:
        print(f"{'  ' * livello} {titolo}")
        children_info = self._get_child_pages(page_id)

        if not children_info:
            return {"id": page_id, "titolo": titolo, "livello": livello, "children": []}

        # Sottometti i figli all'executor condiviso (non crea thread illimitati)
        futures = {}
        for c in children_info:
            if c["has_children"]:
                future = self._executor.submit(
                    self._esplora, c["id"], c["titolo"], livello + 1
                )
                futures[c["id"]] = future

        # Attendi i risultati
        results = {}
        for child_id, future in futures.items():
            try:
                results[child_id] = future.result(timeout=60)
            except Exception as e:
                print(f"Errore nodo {child_id}: {e}")
                results[child_id] = {
                    "id": child_id, "titolo": "Errore",
                    "livello": livello + 1, "children": []
                }

        children_nodes = []
        for c in children_info:
            if c["has_children"]:
                children_nodes.append(results[c["id"]])
            else:
                children_nodes.append({
                    "id": c["id"], "titolo": c["titolo"],
                    "livello": livello + 1, "children": []
                })

        return {"id": page_id, "titolo": titolo, "livello": livello, "children": children_nodes}


    # ── Entry point ───────────────────────────────────────────────────────────

    def get_notion_branching(self):
        print(f"Inizio scansione da ID: {self.BASE_ID}")

        if not self.BASE_ID:
            raise ValueError("BASE_ID non è definito.")

        # Una sola pages.retrieve — solo per il titolo della root
        try:
            with self._sem:
                root_page = self._safe_api_call(
                    self.client.pages.retrieve, page_id=self.BASE_ID
                )
            titoli = root_page.get("properties", {}).get("title", {}).get("title", [])
            root_titolo = titoli[0].get("plain_text", "Root") if titoli else "Root"
            risultato = self._esplora(self.BASE_ID, root_titolo, 0)
        except Exception:
            root_titolo = "Root"
        self._executor.shutdown(wait=False) 
        
        
        output_path = Path(DATAPATH) / "dict_notion.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(risultato, f, indent=4, ensure_ascii=False)

        print(f"Albero salvato in: {output_path}")


if __name__ == "__main__":
    try:
        brancher = NotionBrancher()
        brancher.get_notion_branching()
    except Exception as e:
        print(f" Errore fatale: {e}")
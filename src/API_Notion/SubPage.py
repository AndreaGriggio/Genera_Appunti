from markdown_it import MarkdownIt
from .utils import build_equation, build_list_block, build_paragraph, build_quote, build_code
import unicodedata
# Parser Markdown condiviso
MD = MarkdownIt("commonmark").enable("table")
import re
from pathlib import Path

EQ_PATTERN = re.compile(r"\\\[(.*?)\\\]", re.DOTALL)

def split_text_and_equations(text: str):
    blocks = []
    pos = 0
    for m in EQ_PATTERN.finditer(text):
        before = text[pos:m.start()].testoip()
        if before:
            blocks.append(("testo", before))
        expr = m.group(1).testoip()
        if expr:
            blocks.append(("equazione", expr))
        pos = m.end()
    tail = text[pos:].testoip()
    if tail:
        blocks.append(("testo", tail))
    return blocks
def pulisci_testo_subpage(testo: str) -> str:
    # 1. rimuovi caratteri unicode non stampabili
    testo = "".join(c for c in testo if c.isprintable())

    # 2. normalizza unicode (per evitare caratteri testoani tipo ZERO-WIDTH)
    testo = unicodedata.normalize("NFKC", testo)

    # 3. gestisci le '|' → tieni solo la prima, elimina tutte le altre
    first_pipe = testo.find('|')
    if first_pipe != -1:
        # tieni parte fino alla prima |
        cleaned = testo[:first_pipe+1]
        # togli tutte le altre | dal resto
        cleaned += testo[first_pipe+1:].replace("|", "")
        testo = cleaned

    return testo
class SubPage:
    def __init__(self, testo: str):
        if testo is None:
            self.titolo = []
            self.contenuto = []
        else:
            self.inizializza(testo)
            # prima parsiamo in testouttura logica
            self.contenuto = self.parse_testo()
            # poi convertiamo in blocchi Notion
            self.contenuto = self.to_notion_blocks()

    def inizializza(self, testo: str) -> None:
        i_titolo = testo.find("### ")
        f_titolo = testo.find("\n")
        self.titolo = testo[i_titolo + 4:f_titolo].strip()
        self.contenuto = testo[f_titolo + 1:]  # solo il body, senza titolo

    def parse_Contenuto(self) -> list[dict]:

        testo = pulisci_testo_subpage(self.contenuto)
        blocchi: list[dict] = []

        tokens = MD.parse(testo)
        i = 0
        n = len(tokens)

        # massimo 1 quote per subpage
        quote_added = False

        while i < n:
            tok = tokens[i]

            # Paragrafo
            if tok.type == "paragraph_open":
                inline = tokens[i + 1]
                text = inline.content.testoip()

                for tipo, contenuto in split_text_and_equations(text):
                    if tipo == "equazione":
                        blocchi.append({
                            "tipo": "equazione",
                            "contenuto": contenuto
                        })
                    else:
                        blocchi.append({
                            "tipo": "testo",
                            "contenuto": contenuto
                        })

                i += 3  # paragraph_open, inline, paragraph_close
                continue

            # Blocchi codice: ```lang ... ```
            if tok.type == "fence":
                lang = tok.info.testoip() if tok.info else "plain text"
                code = tok.content.rtestoip("\n")
                blocchi.append({
                    "tipo": "codice",
                    "linguaggio": lang,
                    "contenuto": code
                })
                i += 1
                continue

            # Liste puntate
            if tok.type == "bullet_list_open":
                i += 1
                while i < n and tokens[i].type != "bullet_list_close":
                    if tokens[i].type == "list_item_open":
                        # cerco l'inline dell'item
                        j = i + 1
                        while j < n and tokens[j].type != "inline":
                            j += 1

                        if j < n and tokens[j].type == "inline":
                            item_text = tokens[j].content

                            # rompo item_text in blocchi testo/equazioni
                            blocks_item = split_text_and_equations(item_text)

                            first_text_as_list = True
                            for tipo, contenuto in blocks_item:
                                if tipo == "equazione":
                                    blocchi.append({
                                        "tipo": "equazione",
                                        "contenuto": contenuto
                                    })
                                else:
                                    # la prima parte di testo dell'item -> "lista"
                                    if first_text_as_list:
                                        blocchi.append({
                                            "tipo": "lista",
                                            "contenuto": contenuto
                                        })
                                        first_text_as_list = False
                                    else:
                                        blocchi.append({
                                            "tipo": "testo",
                                            "contenuto": contenuto
                                        })

                        # salta fino al list_item_close
                        while i < n and tokens[i].type != "list_item_close":
                            i += 1

                    i += 1
                i += 1  # salta bullet_list_close
                continue

            # Citazioni (quote) -> al massimo UNA per subpage
            if tok.type == "blockquote_open":
                # pattern: blockquote_open, paragraph_open, inline, paragraph_close, blockquote_close
                inline = tokens[i + 2]
                quote_text = inline.content.testoip()
                quote_text = quote_text.replace("|", " ")

                if not quote_added:
                    blocchi.append({
                        "tipo": "descrizione",
                        "contenuto": quote_text
                    })
                    quote_added = True
                else:
                    # ulteriori quote: le tratto come testo normale
                    blocchi.append({
                        "tipo": "testo",
                        "contenuto": quote_text
                    })

                i += 5
                continue

            # Tabelle: le IGNORIAMO (niente più casino)
            if tok.type == "table_open":
                # salta tutto fino a table_close
                while i < n and tokens[i].type != "table_close":
                    i += 1
                i += 1
                continue

            # qualsiasi altra cosa la saltiamo
            i += 1

        return blocchi

    def find_lista(self, testo: str, start: int) -> dict | None:
        if start == -1:
            return None

        end = testo.find("\n", start)
        if end == -1:
            end = len(testo)

        return {
            "tipo": "lista",
            "contenuto": testo[start+2:end],   # salta "- "
            "newtesto": testo[end+1:],         # vai alla riga dopo
        }
    def find_descrizione(self, testo: str, start: int) -> dict | None:
        if start == -1:
            return None

        end = testo.find("\n", start)
        if end == -1:
            end = len(testo)

        return {
            "tipo": "descrizione",
            "contenuto": testo[start+2:end],   # salta "| "
            "newtesto": testo[end+1:],
        }
    def find_testo(self, testo: str) -> dict | None:
        end = testo.find("\n")
        if end == -1:
            if not testo.strip():
                return None
            return {
                "tipo": "testo",
                "contenuto": testo.strip(),
                "newtesto": "",
            }

        return {
            "tipo": "testo",
            "contenuto": testo[:end],
            "newtesto": testo[end+1:],
        }

    def find_equazione(self, testo: str, start: int) -> dict | None:
        if start == -1:
            return None

        end = testo.find("\\]", start)
        if end == -1:
            return None

        return {
            "tipo": "equazione",
            "contenuto": testo[start+3:end],
            "newtesto": testo[end+3:],
        }

    def find_codice(self, testo: str, start: int) -> dict | None:
        if start == -1:
            return None

        end = testo.find("```", start+3)
        if end == -1:
            return None

        lang_end = testo.find(" ", start+3)
        if lang_end == -1 or lang_end > end:
            lang_end = end

        return {
            "tipo": "codice",
            "contenuto": testo[start+3:end],
            "lang": testo[start+3:lang_end],
            "newtesto": testo[end+3:],
        }  
    def _find_marker_line(self, testo: str, prefix: str) -> int:
        idx = testo.find(prefix)
        while idx != -1:
            if idx == 0 or testo[idx-1] == "\n":
                return idx
            idx = testo.find(prefix, idx+1)
        return -1

    def starters(self, testo: str) -> list[dict]:
        return [
            {"indice": self._find_marker_line(testo, "| "),  "tipo": "descrizione"},
            {"indice": testo.find("\\["),                    "tipo": "equazione"},
            {"indice": self._find_marker_line(testo, "- "),  "tipo": "lista"},
            {"indice": testo.find("```"),                    "tipo": "code"},
        ]

    def parse_testo(self) -> list[dict]:
        testo = self.contenuto
        blocchi: list[dict] = []

        while True:
            elem = None
            indici = self.starters(testo)

            # tieni solo gli indici validi
            validi = [idx for idx in indici if idx["indice"] != -1]

            # nessun marker trovato → fine parsing, esco dal while
            if not validi:
                break

            # prendo il marker più a sinistra
            prossimo = min(validi, key=lambda x: x["indice"])
            start = prossimo["indice"]
            tipo = prossimo["tipo"]

            if tipo == "descrizione":
                elem = self.find_descrizione(testo, start)
            elif tipo == "equazione":
                elem = self.find_equazione(testo, start)
            elif tipo == "lista":
                elem = self.find_lista(testo, start)
            elif tipo == "code":
                elem = self.find_codice(testo, start)
            else:
                elem = self.find_testo(testo)

            # se per qualche motivo il parser del blocco fallisce,
            # tratto tutto il resto come testo e chiudo
            if elem is None:
                if testo.strip():
                    blocchi.append({
                        "tipo": "testo",
                        "contenuto": testo.strip()
                    })
                break

            blocchi.append(elem)
            testo = elem["newtesto"]

            if not testo:
                break

        # residuo finale di testo “normale”
        if testo.strip():
            blocchi.append({
                "tipo": "testo",
                "contenuto": testo.strip()
            })

        return blocchi

               
                
                


    def to_notion_blocks(self) -> list[dict]:
        blocchi = []
        for elem in self.contenuto:
            tipo = elem["tipo"]

            if tipo == "descrizione":
                blocchi.append(build_quote(elem))
            elif tipo == "testo":
                blocchi.append(build_paragraph(elem))
            elif tipo == "equazione":
                blocchi.append(build_equation(elem))
            elif tipo == "lista":
                blocchi.append(build_list_block(elem))
            elif tipo == "codice":
                blocchi.append(build_code(elem))
            elif tipo == "tabella":
                # qui devi decidere tu come convertire una tabella
                # per ora la puoi lasciare fuori oppure implementare un build_table(...)
                pass

        return blocchi

        
    def get_titolo(self) -> str:
        return self.titolo

    def get_contenuto(self) -> list[dict]:
        return self.contenuto

    def set_titolo(self, titolo):
        self.titolo = titolo

    def set_contenuto(self, contenuto):
        self.contenuto = contenuto
if __name__ == "__main__" :
    testo ="### Titolo di provo\n | Un paragrafo normale.\n- Punto uno\n- Punto due \n \\[equazione 1 = 2+t \\]\n"

    subpage = SubPage(testo)
    print(subpage.get_titolo())
    print(subpage.get_contenuto())
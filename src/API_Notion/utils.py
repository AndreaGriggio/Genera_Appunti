from notion_client import Client

def build_equation(blocco : dict)-> dict :
    return {
            "object": "block",
            "type": "equation",
            "equation": {
                "expression": blocco["contenuto"]
            }
        }
    
def build_quote(blocco : dict)-> dict :
    return {
        "object": "block",
        "type": "quote",
        "quote": {
            "rich_text": text_to_rich_text(blocco["contenuto"]),
        }
    }

def build_paragraph(blocco : dict)-> dict :
    return {
        "object" : "block",
        "type" : "paragraph",
        "paragraph":{
            "rich_text" : text_to_rich_text(blocco["contenuto"])
        }
    }

def build_list_block(blocco:dict)->dict :
    return {
        "object": "block",
        "type": "bulleted_list_item",
        "bulleted_list_item": {
            "rich_text":text_to_rich_text(blocco["contenuto"])
            }
        }
def build_code(blocco: dict) -> dict:
    """
    blocco:
      - "contenuto": codice come stringa (anche multilinea)
      - "linguaggio": opzionale, es. "vhdl", "python", ecc.
    """
    codice = blocco.get("contenuto", "")
    linguaggio = blocco.get("linguaggio", "plain text")

    return {
        "object": "block",
        "type": "code",
        "code": {
            "language": linguaggio,
            "rich_text": [
                {
                    "type": "text",
                    "text": {
                        "content": codice
                    }
                }
            ]
        }
    }
def build_tabella(blocco: dict) -> dict:
    """
    blocco:
      - "righe": lista di righe, ogni riga è lista di celle (stringhe)
    """
    righe = blocco.get("righe", [])

    # larghezza = massimo numero di celle tra le righe
    table_width = max((len(r) for r in righe), default=0)

    # costruisci le righe Notion
    children_rows = []
    for riga in righe:
        # pad con celle vuote se riga più corta del massimo
        celle = list(riga) + [""] * (table_width - len(riga))

        cells_rich = []
        for cell in celle:
            cells_rich.append([
                {
                    "type": "text",
                    "text": {
                        "content": cell
                    }
                }
            ])

        children_rows.append({
            "object": "block",
            "type": "table_row",
            "table_row": {
                "cells": cells_rich
            }
        })

    return {
        "object": "block",
        "type": "table",
        "table": {
            "table_width": table_width,
            "has_column_header": True,   # se vuoi considerare la prima riga come header
            "has_row_header": False
        },
        "children": children_rows
    }


def text_to_rich_text(text: str):
    """
    Converte una stringa in una lista di rich_text Notion.
    Supporta:
      - **grassetto**
      - \(equazioni in linea\)
    """
    spans = []
    buffer = []
    bold = False
    i = 0
    n = len(text)

    def flush_buffer():
        nonlocal buffer, bold, spans
        if not buffer:
            return
        spans.append({
            "type": "text",
            "text": {"content": "".join(buffer)},
            "annotations": {
                "bold": bold,
                "italic": False,
                "strikethrough": False,
                "underline": False,
                "code": False,
                "color": "default"
            }
        })
        buffer = []

    while i < n:
        ch = text[i]

        # 1) **grassetto**
        if ch == '*' and i + 1 < n and text[i+1] == '*':
            flush_buffer()
            bold = not bold
            i += 2
            continue

        # 2) \( equazione in linea \)
        if ch == '\\' and i + 1 < n and text[i+1] == '(':
            # chiudi eventuale testo prima
            flush_buffer()
            i += 2  # salta "\("

            # accumula fino a "\)"
            eq_buffer = []
            while i < n:
                if text[i] == '\\' and i + 1 < n and text[i+1] == ')':
                    i += 2  # salta "\)"
                    break
                eq_buffer.append(text[i])
                i += 1

            expr = "".join(eq_buffer).strip()
            if expr:
                spans.append({
                    "type": "equation",
                    "equation": {"expression": expr}
                })
            continue

        # 3) carattere normale
        buffer.append(ch)
        i += 1

    # flush finale
    flush_buffer()

    # se proprio non c’è niente, evita lista vuota
    if not spans:
        spans.append({
            "type": "text",
            "text": {"content": ""},
            "annotations": {
                "bold": False,
                "italic": False,
                "strikethrough": False,
                "underline": False,
                "code": False,
                "color": "default"
            }
        })

    return spans

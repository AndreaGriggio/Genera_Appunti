"""
NotionSchema.py
---------------
Unica fonte di verità per la struttura JSON che Gemini deve produrre
e che NotionParser deve consumare.

Regola: se aggiungi un BlockType, aggiungi il metodo corrispondente
in NotionParser. Non devi toccare nient'altro.
"""

from __future__ import annotations
from enum import Enum
from pydantic import BaseModel, Field


# ── Tipi di blocco consentiti ─────────────────────────────────────────────────

class BlockType(str, Enum):
    paragraph          = "paragraph"
    heading_3          = "heading_3"
    bulleted_list_item = "bulleted_list_item"
    numbered_list_item = "numbered_list_item"
    code               = "code"
    table              = "table"
    quote              = "quote"
    equation           = "equation"

# ── Blocco singolo (schema piatto compatibile con Gemini) ─────────────────────

class NotionBlock(BaseModel):
    type: BlockType = Field(
        description=(
            "Tipo di blocco Notion da usare. Istruzioni di scelta:\n"
            "- 'heading_3'          → titolo di sezione o sotto-argomento\n"
            "- 'paragraph'          → testo espositivo normale\n"
            "- 'bulleted_list_item' → elemento di lista non ordinata\n"
            "- 'numbered_list_item' → elemento di lista numerata o procedura passo-passo\n"
            "- 'code'               → snippet di codice, comandi terminale, pseudocodice\n"
            "- 'table'              → dati con righe e colonne (es. confronti, tabelle)\n"
            "- 'quote'              → definizione da inseriro dopo ogni heading per spiegare brevemente il paragrafo\n"
            "- 'equation'           → equazione standalone centrata su riga propria\n"
            "Non usare MAI tipi non presenti in questa lista.\n"
        )
    )

    # Usato da: paragraph, heading_3, bulleted_list_item, numbered_list_item, callout
    text: str | None = Field(
        default=None,
        description=(
            "Testo del blocco. Obbligatorio per tutti i tipi tranne 'code' e 'table'. "
            "Può contenere **grassetto** e $equazione inline$. "
            "Per equazioni-standalone invece utilizza Katek puro"
        )
    )

    # Usato da: code
    language: str | None = Field(
        default=None,
        description=(
            "Linguaggio di programmazione. Obbligatorio se type è 'code'. "
            "Esempi: 'python', 'java', 'bash', 'c', 'cpp', 'sql'. "
            "Usa stringa vuota '' se il linguaggio non è rilevabile."
        )
    )
    code: str | None = Field(
        default=None,
        description="Contenuto del blocco codice. Obbligatorio se type è 'code'."
    )

    # Usato da: table
    headers: list[str] | None = Field(
        default=None,
        description="Intestazioni delle colonne. Obbligatorio se type è 'table'."
    )
    rows: list[list[str]] | None = Field(
        default=None,
        description=(
            "Righe della tabella. Ogni elemento è una lista di stringhe (celle). "
            "Obbligatorio se type è 'table'. "
            "Il numero di celle per riga deve corrispondere al numero di headers."
        )
    )


# ── Documento radice ──────────────────────────────────────────────────────────

class NotionDocument(BaseModel):
    title: str = Field(
        description="Titolo principale del documento o della lezione. Stringa semplice, senza #."
    )
    blocks: list[NotionBlock] = Field(
        description=(
            "Lista PIATTA di tutti i blocchi del documento, in ordine di lettura. "
            "Non annidare blocchi dentro altri blocchi. "
            "Usa heading_3 per separare le sezioni tematiche."
        )
    )
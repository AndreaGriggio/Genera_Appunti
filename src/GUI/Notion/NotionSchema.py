"""
NotionSchema.py
---------------
Unica fonte di verità per la struttura JSON che Gemini deve produrre
e che NotionParser deve consumare.

Struttura attesa da Gemini:
{
    "title": "Titolo documento",
    "blocks": [
        {"type": "heading_3", "text": "Concetto principale"},
        {"type": "quote",     "text": "Definizione sintetica del concetto"},
        {"type": "paragraph", "text": "Spiegazione estesa..."},
        ...
    ]
}

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


# ── Blocco singolo ────────────────────────────────────────────────────────────

class NotionBlock(BaseModel):
    type: BlockType = Field(
        description=(
            "Tipo di blocco Notion da usare. Istruzioni di scelta:\n"
            "- 'heading_3'          → titolo del concetto o sotto-argomento\n"
            "- 'quote'              → definizione sintetica del concetto (segue sempre heading_3)\n"
            "- 'paragraph'          → spiegazione discorsiva, ragionamenti, connessioni logiche\n"
            "- 'bulleted_list_item' → proprietà, caratteristiche, casi (NON copiare elenchi dal PDF)\n"
            "- 'numbered_list_item' → procedure, passi sequenziali, dimostrazioni\n"
            "- 'code'               → snippet di codice, comandi terminale, pseudocodice\n"
            "- 'table'              → confronti strutturati tra concetti\n"
            "- 'equation'           → formula matematica standalone\n"
            "Non usare MAI tipi non presenti in questa lista.\n"
        )
    )

    # Usato da: paragraph, heading_3, bulleted_list_item, numbered_list_item, quote, equation
    text: str | None = Field(
        default=None,
        description=(
            "Testo del blocco. Obbligatorio per tutti i tipi tranne 'code' e 'table'. "
            "Può contenere **grassetto** (termini tecnici) e $equazione inline$. "
            "Per equazioni standalone usa type 'equation' con LaTeX puro nel campo 'text'."
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
        description=(
            "Titolo sintetico degli appunti — NON il titolo del PDF originale. "
            "Deve descrivere il concetto centrale trattato."
        )
    )
    blocks: list[NotionBlock] = Field(
        description=(
            "Lista PIATTA di tutti i blocchi in ordine di lettura. "
            "Struttura attesa per ogni concetto: "
            "heading_3 → quote → [paragrafi/liste/equazioni/codice]. "
            "L'ultimo gruppo deve essere heading_3 'Punti chiave' "
            "seguito da bulleted_list_item con le 3-5 cose più importanti."
        )
    )
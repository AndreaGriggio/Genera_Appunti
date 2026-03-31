import re
from typing import Any
from pydantic import ValidationError

from src.GUI.NotionSchema import NotionDocument, NotionBlock, BlockType


class NotionParser:
    MAX_TEXT_LENGTH = 2000

    # ── Entry point ───────────────────────────────────────────────────────────

    def parse(self, content: str, is_json: bool) -> tuple[str, list[dict[str, Any]]]:
        """
        Punto di ingresso unico.
        - is_json=True  → parsing strutturato via NotionDocument (Gemini con JSON mode)
        - is_json=False → fallback Markdown per modelli Gemma
        """
        if is_json:
            return self._parse_document(content)
        else:
            return "Appunti Generici", self._parse_markdown_fallback(content)

    # ── Parsing strutturato (JSON mode) ──────────────────────────────────────

    def _parse_document(self, content: str) -> tuple[str, list[dict[str, Any]]]:
        """
        Valida il JSON con Pydantic e converte ogni blocco.
        Se la validazione fallisce, logga l'errore e restituisce lista vuota.
        """
        try:
            doc = NotionDocument.model_validate_json(content)
        except ValidationError as e:
            print(f"JSON non conforme allo schema NotionDocument:\n{e}")
            return "Senza Titolo", []
        except Exception as e:
            print(f"Errore di parsing JSON generico: {e}")
            return "Senza Titolo", []

        blocks: list[dict[str, Any]] = []

        # Heading 2 con il titolo del documento (blocco introduttivo in Notion)
        blocks.append(self.create_heading_2(doc.title))

        for b in doc.blocks:
            notion_block = self._dispatch(b)
            if notion_block is not None:
                blocks.append(notion_block)

        return doc.title, blocks

    def _dispatch(self, b: NotionBlock) -> dict[str, Any] | None:
        """
        Switch sul tipo di blocco. 
        Se aggiungi un BlockType in NotionSchema.py, aggiungi il case qui.
        """
        match b.type:
            case BlockType.paragraph:
                return self.create_paragraph(b.text or "")

            case BlockType.heading_3:
                return self.create_heading_3(b.text or "")

            case BlockType.bulleted_list_item:
                return self.create_bulleted_list_item(b.text or "")

            case BlockType.numbered_list_item:
                return self.create_numbered_list_item(b.text or "")
            case BlockType.quote:
                return self.create_quote(b.text or "")
            case BlockType.code:
                if not b.code:
                    print(f"Blocco 'code' senza campo 'code', ignorato.")
                    return None
                return self.create_code_block(b.code, b.language or "")
            case BlockType.equation:
                return self.create_equation_block(b.text or " ")
            case BlockType.table:
                if not b.headers or not b.rows:
                    print(f"Blocco 'table' senza headers o rows, ignorato.")
                    return None
                return self.create_table(b.headers, b.rows)


            case _:
                print(f"Tipo blocco sconosciuto '{b.type}', ignorato.")
                return None

    # ── Creatori di blocchi Notion API ────────────────────────────────────────

    def create_heading_2(self, text: str) -> dict[str, Any]:
        return {
            "object": "block",
            "type": "heading_2",
            "heading_2": {"rich_text": self._parse_rich_text(text)}
        }

    def create_heading_3(self, text: str) -> dict[str, Any]:
        return {
            "object": "block",
            "type": "heading_3",
            "heading_3": {"rich_text": self._parse_rich_text(text)}
        }

    def create_paragraph(self, text: str) -> dict[str, Any]:
        return {
            "object": "block",
            "type": "paragraph",
            "paragraph": {"rich_text": self._parse_rich_text(text)}
        }

    def create_bulleted_list_item(self, text: str) -> dict[str, Any]:
        return {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {"rich_text": self._parse_rich_text(text)}
        }

    def create_numbered_list_item(self, text: str) -> dict[str, Any]:
        return {
            "object": "block",
            "type": "numbered_list_item",
            "numbered_list_item": {"rich_text": self._parse_rich_text(text)}
        }

    def create_code_block(self, code: str, language: str) -> dict[str, Any]:
        # Notion accetta solo linguaggi specifici; se sconosciuto manda stringa vuota
        NOTION_LANGUAGES = {
            "abap", "arduino", "bash", "basic", "c", "clojure", "coffeescript",
            "cpp", "csharp", "css", "dart", "diff", "docker", "elixir", "elm",
            "erlang", "flow", "fortran", "fsharp", "gherkin", "glsl", "go",
            "graphql", "groovy", "haskell", "html", "java", "javascript", "json",
            "julia", "kotlin", "latex", "less", "lisp", "livescript", "lua",
            "makefile", "markdown", "markup", "matlab", "mermaid", "nix",
            "objective-c", "ocaml", "pascal", "perl", "php", "plain text",
            "powershell", "prolog", "protobuf", "python", "r", "reason",
            "ruby", "rust", "sass", "scala", "scheme", "scss", "shell",
            "sql", "swift", "typescript", "vb.net", "verilog", "vhdl",
            "visual basic", "webassembly", "xml", "yaml", "java/c/c++/c#",
        }
        safe_lang = language.lower() if language.lower() in NOTION_LANGUAGES else "plain text"
        return {
            "object": "block",
            "type": "code",
            "code": {
                "rich_text": [{"type": "text", "text": {"content": code[:self.MAX_TEXT_LENGTH]}}],
                "language": safe_lang,
            }
        }

    def create_table(self, headers: list[str], rows: list[list[str]]) -> dict[str, Any]:
        """
        Notion vuole le tabelle con table_width e una lista di table_row children.
        Nota: le tabelle Notion non supportano rich_text nelle celle, solo testo semplice.
        """
        col_count = len(headers)

        # Riga di intestazione
        header_row = {
            "object": "block",
            "type": "table_row",
            "table_row": {
                "cells": [[{"type": "text", "text": {"content": h[:self.MAX_TEXT_LENGTH]}}]
                          for h in headers]
            }
        }

        # Righe dati — normalizza il numero di celle
        data_rows = []
        for row in rows:
            # Padding/trim per allineare al numero di colonne
            normalized = (row + [""] * col_count)[:col_count]
            data_rows.append({
                "object": "block",
                "type": "table_row",
                "table_row": {
                    "cells": [[{"type": "text", "text": {"content": cell[:self.MAX_TEXT_LENGTH]}}]
                              for cell in normalized]
                }
            })

        return {
            "object": "block",
            "type": "table",
            "table": {
                "table_width": col_count,
                "has_column_header": True,
                "has_row_header": False,
                "children": [header_row] + data_rows,
            }
        }
    def create_quote(self, text: str) -> dict[str, Any]:
        return {
            "object": "block",
            "type": "quote",
            "quote": {"rich_text": self._parse_rich_text(text)}
        }


    def create_divider(self) -> dict[str, Any]:
        return {"object": "block", "type": "divider", "divider": {}}
    def create_equation_block(self, expression: str) -> dict:
        return {
            "object": "block",
            "type": "equation",
            "equation": {
                "expression": expression  # solo LaTeX puro, senza $ o $$
            }
        }
    # ── Rich text inline (grassetto + equazioni) ──────────────────────────────

    def _parse_rich_text(self, text: str) -> list[dict[str, Any]]:
        """
        Scompone il testo per trovare **grassetto** e $equazione inline$.
        Le equazioni a blocco ($$...$$) vengono trattate come inline qui
        perché sono già state gestite a livello di blocco da Gemini.
        """
        rich_text = []
        parts = re.split(r'(\*\*.*?\*\*|\$\$.*?\$\$|\$.*?\$)', text)

        for part in parts:
            if not part:
                continue

            if part.startswith("**") and part.endswith("**"):
                rich_text.append({
                    "type": "text",
                    "text": {"content": part[2:-2][:self.MAX_TEXT_LENGTH]},
                    "annotations": {"bold": True}
                })
            elif part.startswith("$$") and part.endswith("$$"):
                rich_text.append({
                    "type": "equation",
                    "equation": {"expression": part[2:-2].strip()}
                })
            elif part.startswith("$") and part.endswith("$"):
                rich_text.append({
                    "type": "equation",
                    "equation": {"expression": part[1:-1].strip()}
                })
            else:
                rich_text.append({
                    "type": "text",
                    "text": {"content": part[:self.MAX_TEXT_LENGTH]}
                })

        return rich_text if rich_text else [{"type": "text", "text": {"content": ""}}]

    # ── Fallback Markdown (solo per Gemma, no JSON mode) ─────────────────────

    def _parse_markdown_fallback(self, content: str) -> list[dict[str, Any]]:
        """
        Parser Markdown minimale per i modelli che non supportano JSON mode.
        Non ha la stessa affidabilità dello schema strutturato.
        """
        blocks = []
        in_math_block = False
        math_lines: list[str] = []

        for line in content.split('\n'):
            stripped = line.strip()

            # Blocchi math \[ ... \]
            if stripped == "\\[":
                in_math_block = not in_math_block
                if not in_math_block and math_lines:
                    blocks.append({
                        "object": "block", "type": "equation",
                        "equation": {"expression": "\n".join(math_lines)}
                    })
                    math_lines = []
                continue

            if in_math_block:
                math_lines.append(line)
                continue

            if not stripped:
                continue

            if stripped.startswith("# "):
                blocks.append(self.create_heading_2(stripped[2:]))
            elif stripped.startswith("## ") or stripped.startswith("### "):
                text = re.sub(r'^#+\s+', '', stripped)
                blocks.append(self.create_heading_3(text))
            elif stripped.startswith("- ") or stripped.startswith("* "):
                blocks.append(self.create_bulleted_list_item(stripped[2:]))
            elif re.match(r'^\d+\.\s', stripped):
                text = re.sub(r'^\d+\.\s+', '', stripped)
                blocks.append(self.create_numbered_list_item(text))
            else:
                blocks.append(self.create_paragraph(stripped))

        return blocks
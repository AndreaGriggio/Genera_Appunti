import json
import re
from typing import List, Dict, Any

class NotionParser:
    def __init__(self):
        self.MAX_TEXT_LENGTH = 2000

    def parse(self, content: str, is_json: bool) -> tuple[str, List[Dict[str, Any]]]:
        """
        Ritorna il Titolo della pagina e la lista dei blocchi da caricare.
        """
        if is_json:
            return self._parse_json_to_blocks(content)
        else:
            return "Appunti Generici", self._parse_markdown_to_blocks(content)

    def _parse_json_to_blocks(self, content: str) -> tuple[str, List[Dict[str, Any]]]:
        blocks = []
        page_title = "Senza Titolo"
        
        try:
            data = json.loads(content)
            
            # 1. Estraggo il Titolo (e creo il primo blocco Heading 2)
            if "title" in data:
                page_title = self._clean_title(data["title"])
                blocks.append(self.create_heading_2(page_title))
            
            # 2. Cerco l'array dei contenuti (Gemini lo chiama in vari modi, li copriamo)
            sections = data.get("sections") or data.get("notes") or data.get("content") or []
            
            # 3. Parso le sezioni
            if sections:
                blocks.extend(self.parse_section(sections))

            return page_title, blocks

        except json.JSONDecodeError as e:
            print(f"❌ Errore di decodifica JSON: {e}")
            return page_title, blocks
        
    def _clean_title(self,text:str)->str:
        return re.sub(r'^#+\s*','',text).strip()
    
    def parse_section(self, sections: list) -> List[Dict[str, Any]]:
        blocks = []
        for i,element in enumerate(sections):
            if not isinstance(element, dict):
                continue
            
            # Titolo della sezione diventa Heading 3
            heading = element.get("heading") or element.get("title")
            if heading:
                if i>0:
                    blocks.append(self.create_divider())
                blocks.append(self.create_heading_3(self._clean_title(heading)))
            
            # Contenuto della sezione
            content_lines = element.get("content") or element.get("points") or element.get("notes") or []
            
            for line in content_lines:
                if isinstance(line, str):
                    blocks.extend(self.parse_markdown_line(line))
                elif isinstance(line, dict):
                    # Se Gemini ha nidificato ancora (es. sotto-sezioni), ricorsione semplice
                    if "heading" in line or "title" in line:
                        blocks.extend(self.parse_section([line]))
                        
        return blocks

    def parse_markdown_line(self, line: str) -> List[Dict[str, Any]]:
        """
        Legge una riga e usa semplici regole per creare il blocco giusto.
        """
        line = line.strip()
        if not line:
            return []
        
        match_heading = re.match(r'^#{2,3}\s+(.*)', line)
        if match_heading:
            return [self.create_paragraph(f"**{match_heading.group(1)}**")]

        # Regola 1: Equazione blocco intero (es. $$ E=mc^2 $$)
        eq_start = line.find("$$")
        if eq_start != -1:
            eq_end = line.find("$$", eq_start + 2)
            if eq_end != -1:                           # $$ di chiusura trovata
                blocks = []
                line1 = line[:eq_start].strip()
                eq    = line[eq_start + 2:eq_end].strip()
                line2 = line[eq_end + 2:].strip()

                if line1:
                    blocks.extend(self.parse_markdown_line(line1))
                blocks.append(self.create_equation_block(eq))
                if line2:
                    blocks.extend(self.parse_markdown_line(line2))
                return blocks

        # Regola 2: Elenco Puntato
        if line.startswith("- ") or line.startswith("* "):
            return [self.create_bulleted_list_item(line[2:])]
            
        # Regola 3: Elenco Numerato (es. "1. Testo")
        match = re.match(r'^(\d+)\.\s+(.*)', line)
        if match:
            return [self.create_numbered_list_item(match.group(2))]

        # Regola 4: Paragrafo normale (al cui interno controlliamo Grassetto ed Equazioni)
        return [self.create_paragraph(line)]


    # =======================================================
    # METODI SEMPLICI DI CREAZIONE BLOCCHI NOTION (Le "Foglie")
    # =======================================================

    def _parse_rich_text(self, text: str) -> List[Dict[str, Any]]:
        """
        Scompone una stringa per trovare testo in **grassetto** e $equazioni inline$.
        """
        rich_text = []
        # Questa regex divide il testo isolando le parti con ** e con $
        parts = re.split(r'(\*\*.*?\*\*|\$.*?\$)', text)
        
        for part in parts:
            if not part:
                continue
            
            if part.startswith("**") and part.endswith("**"):
                # È un grassetto
                clean_text = part[2:-2]
                rich_text.append({
                    "type": "text",
                    "text": {"content": clean_text[:self.MAX_TEXT_LENGTH]},
                    "annotations": {"bold": True}
                })
            elif part.startswith("$") and part.endswith("$"):
                # È un'equazione in linea
                clean_eq = part[1:-1]
                rich_text.append({
                    "type": "equation",
                    "equation": {"expression": clean_eq}
                })
            else:
                # È testo normale
                rich_text.append({
                    "type": "text",
                    "text": {"content": part[:self.MAX_TEXT_LENGTH]}
                })
                
        return rich_text
    def create_divider(self) -> Dict[str, Any]:
        return {
            "object": "block",
            "type": "divider",
            "divider": {}
        }

    def create_heading_2(self, text: str) -> Dict[str, Any]:
        return {
            "object": "block",
            "type": "heading_2",
            "heading_2": {"rich_text": self._parse_rich_text(text)}
        }

    def create_heading_3(self, text: str) -> Dict[str, Any]:
        return {
            "object": "block",
            "type": "heading_3",
            "heading_3": {"rich_text": self._parse_rich_text(text)}
        }

    def create_paragraph(self, text: str) -> Dict[str, Any]:
        return {
            "object": "block",
            "type": "paragraph",
            "paragraph": {"rich_text": self._parse_rich_text(text)}
        }

    def create_bulleted_list_item(self, text: str) -> Dict[str, Any]:
        return {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {"rich_text": self._parse_rich_text(text)}
        }

    def create_numbered_list_item(self, text: str) -> Dict[str, Any]:
        return {
            "object": "block",
            "type": "numbered_list_item",
            "numbered_list_item": {"rich_text": self._parse_rich_text(text)}
        }

    def create_equation_block(self, expression: str) -> Dict[str, Any]:
        return {
            "object": "block",
            "type": "equation",
            "equation": {"expression": expression}
        }

    def _parse_markdown_to_blocks(self, content: str) -> List[Dict[str, Any]]:
        blocks = []
        lines = content.split('\n')
        
        in_math_block = False
        math_content = []

        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
            if stripped == "\\[":
                if in_math_block:
                    # Chiude il blocco e lo salva
                    blocks.append(self.create_equation_block("\n".join(math_content)))
                    in_math_block = False
                    math_content = []
                else:
                    # Apre il blocco
                    in_math_block = True
                continue
            
            if in_math_block:
                math_content.append(line)
                continue

            # 2. Ignora righe vuote se non siamo in un blocco math
            if not stripped:
                continue
            if stripped.startswith('# '):
                blocks.append(self.create_heading_2(stripped[2:] ))
            elif stripped.startswith('## '):
                blocks.append(self.create_heading_3(stripped[3:]))
            elif stripped.startswith('### '):
                blocks.append(self.create_heading_3(stripped[4:]))
            elif stripped.startswith('- ') or stripped.startswith('* '):
                blocks.append(self.create_bulleted_list_item(stripped[2:]))
            elif stripped[0].isdigit() and stripped[1:].startswith('. '):
                # Riconosce "1. Testo", "2. Testo"
                blocks.append(self.create_numbered_list_item(stripped[3:]))
            else:
                blocks.append(self.create_paragraph(stripped))
                
        return blocks
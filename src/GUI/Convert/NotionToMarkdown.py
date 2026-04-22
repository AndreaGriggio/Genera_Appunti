import matplotlib
import matplotlib.pyplot as plt
import io
from pathlib import Path

class NotionToMarkdown:
    def _render_formula(self, expression: str, inline: bool = False) -> str:
        """Renderizza la formula come PNG e restituisce il tag markdown."""

        if inline :
            expression.replace(r"\{","{")
            expression.replace(r"\}","}")
            
            return f"${expression}$"
        else:
        # Se contiene \\ va wrappato in aligned
            if r'\\' in expression:
                expression = f"\\begin{{aligned}}\n{expression}\n\\end{{aligned}}"
        return f"$$\n{expression}\n$$"
        
    def convert(self, blocks: list[dict]) -> str:
        lines = []
        self._convert_blocks_recursive(blocks, lines)
        return "\n\n".join(filter(None, lines))

    def _convert_blocks_recursive(self, blocks: list[dict], lines: list):
        for block in blocks:
            converted = self._convert_block(block)
            if converted:
                lines.append(converted)
            # Se il blocco ha figli NON gestiti internamente da _convert_block
            # (es. bulleted con sotto-liste), li processa qui
            btype = block.get("type")
            if btype not in ("child_page", "synced_block") and block.get("_children"):
                self._convert_blocks_recursive(block["_children"], lines)

    def _extract_text(self, rich_text: list) -> str:
        result = ""
        for t in rich_text:
            if t["type"] == "text":
                content = t["text"]["content"]
                if t.get("annotations", {}).get("bold"):
                    content = f"**{content}**"
                result += content
            elif t["type"] == "equation":
                expr = t['equation']['expression']

                expr = expr.replace(r'\_', '_').replace(r'\$', '$')
                result += self._render_formula(expr, inline=True)
        return result

    def _convert_block(self, block: dict) -> str | None:
        btype = block["type"]
        match btype:
            case "heading_2":
                return "## " + self._extract_text(block["heading_2"]["rich_text"])
            case "heading_3":
                return "### " + self._extract_text(block["heading_3"]["rich_text"])
            case "paragraph":
                return self._extract_text(block["paragraph"]["rich_text"])
            case "bulleted_list_item":
                return "- " + self._extract_text(block["bulleted_list_item"]["rich_text"])
            case "numbered_list_item":
                return "1. " + self._extract_text(block["numbered_list_item"]["rich_text"])
            case "equation":
                expr = block["equation"]["expression"]
                return self._render_formula(expr, inline=False)
            case "code":
                lang = block["code"].get("language", "")
                code = self._extract_text(block["code"]["rich_text"])
                return f"```{lang}\n{code}\n```"
            case "quote":
                return "> " + self._extract_text(block["quote"]["rich_text"])
            case "callout":
                return "> 💡 " + self._extract_text(block["callout"]["rich_text"])
            case "divider":
                return "---"
            case "image":
                url = block["image"].get("file", {}).get("url", "") or \
                      block["image"].get("external", {}).get("url", "")
                return f"![]({url})"
            case "child_page":
                # Il titolo della sottopagina diventa un heading 2
                titolo = block.get("child_page", {}).get("title", "")
                lines = []
                if titolo:
                    lines.append(f"## {titolo}")
                # Scende nei figli
                for child in block.get("_children", []):
                    converted = self._convert_block(child)
                    if converted:
                        lines.append(converted)
                    # Figli dei figli
                    for grandchild in child.get("_children", []):
                        converted = self._convert_block(grandchild)
                        if converted:
                            lines.append(converted)
                return "\n\n".join(lines) if lines else None

            case "synced_block":
                # Blocco sincronizzato — il contenuto è nei figli
                lines = []
                for child in block.get("_children", []):
                    converted = self._convert_block(child)
                    if converted:
                        lines.append(converted)
                return "\n\n".join(lines) if lines else None
            case _:
                return None

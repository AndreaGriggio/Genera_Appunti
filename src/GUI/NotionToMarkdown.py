import matplotlib
import matplotlib.pyplot as plt
import io
from pathlib import Path

class NotionToMarkdown:
    def __init__(self, formula_dir: Path):
        self.formula_dir = formula_dir
        self.formula_dir.mkdir(parents=True, exist_ok=True)
        self._formula_counter = 0

    def _render_formula(self, expression: str, inline: bool = False) -> str:
        """Renderizza la formula come PNG e restituisce il tag markdown."""
        self._formula_counter += 1
        filename = f"formula_{self._formula_counter}.png"
        output_path = self.formula_dir / filename

        success = self.formula_to_png(expression, output_path)
        if success:
            uri = output_path.as_uri()
            if inline:
                return f"![]({uri})"
            else:
                return f"\n![]({uri})\n"
        else:
            # Fallback testo grezzo se la formula non si renderizza
            return f"`{expression}`"
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
                return self._render_formula(t['equation']['expression'], inline=True)
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
    def formula_to_png(self,expression: str, output_path: Path) -> bool:
        """Converte una formula LaTeX in PNG usando matplotlib."""
        try:
            fig = plt.figure(figsize=(0.01, 0.01))
            fig.text(0, 0, f"${expression}$", fontsize=14)
            
            fig.savefig(
                output_path,
                dpi=150,
                bbox_inches="tight",
                pad_inches=0.1,
                transparent=True,
                format="png"
            )
            plt.close(fig)
            return True
        except Exception as e:
            print(f"⚠️ Formula non renderizzata: {e}")
            plt.close()
            return False
import markdown
import pdfkit
from pathlib import Path

class MarkdownToPDF:
    HTML_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>
        MathJax = {{
            tex: {{ inlineMath: [['$','$']], displayMath: [['$$','$$']] }}
        }};
    </script>
    <script src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-svg.js"></script>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 800px;
               margin: 40px auto; line-height: 1.6; }}
        code {{ background: #f4f4f4; padding: 2px 6px; border-radius: 3px; }}
        pre  {{ background: #f4f4f4; padding: 16px; border-radius: 6px; }}
        blockquote {{ border-left: 4px solid #ccc; margin: 0; padding-left: 16px; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; }}
        img {{ max-width: 100%; }}
    </style>
</head>
<body>{content}</body>
</html>"""

    OPTIONS = {
        "enable-local-file-access": "",
        "javascript-delay": "3000",
        "no-stop-slow-scripts": "",
        "encoding": "UTF-8",
        "margin-top":    "15mm",
        "margin-bottom": "15mm",
        "margin-left":   "15mm",
        "margin-right":  "15mm",
        "page-size": "A4",
    }

    def convert(self, markdown_text: str, output_path: str | Path) -> bool:
        if not markdown_text.strip():
            print("❌ Markdown vuoto, PDF non generato.")
            return False

        html_content = markdown.markdown(
            markdown_text,
            extensions=["fenced_code", "tables", "nl2br", "sane_lists"]
        )
        full_html = self.HTML_TEMPLATE.format(content=html_content)

        try:
            pdfkit.from_string(full_html, str(output_path), options=self.OPTIONS)
            print(f"✅ PDF generato: {output_path}")
            return True
        except Exception as e:
            print(f"❌ Errore pdfkit: {e}")
            return False
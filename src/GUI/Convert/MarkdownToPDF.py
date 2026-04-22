import pypandoc
import pytinytex
import re
import tempfile


class MarkdownToPDF:
     
    """ E' una classe che utilizza pandoc per convertire i file markdown presi da notion in pdf 
        E' necessario per utilizzarla avere installati all'interno del proprio computer anche tinytex con tutte i pacchetti latex necessari
        Per processare effettivamente i documenti markdown
    """
    LATEX_HEADER = r"""        
        \usepackage{amsmath}
        \usepackage{amssymb}
        \usepackage{cancel}
        \usepackage{mathtools}
        """
    def _fix_notion_shortcuts(self, text: str) -> str:
        """Sostituisce shortcut Notion non validi in LaTeX standard"""
        replacements = {
            r'\R': r'\mathbb{R}',
            r'\N': r'\mathbb{N}',
            r'\Z': r'\mathbb{Z}',
            r'\C': r'\mathbb{C}',
            r'\Q': r'\mathbb{Q}',
        }
        for wrong, correct in replacements.items():
            text = text.replace(wrong, correct)
        return text

    def _clean_math_blocks(self, text: str) -> str:
        """Rimuove righe vuote all'interno dei blocchi $$ ... $$"""
        def remove_blank_lines(match):
            inner = match.group(1)
            cleaned = re.sub(r'\n\s*\n', '\n', inner)
            return f"$$\n{cleaned.strip()}\n$$"
        
        return re.sub(r'\$\$(.*?)\$\$', remove_blank_lines, text, flags=re.DOTALL)

    def convert(self, markdown_text: str, output_path: str ) -> bool:
        if not markdown_text.strip():
            return False
        
        markdown_text = self._fix_notion_shortcuts(markdown_text)
        markdown_text = self._clean_math_blocks(markdown_text)  # ← aggiungi
        markdown_text =  re.sub(r'\$\s+([^\$]+?)\s+\$', r'$\1$', markdown_text)
        
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.tex', delete=False, encoding='utf-8'
        ) as f:
            f.write(self.LATEX_HEADER)
            header_path = f.name

        try:
            pypandoc.convert_text(
                markdown_text,
                'pdf',
                format='md',
                outputfile=str(output_path),
                extra_args=[
                    '--pdf-engine=xelatex',
                    f'--include-in-header={header_path}',
                    '--pdf-engine-opt=-interaction=nonstopmode',
                    '-V','geometry:top=1cm,bottom=1cm,left=1cm,right=1cm',
                    '-V', 'parskip=0pt',        # elimina spazio extra tra paragrafi
                    '-V', 'linestretch=1',    # interlinea (default è 1.2, abbassa se vuoi più compatto)
                ]
            )
            return True
        except Exception as e:
            print(f"Errore Pandoc: {e}")
            return False
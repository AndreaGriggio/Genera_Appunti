from src.GUI.Notion.NotionDownloader import NotionDownloader
from src.GUI.Convert.NotionToMarkdown import NotionToMarkdown
from src.GUI.Convert.MarkdownToPDF import MarkdownToPDF
from PyQt6.QtCore import QThread, pyqtSignal
from pathlib import Path
class NotionDownloaderSync(QThread):
    log = pyqtSignal(str)
    error = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self,instructions:dict):
        super().__init__()
        self.downloader = NotionDownloader()
        self.markdown_converter = MarkdownToPDF()
        self.instructions = instructions
    
    def run(self):
        try:
            self.log.emit("Scarico contenuti da Notion...")
            totali = len(self.instructions["ids"])
            failed = []

            for idx in range(totali):
                notion_id  = self.instructions["ids"][idx]
                output_pdf = self.instructions["outputs"][idx]
                output_pdf = Path(output_pdf).parent.with_suffix(".pdf")
                self.notion_converter = NotionToMarkdown()

                self.log.emit(f" [{idx+1}/{totali}] {output_pdf.stem}...")

                blocks = self.downloader.download_page(notion_id)

                markdown_text  = self.notion_converter.convert(blocks)

        
                success = self.markdown_converter.convert(markdown_text, str(output_pdf))
                self.notion_converter = None
                if not success:
                    failed.append(output_pdf.stem)
                    self.log.emit(f"Errore esportazione {output_pdf.stem}")
                else:
                    self.log.emit(f"Esportazione completata: {output_pdf.stem}")
            if failed:
                self.log.emit(f"PDF non generati : {', '.join(failed)}")
            else : 
                self.log.emit("Export completato!")
            self.finished.emit()

        except Exception as e:
            self.error.emit(f"Riscontrato errore: {e}")

    
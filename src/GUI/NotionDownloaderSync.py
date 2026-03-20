from src.GUI.NotionDownloader import NotionDownloader
from src.GUI.NotionToMarkdown import NotionToMarkdown
from src.GUI.MarkdownToPDF import MarkdownToPDF
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

            for idx in range(totali):
                notion_id  = self.instructions["ids"][idx]
                output_pdf = self.instructions["outputs"][idx]
                path_img = Path(output_pdf).parent
                output_img = path_img/"img"
                self.notion_converter = NotionToMarkdown(Path(output_img))

                self.log.emit(f" [{idx+1}/{totali}] {output_pdf.stem}...")

                blocks = self.downloader.download_page(notion_id)
                print(f"Blocchi scaricati : {len(blocks)}")
                print(f"Blocchi :\n {blocks}")
                markdown_text  = self.notion_converter.convert(blocks)
                print(f"Markdown generato : \n {markdown_text}")
                self.markdown_converter.convert(markdown_text, output_pdf)
                self.notion_converter = None

            self.log.emit("✅ Export completato!")
            self.finished.emit()

        except Exception as e:
            print(f"Riscontrato errore: {e}")
            self.error.emit(f"Riscontrato errore: {e}")

    
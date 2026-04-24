from pathlib import Path

from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import QMessageBox,QWidget

from src.GUI.Core.DeleteSync import DeleteSyncWorker
from src.GUI.Core.WorkerHandler import WorkerHandler
from src.GUI.Core.WhisperHandler import WhisperHandler 
from src.GUI.Core.PdfWindowHandler import PdfWindowHandler 
from src.GUI.Gen.GeminiAnswer import GeminiAnswer
from src.GUI.Gen.GeminiSync import GeminiSyncWorker
from src.GUI.Notion.NotionDownloaderSync import NotionDownloaderSync
from src.GUI.Notion.NotionLoader import NotionLoader
from src.GUI.Notion.NotionSyncBrancher import NotionSyncWorker
from src.GUI.Notion.NotionSyncLoader import NotionSyncLoader
from src.GUI.Transcribe.TranscribeWorker import TranscribeWorker


_GEMINI_PROMPT = (
    "Prendi il file caricato e crea gli appunti per Notion "
    "spiegando cosa contiene il file"
)


class FileActionHandler(QObject):
    """
    Contiene tutta la business logic delle azioni dell'utente.

    Non ha dipendenze da widget PyQt — riceve le tre classi di
    infrastruttura per iniezione di dipendenza, e comunica verso
    l'esterno solo tramite segnali.

    Emette:
      - log(str): messaggi da mostrare nella log area della UI
    """

    log = pyqtSignal(str)
    new_tab_ready = pyqtSignal(QWidget,str)

    def __init__(
        self,
        orchestrator: WorkerHandler,
        whisper: WhisperHandler,
        pdf_pool: PdfWindowHandler,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._orc = orchestrator
        self._whisper = whisper
        self._pdf = pdf_pool
        

        # Connessioni con WhisperManager
        self._whisper.log.connect(self.log)
        self._whisper.transcription_done.connect(self._on_transcription_done)
        self._whisper.error.connect(self._on_whisper_error)

        self._pdf.new_tab_ready.connect(self._on_new_tab_ready)
        # Stato temporaneo tra crea() e _on_transcription_done()
        # list[str] invece di variabili d'istanza separate per evitare
        # la race condition originale (self.audio + self.files settati in crea()).
        self._pending_pdf_paths: list[str] = []

    # ── Azioni pubbliche ────────────────────────────────────────────────────

    def crea(self, file_paths: list[Path],is_map:bool = False,is_pdf:bool = True,json_mode:bool = True) -> None:
        """
        Crea gli appunti per i file selezionati.
        - PDF → direttamente a Gemini
        - Audio → prima trascrizione Whisper, poi Gemini sul testo prodotto
        """
        audio = [p for p in file_paths if p.suffix.lower() in TranscribeWorker.SUPPORTED_FORMATS]
        pdfs  = [p for p in file_paths if p.suffix.lower() == ".pdf"]

        pdf_da_elaborare = self._filter_già_elaborati(pdfs)

        if pdf_da_elaborare:
            worker = GeminiSyncWorker(
                prompt=_GEMINI_PROMPT,
                paths=pdf_da_elaborare,
                is_map=is_map,
                pdf=is_pdf,
                json_mode=json_mode
                )
            worker.log.connect(self.log)
            self._orc.start_worker(worker)

        if audio:
            self.log.emit(f"Trovati {len(audio)} file audio, avvio trascrizione...")
            self._pending_pdf_paths = pdf_da_elaborare
            # Occupa uno slot nell'orchestrator per tenere la UI bloccata
            # durante la trascrizione (il processo non è un QThread).
            self._orc.begin_external()
            self._whisper.send_task(audio)

    def carica(self, file_paths: list[Path]) -> None:
        """Carica i file selezionati su Notion."""
        worker = NotionSyncLoader(file_paths)
        worker.log.connect(self.log)
        self._orc.start_worker(worker)

    def aggiorna(self) -> None:
        """Sincronizza la struttura cartelle con Notion."""
        worker = NotionSyncWorker()
        worker.log.connect(self.log)
        self._orc.start_worker(worker)

    def pulisci(self) -> None:
        """Elimina i file già elaborati e caricati su Notion."""
        worker = DeleteSyncWorker()
        worker.log.connect(self.log)
        self._orc.start_worker(worker)

    def scarica_pdf(self, folder_paths: list[Path]) -> None:
        """Scarica come PDF le pagine Notion corrispondenti alle cartelle selezionate."""
        instructions: dict = {"ids": [], "outputs": []}
        for folder in folder_paths:
            id_file = folder / ".id"
            if not id_file.exists():
                print(f"[FileActionHandler] Cartella senza .id ignorata: {folder.name}")
                continue
            notion_id = id_file.read_text(encoding="utf-8").strip()
            instructions["ids"].append(notion_id)
            instructions["outputs"].append(str(folder / f"{folder.name}.pdf"))

        if not instructions["ids"]:
            return

        worker = NotionDownloaderSync(instructions=instructions)
        worker.log.connect(self.log)
        self._orc.start_worker(worker)

    def open_pdf(self, file_path: str) -> None:
        """Apre un PDF nel viewer interno."""
        self._pdf.open(file_path)

    # ── Callback privati ────────────────────────────────────────────────────
    def _on_new_tab_ready(self,obj,titolo):

        self.new_tab_ready.emit(obj,titolo)

    def _on_transcription_done(self, txt_paths: list[Path]) -> None:
        """
        Chiamato quando Whisper termina. Avvia Gemini sui testi prodotti
        (più eventuali PDF già in lista), poi libera lo slot di occupato.

        L'ordine è deliberato: start_worker() incrementa il contatore prima
        che end_external() lo decrementi, così la UI non flasha mai su busy=False
        tra le due operazioni consecutive.
        """
        tutti = self._pending_pdf_paths + [str(p) for p in txt_paths]
        self._pending_pdf_paths = []

        if tutti:
            worker = GeminiSyncWorker(prompt=_GEMINI_PROMPT, paths=tutti)
            worker.log.connect(self.log)
            self._orc.start_worker(worker)  # incrementa prima di decrementare

        self._orc.end_external()  # rilascia lo slot riservato in crea()

    def _on_whisper_error(self, msg: str) -> None:
        self._orc.end_external()
        self.log.emit(f"Errore Whisper: {msg}")

    def _filter_già_elaborati(self, pdfs: list[Path]) -> list[str]:
        """
        Chiede conferma all'utente per i PDF già presenti nella storia.
        Restituisce la lista di path (come str) da effettivamente elaborare.
        """
        handler = GeminiAnswer()
        storia = handler.get_history()
        result: list[str] = []

        for f in pdfs:
            if f.name in storia:
                reply = QMessageBox.question(
                    None,
                    "File già elaborato",
                    f"'{f.name}' è già stato elaborato.\nVuoi rigenerare gli appunti?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                )
                if reply == QMessageBox.StandardButton.Yes:
                    result.append(str(f))
                    NotionLoader().delete_file(f.name)
            else:
                result.append(str(f))

        return result
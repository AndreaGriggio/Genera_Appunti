import sys
from pathlib import Path
# 1. Widgets (Elementi visivi: Finestre, Bottoni, Layout)
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, 
    QHBoxLayout, QPushButton, QTreeView, 
    QMessageBox, QTextEdit
)
import multiprocessing

from src.GUI.NotionSyncBrancher import NotionSyncWorker
from src.GUI.GeminiSync import GeminiSyncWorker
from src.GUI.GeminiAnswer import GeminiAnswer
from src.GUI.NotionSyncLoader import NotionSyncLoader
from src.GUI.DeleteSync import DeleteSyncWorker
from src.GUI.DeleteWorker import DeleteWorker
from src.GUI.ColorFileSystemModel import ColorFileSystemModel
from src.GUI.SettingsDialog import open_settings
from src.GUI.NotionLoader import NotionLoader
from src.GUI.TranscribeSync import TranscribeSyncWorker
from src.GUI.TranscribeWorker import TranscribeWorker
from src.GUI.NotionDownloaderSync import NotionDownloaderSync
from src.GUI.TranscribeModelLoaderWorker import TranscribeModelLoaderWorker
from src.GUI.whisperProcess import whisper_lazy_engine
from src.GUI.PDFViewer import PDFViewerWidget
# 2. QtGui (Componenti grafici e Modelli) -> QFileSystemModel è QUI!
from PyQt6.QtGui import QAction, QShortcut, QKeySequence, QDesktopServices


# 3. QtCore (Funzionalità base non grafiche: Directory, Threading)
from PyQt6.QtCore import Qt, QUrl, QTimer
from src.GUI.config import DATAPATH, BTN_HEIGHT
#Parti fatte bene
#1) aggiornamento di Notion
#2) interfaccia grafica
#3) rintracciamento id pagina
#4) inserimento e cancellazione pdf

#Parti da fare 
#1) interazione con API gemini
#2) inserimento delle risposte con Notion
#3) gestione file dict_json

class FileManagerWindow(QMainWindow):
    
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Generatore Appunti")#setta il nome della finestra
        self.resize(1200, 650)#setta la dimensione della finestra
        self.setAcceptDrops(True) # Abilita il trascinamento

        menu_bar = self.menuBar()
        settings_action = QAction("Impostazioni", self)
        settings_action.triggered.connect(self.apri_impostazioni)
        menu_bar.addAction(settings_action)

        # --- Setup UI ---
        central_widget = QWidget()#creazione oggetto Qwidget come contenitore dell'elemento princpale
        self.setCentralWidget(central_widget)#dice alla finestra principale di contenere l'oggetto Qwidget come contenitore dell'elemento principale
        main_layout = QVBoxLayout()#VBox layout per contenere le cartelle di progetto
        central_widget.setLayout(main_layout)#main_layout viene inserito all'interno del contenitore principale

        # Mantieni i riferimenti alle finestre PDF aperte, altrimenti PyQt le distrugge subito
        self.open_pdf_windows = []
        self.active_workers = set()
        self.pending_operations = 0



        
        self.model = ColorFileSystemModel()
        filter = TranscribeWorker.SUPPORTED_FORMATS
        filter = list(filter)
        filters = []
        for f in filter :
            filters.append("*"+f)
        
        filters.append("*.pdf")
        filters.append("*.txt")
    
        self.model.setRootPath(DATAPATH) 
        self.model.setReadOnly(False)
        self.model.setNameFilters(filters)
        self.model.setNameFilterDisables(False)
        self.tree_view = QTreeView()
        self.tree_view.setModel(self.model)
        self.tree_view.setRootIndex(self.model.index(DATAPATH))
        #--- Scorciatoie ---
        self.shortcut_delete = QShortcut(QKeySequence("Delete"), self.tree_view)
        self.shortcut_enter = QShortcut(QKeySequence("Return"), self.tree_view)
        self.shortcut_num_enter = QShortcut(QKeySequence("Enter"), self.tree_view)

        # Colleghiamo entrambe alla stessa funzione
        self.shortcut_enter.activated.connect(self.azione_apri_elemento)
        self.shortcut_num_enter.activated.connect(self.azione_apri_elemento)
        self.shortcut_delete.activated.connect(self.cancella)
        self.tree_view.doubleClicked.connect(self.azione_apri_elemento)        

        self.tree_view.setColumnHidden(1, False) 
        self.tree_view.setColumnHidden(2, True)  
        self.tree_view.setColumnHidden(3, False)
        self.tree_view.sortByColumn(0, Qt.SortOrder.AscendingOrder)
        self.tree_view.setDragDropMode(QTreeView.DragDropMode.DropOnly)
        self.tree_view.setSelectionMode(QTreeView.SelectionMode.ExtendedSelection)
        self.tree_view.setAnimated(True)
        self.tree_view.setIndentation(20)
        self.tree_view.setSortingEnabled(True)
        
        # Allarga la colonna del nome
        self.tree_view.header().resizeSection(0, 300)
        main_layout.addWidget(self.tree_view)
        # --- Bottoni ---
        buttons_layout = QHBoxLayout()
        
        #--- BOTTONE PULISCI ---
        self.btn_pulisci = QPushButton("Pulisci")
        self.btn_pulisci.setFixedHeight(BTN_HEIGHT)
        self.btn_pulisci.setStyleSheet("padding: 5px;")

        #azione del bottone
        self.btn_pulisci.clicked.connect(self.pulisci)
        
        #--- BOTTONE CREA ---
        self.btn_crea = QPushButton("Crea")

        self.btn_crea.setFixedHeight(BTN_HEIGHT)
        self.btn_crea.setStyleSheet("padding: 5px;")

        #azione del bottone
        self.btn_crea.clicked.connect(self.crea)

        #--- BOTTONE CARICA ---
        self.btn_carica = QPushButton("Carica")
        self.btn_carica.setFixedHeight(BTN_HEIGHT)
        self.btn_carica.setStyleSheet("padding: 5px;")

        #azione del bottone
        self.btn_carica.clicked.connect(self.carica)

        #--- BOTTONE AGGIORNA ---
        self.btn_aggiorna = QPushButton("Aggiorna")
        self.btn_aggiorna.setFixedHeight(BTN_HEIGHT)
        self.btn_aggiorna.setStyleSheet("padding: 5px;")
        
                #azione del bottone
        self.btn_aggiorna.clicked.connect(self.aggiorna)
        #--- BOTTONE SCARICA PDF ---
        self.btn_pdf = QPushButton("Scarica PDF")
        self.btn_pdf.setFixedHeight(BTN_HEIGHT)
        self.btn_pdf.setStyleSheet("padding: 5px;")

        self.btn_pdf.clicked.connect(self.scarica_pdf)



        # Aggiungi i bottoni al layout
        buttons_layout.addWidget(self.btn_pulisci)
        buttons_layout.addWidget(self.btn_aggiorna)
        buttons_layout.addStretch() # Molla separatrice
        buttons_layout.addWidget(self.btn_crea)
        buttons_layout.addWidget(self.btn_carica)
        buttons_layout.addWidget(self.btn_pdf)

        main_layout.addLayout(buttons_layout)
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setFixedHeight(60)
        self.log_area.setStyleSheet(
            "font-family: 'Courier New'; font-size: 11px; "
            "border: 1px solid #444;"
        )
        main_layout.addWidget(self.log_area)

        self.task_queue = multiprocessing.Queue()
        self.result_queue = multiprocessing.Queue()
        self.whisper_process = multiprocessing.Process(
            target=whisper_lazy_engine, 
            args=(self.task_queue, self.result_queue),
            daemon=True
        )
        self.whisper_process.start()
        
        # Timer che controlla i risultati (già visto)
        self.monitor_timer = QTimer()
        self.monitor_timer.timeout.connect(self.check_whisper_results)
        self.monitor_timer.start(200)
        #--- Spazzino ---
        self.cleaner = DeleteWorker()
        self.transcriber = None

    def _set_busy_state(self, busy: bool):
        controls = (
            self.btn_crea,
            self.btn_aggiorna,
            self.btn_carica,
            self.btn_pulisci,
            self.btn_pdf,
        )
        for control in controls:
            control.setEnabled(not busy)

        self.btn_aggiorna.setText("Sincronizzazione in corso..." if busy else "Aggiorna")

    def _begin_operation(self):
        self.pending_operations += 1
        self._set_busy_state(True)

    def _end_operation(self):
        self.pending_operations = max(0, self.pending_operations - 1)
        if self.pending_operations == 0:
            self.reset_gui_state()

    def _start_worker(self, worker):
        self.active_workers.add(worker)
        self._begin_operation()
        worker.finished.connect(lambda w=worker: self._on_worker_finished(w))
        worker.error.connect(lambda error_msg, w=worker: self._on_worker_error(w, error_msg))
        worker.start()
        return worker

    def _on_worker_finished(self, worker):
        self.active_workers.discard(worker)
        QMessageBox.information(self, "Successo", "Operazione terminata")
        self._end_operation()

    def _on_worker_error(self, worker, error_msg):
        self.active_workers.discard(worker)
        QMessageBox.critical(self, "Errore Notion", f"Si è verificato un errore:\n{error_msg}")
        self._end_operation()

    def check_whisper_results(self):
        while not self.result_queue.empty():
            msg = self.result_queue.get()
            
            if msg["type"] == "log":
                self.on_log_message(msg["content"])
        

                
            elif msg["type"] == "all_done":
                self.on_log_message("✅ Trascrizione completata. Avvio analisi con Gemini...")
                # ORA chiamiamo Gemini con la lista completa (PDF originali + TXT generati)
                self.on_transcription_done()
                self._end_operation()
                
            elif msg["type"] == "error":
                QMessageBox.critical(self, "Errore Trascrizione", msg["content"])
                self._end_operation()

    #--- Eventi Drag & Drop ---
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        testo_files = "\n".join([Path(f).name for f in files])
        self.mostra_messaggio(f"Hai caricato:\n{testo_files}")

    # --- Le tue Azioni ---
    def apri_impostazioni(self):
        """
        Apre il dialogo impostazioni in modalità modale.
        Blocca la finestra principale fino alla chiusura.
        Se l'utente salva, aggiorna i colori nel model.
        """
        self.log_area.clear()
        print("1 - prima di open_settings")
        changed = open_settings(parent=self)
        print(f"2 - dopo open_settings, changed={changed}")
        if changed:
            self.model.refresh_histories()
    def pulisci(self):
        self.log_area.clear()
        self.worker = DeleteSyncWorker()
        self.worker.log.connect(self.on_log_message)
        self._start_worker(self.worker)
    
    def scarica_pdf(self):
        self.log_area.clear()

        file_selezionati = self.tree_view.selectedIndexes()
        if not file_selezionati:
            return

        raw_paths = [Path(self.model.filePath(index)) for index in file_selezionati
                    if self.model.isDir(index)]
        file_paths = list(set(raw_paths))

        instructions = {"ids": [], "outputs": []}

        for f in file_paths:
            id_path = f / ".id"
            if not id_path.exists():
                print(f"Cartella senza .id ignorata: {f.name}")
                continue
            with open(id_path, "r", encoding="utf-8") as file:
                notion_id = file.read().strip()
            instructions["ids"].append(notion_id)
            instructions["outputs"].append(f / f"{f.name}.pdf")

        if not instructions["ids"]:
            return

        self.worker = NotionDownloaderSync(instructions=instructions)
        self.worker.log.connect(self.on_log_message)
        self._start_worker(self.worker)
    

    def load_model(self)->None:
        self._begin_operation()
        self.task_queue.put({"paths":self.audio})
        
    

    def crea(self):
        print("Creazione in corso...")
        self.log_area.clear()

        file_selezionati = self.tree_view.selectedIndexes()
        if not file_selezionati:
            return

        raw_paths = [self.model.filePath(index) for index in file_selezionati
                    if not self.model.isDir(index)]
        file_paths = list(set(raw_paths))

        audio_paths = [Path(f) for f in file_paths
                    if Path(f).suffix.lower() in TranscribeWorker.SUPPORTED_FORMATS]
        pdf_paths   = [Path(f) for f in file_paths
                    if Path(f).suffix.lower() == ".pdf"]

        # ── Controlla storia PDF ──────────────────────────────────────────
        handler = GeminiAnswer()
        storia = handler.get_history()
        file_da_elaborare = []

        for file in pdf_paths:
            file_name = Path(file).name
            if file_name in storia:
                risposta = QMessageBox.question(
                    self,
                    "File già elaborato",
                    f"Il file '{file_name}' è già stato elaborato in passato.\nVuoi rigenerare gli appunti?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if risposta == QMessageBox.StandardButton.Yes:
                    file_da_elaborare.append(str(file))
                    NotionLoader().delete_file(file_name)
                else:
                    print(f"File {file_name} non elaborato")
            else:
                file_da_elaborare.append(str(file))

        prompt_utente = 'Prendi il file caricato e crea gli appunti per Notion spiegando cosa contiene il file'

        # ── Caso 1: ci sono audio ────────────────────────────────────────
        if file_da_elaborare:
            self.worker = GeminiSyncWorker(prompt=prompt_utente, paths=file_da_elaborare)
            self.worker.log.connect(self.on_log_message)
            self._start_worker(self.worker)
        
        # ── Caso 2: solo PDF ─────────────────────────────────────────────
        if audio_paths:
            self.on_log_message(f"Trovati {len(audio_paths)} file audio, avvio trascrizione...")
            self.audio = audio_paths
            self.files = file_da_elaborare
            self.prompt = prompt_utente

            self.load_model()

    def on_transcription_done(self):
        txt_paths = [str(p.with_suffix(".txt")) for p in self.audio]
        tutti = self.files + txt_paths
        if tutti:
            self.worker = GeminiSyncWorker(prompt=self.prompt, paths=tutti)
            self.worker.log.connect(self.on_log_message)
            self._start_worker(self.worker)

        

        

    def carica(self):
        self.log_area.clear()

        file_selezionati = self.tree_view.selectedIndexes()
        if not file_selezionati :
            return 
        file_paths = [self.model.filePath(index) for index in file_selezionati if not self.model.isDir(index)]
        
        raw_paths = [self.model.filePath(index) for index in file_selezionati if not self.model.isDir(index)]

# Rimuoviamo i duplicati convertendola in set e poi di nuovo in lista
        file_paths = list(Path(file) for file in set(raw_paths))
 
        for file in file_paths:
            print(file)

        self.worker = NotionSyncLoader(file_paths)
        self.worker.log.connect(self.on_log_message)
        self._start_worker(self.worker)

        

    def aggiorna(self):
        """Chiamato quando premi il bottone."""
        self.log_area.clear()
        
        # 1. Disabilita i bottoni per evitare che l'utente clicchi due volte
        self.btn_aggiorna.setEnabled(False)
        self.btn_carica.setEnabled(False)

        self.btn_aggiorna.setText("Sincronizzazione in corso...")

        # 2. Crea il thread
        self.worker = NotionSyncWorker()

        # 3. Collega i segnali del thread alle funzioni della GUI

        self.worker.log.connect(self.on_log_message)
        # 4. Avvia il thread
        self._start_worker(self.worker)

    def on_log_message(self, message):
        """Chiamato dal segnale log."""
        self.log_area.append(message)
    # Scrolla automaticamente in fondo
        self.log_area.verticalScrollBar().setValue(
            self.log_area.verticalScrollBar().maximum()
        )
        # Se hai una casella di testo nella GUI, fai: self.text_area.append(message)
        print(f"[GUI LOG] {message}") 

    def reset_gui_state(self):
        """Riporta i bottoni allo stato normale."""
        self._set_busy_state(False)
        self.model.refresh_histories()

    def cancella(self):
        indici = self.tree_view.selectedIndexes()

        
        if indici is not None:
            path_list = []
            for index in indici:
                if not self.model.isDir(index):
                    path_list.append(self.model.filePath(index))

            file_paths = list(Path(file) for file in set(path_list))
    

            self.cleaner.delete_specific(file_paths)
            
            self.model.refresh_histories()


    def mostra_messaggio(self, testo):
        msg = QMessageBox(self)
        msg.setWindowTitle("Info")
        msg.setText(testo)
        msg.exec()

    def apri_pdf_in_viewer(self, file_path: str):
        """Apre un PDF con il widget interno e mantiene il codice centralizzato."""
        viewer = PDFViewerWidget(file_path)
        viewer.setWindowTitle(Path(file_path).name)
        self.open_pdf_windows.append(viewer)
        viewer.destroyed.connect(lambda *_: self._cleanup_pdf_windows())
        viewer.show()
        viewer.activateWindow()
        viewer.raise_()
        viewer.setFocus()
        return viewer

    def _cleanup_pdf_windows(self):
        active_windows = []
        for window in self.open_pdf_windows:
            if window is None:
                continue
            try:
                if not window.isHidden():
                    active_windows.append(window)
            except RuntimeError:
                continue
        self.open_pdf_windows = active_windows

    def azione_apri_elemento(self, index=None):
        """
        Gestisce la pressione del tasto INVIO.
        - Se è una cartella: Espande o Collassa l'albero.
        - Se è un file: Lo apre con il programma predefinito di sistema.
        """
        # 1. Recupera l'indice selezionato
        if index is None or not index.isValid():
            index = self.tree_view.currentIndex()
        
        # Se non c'è nulla di selezionato, esci
        if not index.isValid():
            return

        # 2. Gestione Cartelle
        if self.model.isDir(index):
            # Controlla lo stato visivo nella TreeView
            if self.tree_view.isExpanded(index):
                self.tree_view.collapse(index) # Se aperta, chiudila
            else:
                self.tree_view.expand(index)   # Se chiusa, aprila
        
        # 3. Gestione File (Opzionale ma comodissimo)
        else:
            # Recupera il percorso completo del file dal modello
            file_path = self.model.filePath(index)
            
            if file_path.lower().endswith('.pdf'):
                self.apri_pdf_in_viewer(file_path)
            else:
                # Usa QDesktopServices per aprire il file come se facessi doppio click
                # (Apre i TXT con l'editor di sistema, ecc.)
                QDesktopServices.openUrl(QUrl.fromLocalFile(file_path))

    def closeEvent(self, event):
        self.monitor_timer.stop()
        for window in list(self.open_pdf_windows):
            try:
                window.close()
            except RuntimeError:
                continue
        if self.whisper_process.is_alive():
            self.whisper_process.terminate()
            self.whisper_process.join(timeout=1)
        super().closeEvent(event)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FileManagerWindow()
    window.show()
    sys.exit(app.exec())

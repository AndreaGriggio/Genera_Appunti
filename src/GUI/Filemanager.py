import sys
from pathlib import Path
import fitz
# 1. Widgets (Elementi visivi: Finestre, Bottoni, Layout)
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, 
    QHBoxLayout, QPushButton, QTreeView, 
    QHeaderView, QMessageBox, QLabel,QSplitter,QScrollArea,QTextEdit
)
from src.GUI.NotionSyncBrancher import NotionSyncWorker
from src.GUI.GeminiSync import GeminiSyncWorker
from src.GUI.GeminiAnswer import GeminiAnswer
from src.GUI.NotionSyncLoader import NotionSyncLoader
from src.GUI.DeleteSync import DeleteSyncWorker
from src.GUI.DeleteWorker import DeleteWorker
from src.GUI.ColorFileSystemModel import ColorFileSystemModel
from src.GUI.SettingsDialog import open_settings

# 2. QtGui (Componenti grafici e Modelli) -> QFileSystemModel è QUI!
from PyQt6.QtGui import  QAction,QShortcut, QKeySequence,QDesktopServices,QPixmap


# 3. QtCore (Funzionalità base non grafiche: Directory, Threading)
from PyQt6.QtCore import Qt, QDir,QUrl,QByteArray
from src.GUI.config import DATAPATH,BTN_HEIGHT
PREVIEW_PAGES = 3
PREVIEW_WIDTH = 320
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
        splitter = QSplitter(Qt.Orientation.Horizontal)



        # --- File System Model (La correzione è qui) ---
        self.model = ColorFileSystemModel()
        
        self.model.setRootPath(DATAPATH) 
        self.model.setReadOnly(False)
        self.model.setNameFilters(["*.pdf"])
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
        self.tree_view.clicked.connect(self.aggiorna_anteprima)
        self.splitter = QSplitter(Qt.Orientation.Horizontal)

        #-- WIDGET ANTEPRIMA ---
        preview_container = QWidget()
        preview_container.setMinimumWidth(PREVIEW_WIDTH + 20)
        preview_layout = QVBoxLayout(preview_container)
        preview_layout.setContentsMargins(4, 4, 4, 4)
        preview_layout.setSpacing(4)
        main_layout.addWidget(self.tree_view)#aggiunta del treeview
        # Titolo del file selezionato
        self.preview_title = QLabel("Nessun file selezionato")
        self.preview_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_title.setStyleSheet("font-weight: bold; padding: 4px;")
        self.preview_title.setWordWrap(True)
        preview_layout.addWidget(self.preview_title)

        # Scroll area che contiene le pagine impilate verticalmente
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.pages_widget = QWidget()
        self.pages_layout = QVBoxLayout(self.pages_widget)
        self.pages_layout.setContentsMargins(4, 4, 4, 4)
        self.pages_layout.setSpacing(8)
        self.pages_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.scroll_area.setWidget(self.pages_widget)
        preview_layout.addWidget(self.scroll_area)

        # --- Aggiunge i due pannelli allo splitter ---
        self.splitter.addWidget(self.tree_view)
        self.splitter.addWidget(preview_container)

        # Proporzione iniziale: 65% TreeView, 35% Anteprima
        self.splitter.setStretchFactor(0, 65)
        self.splitter.setStretchFactor(1, 35)

        main_layout.addWidget(self.splitter)
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

        # Aggiungi i bottoni al layout
        buttons_layout.addWidget(self.btn_pulisci)
        buttons_layout.addWidget(self.btn_aggiorna)
        buttons_layout.addStretch() # Molla separatrice
        buttons_layout.addWidget(self.btn_crea)
        buttons_layout.addWidget(self.btn_carica)

        main_layout.addLayout(buttons_layout)
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setFixedHeight(60)
        self.log_area.setStyleSheet(
            "font-family: 'Courier New'; font-size: 11px; "
            "border: 1px solid #444;"
        )
        main_layout.addWidget(self.log_area)
        #--- Spazzino ---
        self.cleaner = DeleteWorker()
    def aggiorna_anteprima(self, index):
        """
        Chiamato al click singolo sul TreeView.
        Se è un PDF, mostra le prime PREVIEW_PAGES pagine nel pannello.
        Se è una cartella o un file non-PDF, mostra il placeholder.
        Non interferisce con la selezione multipla (usa clicked, non selectionChanged).
        """
        # Pulisce il contenuto precedente
        self._svuota_anteprima()

        if self.model.isDir(index):
            self.preview_title.setText("Seleziona un file PDF")
            return

        file_path = self.model.filePath(index)
        if not file_path.lower().endswith(".pdf"):
            self.preview_title.setText("Seleziona un file PDF")
            return

        nome = Path(file_path).name
        self.preview_title.setText(nome)
        

        try:
            doc = fitz.open(file_path)
            n_pages = min(PREVIEW_PAGES, len(doc))

            for i in range(n_pages):
                page = doc[i]

                # Zoom proporzionale per adattarsi a PREVIEW_WIDTH
                zoom = PREVIEW_WIDTH / page.rect.width
                mat = fitz.Matrix(zoom, zoom)
                pix = page.get_pixmap(matrix=mat, alpha=False)

                # Converti in QPixmap tramite bytes PNG
                img_bytes = QByteArray(pix.tobytes("png"))
                pixmap = QPixmap()
                pixmap.loadFromData(img_bytes)

                lbl_pagina = QLabel()
                lbl_pagina.setPixmap(pixmap)
                lbl_pagina.setAlignment(Qt.AlignmentFlag.AlignHCenter)
                lbl_pagina.setStyleSheet("border: 1px solid #cccccc;")
                self.pages_layout.addWidget(lbl_pagina)

                # Separatore visivo tra pagine
                if i < n_pages - 1:
                    sep = QLabel()
                    sep.setFixedHeight(1)
                    sep.setStyleSheet("background-color: #dddddd;")
                    self.pages_layout.addWidget(sep)

            doc.close()

            # Se il PDF ha più pagine di quelle mostrate, avvisa
            if len(doc) > PREVIEW_PAGES:
                lbl_more = QLabel(f"… altre {len(doc) - PREVIEW_PAGES} pagine")
                lbl_more.setAlignment(Qt.AlignmentFlag.AlignCenter)
                lbl_more.setStyleSheet("color: #888888; font-style: italic; padding: 4px;")
                self.pages_layout.addWidget(lbl_more)

        except Exception as e:
            lbl_err = QLabel(f"Errore anteprima:\n{e}")
            lbl_err.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl_err.setStyleSheet("color: #cc0000; padding: 10px;")
            self.pages_layout.addWidget(lbl_err)

    def _svuota_anteprima(self):
        """Rimuove tutti i widget figli dal layout delle pagine."""
        while self.pages_layout.count():
            item = self.pages_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
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
        self.btn_crea.setEnabled(True)
        self.btn_pulisci.setEnabled(False)
        self.btn_carica.setEnabled(False)

        self.worker = DeleteSyncWorker()
        self.worker.finished.connect(self.on_sync_finished)
        self.worker.error.connect(self.on_sync_error)
        self.worker.log.connect(self.on_log_message)
        self.worker.start()

    def crea(self):
        print("Creazione in corso...")
        self.log_area.clear()
        #1. Disabilito bottoni non necessari
        self.btn_pulisci.setEnabled(False)

        file_da_elaborare = []
        #prendiamo i percorsi dei selezionati

        file_selezionati = self.tree_view.selectedIndexes()
        if not file_selezionati :
            return 
        file_paths = [self.model.filePath(index) for index in file_selezionati if not self.model.isDir(index)]
        
        raw_paths = [self.model.filePath(index) for index in file_selezionati if not self.model.isDir(index)]

# Rimuoviamo i duplicati convertendola in set e poi di nuovo in lista
        file_paths = list(set(raw_paths))
        
        handler = GeminiAnswer()

        storia = handler.get_history()

        for file in file_paths:
            file_name = Path(file).name
            if file_name in storia:
                risposta = QMessageBox.question(
                    self, 
                    "File già elaborato", 
                    f"Il file '{file_name}' è già stato elaborato in passato.\nVuoi rigenerare gli appunti?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                #E' nella storia allora decidi se elaborarlo
                if risposta == QMessageBox.StandardButton.Yes:
                    file_da_elaborare.append(file)
                else:
                    print(f"File {file_name} non elaborato")
            else:#non in storia
                file_da_elaborare.append(file)
            
        # 4. Avvia il Thread passando la lista filtrata!
        prompt_utente = 'Prendi il file caricato e crea gli appunti per Notion spiegando cosa contiene il file'
        self.worker = GeminiSyncWorker(prompt=prompt_utente, pdf_paths=file_da_elaborare)

        #3. Collega i segnali del thread alle funzioni della GUI
        self.worker.finished.connect(self.on_sync_finished)
        self.worker.error.connect(self.on_sync_error)
        self.worker.log.connect(self.on_log_message)

        #4. Avvia il thread
        self.worker.start()


        

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
        self.btn_pulisci.setEnabled(False)
        self.btn_carica.setEnabled(False)

        self.worker = NotionSyncLoader(file_paths)
        self.worker.finished.connect(self.on_sync_finished)
        self.worker.error.connect(self.on_sync_error)
        self.worker.log.connect(self.on_log_message)
        self.worker.start()

        

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
        self.worker.finished.connect(self.on_sync_finished)
        self.worker.error.connect(self.on_sync_error)
        # 4. Avvia il thread
        self.worker.start()

    def on_sync_finished(self):
        """Chiamato dal segnale finished."""
        QMessageBox.information(self, "Successo", "Operazione terminata")
        self.reset_gui_state()

    def on_sync_error(self, error_msg):
        """Chiamato dal segnale error."""
        QMessageBox.critical(self, "Errore Notion", f"Si è verificato un errore:\n{error_msg}")
        self.reset_gui_state()

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
        self.log_area.clear()
        self.btn_aggiorna.setEnabled(True)
        self.btn_carica.setEnabled(True)
        self.btn_pulisci.setEnabled(True)
        self.btn_carica.setEnabled(True)
        
        self.model.refresh_histories()
        self.btn_aggiorna.setText("Aggiorna")
        # Puliamo la variabile worker per sicurezza
        self.worker = None
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
    def azione_apri_elemento(self):
        """
        Gestisce la pressione del tasto INVIO.
        - Se è una cartella: Espande o Collassa l'albero.
        - Se è un file: Lo apre con il programma predefinito di sistema.
        """
        # 1. Recupera l'indice selezionato
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
            
            # Usa QDesktopServices per aprire il file come se facessi doppio click
            # (Apre i PDF col lettore PDF, i TXT col blocco note, etc.)
            QDesktopServices.openUrl(QUrl.fromLocalFile(file_path))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FileManagerWindow()
    window.show()
    sys.exit(app.exec())
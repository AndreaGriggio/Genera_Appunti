import sys
from pathlib import Path
from typing import Callable
# 1. Widgets (Elementi visivi: Finestre, Bottoni, Layout)
from PyQt6.QtWidgets import (
    QApplication,  QWidget, QVBoxLayout, 
    QHBoxLayout, QPushButton, QTreeView, 
    QMessageBox, QTextEdit
)



from PyQt6.QtGui import QShortcut, QKeySequence, QDesktopServices
from PyQt6.QtCore import Qt, QUrl, QTimer, pyqtSignal

from src.GUI.Core.DeleteWorker import DeleteWorker
from src.GUI.config import DATAPATH, BTN_HEIGHT
from src.GUI.Transcribe.TranscribeWorker import TranscribeWorker
from src.GUI.Core.WorkerHandler import WorkerHandler
from src.GUI.Core.WhisperHandler import WhisperHandler 
from src.GUI.Core.PdfWindowHandler import PdfWindowHandler 
from src.GUI.Core.FileActionHandler import FileActionHandler
from src.GUI.Core.ColorFileSystemModel import ColorFileSystemModel

class Manager(QWidget):
    new_tab_ready = pyqtSignal(QWidget,str)
    open_this_mappa = pyqtSignal(str)
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Generatore Appunti")#setta il nome della finestra
        self.resize(1200, 650)#setta la dimensione della finestra
        self.setAcceptDrops(True) # Abilita il trascinamento

        main_layout = QVBoxLayout()#VBox layout per contenere le cartelle di progetto
        self.setLayout(main_layout)
        self.deleter = DeleteWorker()
        
        self.file_manager_window = FileActionHandler(WorkerHandler(),WhisperHandler(),PdfWindowHandler())
        self.model = ColorFileSystemModel()
        filter = TranscribeWorker.SUPPORTED_FORMATS
        filter = list(filter)
        filters = []
        for f in filter :
            filters.append("*"+f)
        
        filters.append("*.pdf")
        filters.append("*.txt")
        filters.append("*.mappa")
    
        self.model.setRootPath(DATAPATH) 
        self.model.setReadOnly(False)
        self.model.setNameFilters(filters)
        self.model.setNameFilterDisables(False)
        self.tree_view = QTreeView()
        self.tree_view.setModel(self.model)
        self.tree_view.setRootIndex(self.model.index(DATAPATH))
        #--- Scorciatoie ---
        self.shortcut_delete = QShortcut(QKeySequence("Delete"), self)
        self.shortcut_delete_backspace = QShortcut(QKeySequence("Backspace"), self)
        
        self.shortcut_delete_backspace.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        self.shortcut_delete.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)


        self.shortcut_enter = QShortcut(QKeySequence("Return"), self.tree_view)
        self.shortcut_num_enter = QShortcut(QKeySequence("Enter"), self.tree_view)

        # Colleghiamo entrambe alla stessa funzione
        self.shortcut_enter.activated.connect(self.azione_apri_elemento)
        self.shortcut_num_enter.activated.connect(self.azione_apri_elemento)
        self.tree_view.doubleClicked.connect(self.azione_apri_elemento) 
        self.shortcut_delete.activated.connect(self.cancella)
        self.shortcut_delete_backspace.activated.connect(self.cancella)       

        self.tree_view.setColumnHidden(1, False) 
        self.tree_view.setColumnHidden(2, True)  
        self.tree_view.setColumnHidden(3, False)
        self.tree_view.sortByColumn(0, Qt.SortOrder.AscendingOrder)
        self.tree_view.setDragDropMode(QTreeView.DragDropMode.InternalMove)
        
        self.tree_view.setSelectionMode(QTreeView.SelectionMode.ExtendedSelection)
        self.tree_view.setAnimated(True)
        self.tree_view.setIndentation(20)
        self.tree_view.setSortingEnabled(True)
        
        # Allarga la colonna del nome
        self.tree_view.header().resizeSection(0, 300)
        main_layout.addWidget(self.tree_view)
        # --- Bottoni ---
        buttons_layout = QHBoxLayout()
        
        self.btn_crea_mappa = self._crea_bottone("Crea Mappa",self.crea_mappe)
        self.btn_pulisci = self._crea_bottone("Pulisci", self.pulisci)
        self.btn_aggiorna = self._crea_bottone("Aggiorna", self.aggiorna)
        self.btn_crea = self._crea_bottone("Crea Appunti", self.crea)
        self.btn_carica = self._crea_bottone("Carica", self.carica)
        self.btn_pdf = self._crea_bottone("Scarica PDF", self.scarica_pdf)



        # Aggiungi i bottoni al layout
        buttons_layout.addWidget(self.btn_pulisci)
        buttons_layout.addWidget(self.btn_aggiorna)
        buttons_layout.addStretch() # Molla separatrice
        buttons_layout.addWidget(self.btn_crea_mappa)
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
        # --- Collegamento segnali backend ---

        self.file_manager_window.log.connect(self.on_log_message)
        self.file_manager_window.new_tab_ready.connect(self.on_new_tab_ready)

        
        self.file_manager_window._orc.operation_finished.connect(self.reset_gui_state)
        self.file_manager_window._orc.busy_changed.connect(self._imposta_stato_caricamento)
        self.file_manager_window._orc.operation_error.connect(self.on_log_message)
        main_layout.addWidget(self.log_area)
    def _imposta_stato_caricamento(self, occupato: bool):
        """
        Abilita o disabilita i bottoni in base allo stato del backend.

        Args:
            occupato (bool): True se il backend sta lavorando, False se è libero.
        """
        
        
        # Opzionale: puoi cambiare il cursore per far capire visivamente che sta caricando
        if occupato:
            self.setCursor(Qt.CursorShape.WaitCursor)

        else:
            self.setCursor(Qt.CursorShape.ArrowCursor)
    def _disabilita_crea(self):
        self.btn_crea.setDisabled(True)
        self.btn_crea_mappa.setDisabled(True)
        self.btn_carica.setDisabled(True)
        self.btn_pdf.setDisabled(True)

    def _disabilita_pulisci_aggiorna(self):
        self.btn_pulisci.setDisabled(True)
        self.btn_aggiorna.setDisabled(True)


    
    def on_new_tab_ready(self,obj,testo):
        self.new_tab_ready.emit(obj,testo)
    def on_log_message(self, message):
        """Chiamato dal segnale log scrive sulla finestra del Filemanagaer."""
        self.log_area.append(message)
    # Scrolla automaticamente in fondo
        self.log_area.verticalScrollBar().setValue(
            self.log_area.verticalScrollBar().maximum()
        )
        # Se hai una casella di testo nella GUI, fai: self.text_area.append(message)
        print(f"[GUI LOG] {message}") 

    def reset_gui_state(self):
        """Riporta i bottoni allo stato normale."""
        self.btn_aggiorna.setDisabled(False)
        self.btn_pulisci.setDisabled(False)
        self.btn_crea.setDisabled(False)
        self.btn_crea_mappa.setDisabled(False)
        self.btn_carica.setDisabled(False)
        self.btn_pdf.setDisabled(False)

        self.model.refresh_histories()
    def _crea_bottone(self,text: str,azione:Callable)->QPushButton:
        btn = QPushButton(text)
        btn.setFixedHeight(BTN_HEIGHT)
        btn.setStyleSheet("padding: 5px;")

        btn.clicked.connect(azione)

        return btn
    
    def dragEnterEvent(self, a0):
        """
        Accetazione del Drag Enter event guarda se l'evento di tipo Drag che entra nella finestra porta con se percorsi fisici

        Args :
            a0 (QDragEnterEvent) : è l'evento del mouse che incrocia la finestra dell'applicazione
        """
        if a0.mimeData().hasUrls():
            a0.accept()
        else:
            a0.ignore()

    def dropEvent(self, a0):
        """
        Gestisce il drop di file all'interno della finestra si occupa delle seguenti funzioni:
            1. Gestisce l'evento di Drop (è un'Override del DropEvent di Super() )
            2. Inserisce i file all'interno del file System
        Args:
            a0 (QDropEvent) : è l'evento da gestire
        """
        files = [u.toLocalFile() for u in a0.mimeData().urls()]
        testo_files = "\n".join([Path(f).name for f in files])
        self.mostra_messaggio(f"Hai caricato:\n{testo_files}")

    def _get_selected_paths(self, include_dirs: bool = False) -> list[Path]:
        """Estrae i percorsi dei file/cartelle selezionati nella TreeView."""
        indici = self.tree_view.selectedIndexes()
        paths = set()
        
        for index in indici:
            # Lavoriamo solo sulla colonna 0 per evitare duplicati 
            # (Qt crea un indice per ogni colonna della riga)
            if index.column() == 0:
                is_dir = self.model.isDir(index)
                if not is_dir or (is_dir and include_dirs):
                    paths.add(Path(self.model.filePath(index)))
                    
        return list(paths)
# ==== Azioni ====
    def cancella(self):
        """
        controlla gli indici selezionati , se questi sono files li cancella altrimenti no
        """
        indici = self.tree_view.selectedIndexes()

        
        if indici is not None:
            path_list = []
            for index in indici:
                if not self.model.isDir(index):
                    path_list.append(self.model.filePath(index))

            file_paths = list(Path(file) for file in set(path_list))
    

            self.deleter.delete_specific(file_paths)

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
            
            if file_path.lower().endswith('.pdf'):
                self.file_manager_window.open_pdf(file_path)
            elif file_path.lower().endswith('.mappa'):
                self.open_this_mappa.emit(file_path)

            else:
                # Usa QDesktopServices per aprire il file come se facessi doppio click
                # (Apre i TXT con l'editor di sistema, ecc.)
                QDesktopServices.openUrl(QUrl.fromLocalFile(file_path))

    def pulisci(self):
        """
        Elimina tutti i file che sono già stati elaborati presenti all'interno della storia
        """
        self.file_manager_window.pulisci()

    def aggiorna(self):
        """
        Entra nella root base di Notion e ricorsivamente esplora tutto il profilo
        """
        self._disabilita_pulisci_aggiorna()
        self._disabilita_crea()
        
        self.file_manager_window.aggiorna()
    def crea_mappe(self):
        """
        Inizia il processo di generazione di mappe
            1. Prende i file pdf selezionati
            2. Utilizza le API di Gemini per elaborare il file
            3. Riceve la risposta formattata pronta per essere inserita su Notion
        """
        self._disabilita_pulisci_aggiorna()
        self.log_area.clear()
        file_paths = self._get_selected_paths(include_dirs=False)
        
        if not file_paths:
            self.mostra_messaggio("Seleziona almeno un file audio o PDF per generare gli appunti.")
            return
            
        self.file_manager_window.crea(
            file_paths,
            is_map=True,
            is_pdf=True,
            json_mode=True,
            )

    def crea(self):
        """
        Inizia il processo di generazione appunti 
            1. Prende i file pdf selezionati
            2. Utilizza le API di Gemini per elaborare il file
            3. Riceve la risposta formattata pronta per essere inserita su Notion
        """
        self._disabilita_pulisci_aggiorna()

        self.log_area.clear()
        file_paths = self._get_selected_paths(include_dirs=False)
        
        if not file_paths:
            self.mostra_messaggio("Seleziona almeno un file audio o PDF per generare gli appunti.")
            return
            
        self.file_manager_window.crea(file_paths)

    def carica(self):
        """
        Carica le risposta all'interno della corrispondente pagina di Notion
        Funziona solamente se è già stata generato il contenuto per quel file PDF
        """

        file_paths = self._get_selected_paths(include_dirs=False)
        
        if not file_paths:
            self.mostra_messaggio("Seleziona almeno un file da caricare su Notion.")
            return
            
        self.file_manager_window.carica(file_paths)

    def scarica_pdf(self):
        """
        Ricorsivamente scarica e crea il pdf partendo dalla pagina di Notion selezionata.
        Funziona solamente se il file selezionato è una cartella
        """
        self._disabilita_pulisci_aggiorna()
        # Per il download PDF da Notion, il tuo FileActionHandler si aspetta le cartelle
        folder_paths = self._get_selected_paths(include_dirs=True)
        
        # Filtriamo tenendo solo le cartelle reali
        folder_paths = [p for p in folder_paths if p.is_dir()]
        
        if not folder_paths:
            self.mostra_messaggio("Seleziona almeno una cartella progetto per scaricare il PDF.")
            return
            
        self.file_manager_window.scarica_pdf(folder_paths)
    def mostra_messaggio(self, testo):
        msg = QMessageBox(self)
        msg.setWindowTitle("Info")
        msg.setText(testo)
        msg.exec()
    
if __name__ == "__main__":
    arg = sys.argv
    app = QApplication(arg)
    manager = Manager()
    
    manager.show()
    app.exec()

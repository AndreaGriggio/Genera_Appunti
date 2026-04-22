
import sys
from src.GUI.Core.Filemanager import FileManagerWindow
from src.GUI.MapTree.MapTreeGrid import Viewer, MapTreeGrid
from src.GUI.Core.SettingsDialog import open_settings
from src.GUI.MainHub.DockPanel import PannelloDock
from PyQt6.QtWidgets import QWidget, QMainWindow, QApplication
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QAction
import os


WIDTH = 1200
HEIGHT = 600
FILEMANAGER = "Filemanager"
MAPPA = "Mappa"
_SNAP_MAP = {
    Qt.DockWidgetArea.LeftDockWidgetArea:   (Qt.DockWidgetArea.RightDockWidgetArea,  Qt.Orientation.Horizontal),
    Qt.DockWidgetArea.RightDockWidgetArea:  (Qt.DockWidgetArea.LeftDockWidgetArea,   Qt.Orientation.Horizontal),
    Qt.DockWidgetArea.TopDockWidgetArea:    (Qt.DockWidgetArea.BottomDockWidgetArea, Qt.Orientation.Vertical),
    Qt.DockWidgetArea.BottomDockWidgetArea: (Qt.DockWidgetArea.TopDockWidgetArea,    Qt.Orientation.Vertical),
}


class Hub(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Main Hub")
        self.resize(WIDTH, HEIGHT)

        self.singleton_aperti = {}

        self.setDockOptions(
            QMainWindow.DockOption.AllowTabbedDocks |
            QMainWindow.DockOption.AnimatedDocks
        )
        # ==== MenuBar ====
        menuBar = self.menuBar()
        menuFinestre = menuBar.addMenu("Strumenti")



        azioni = [
            (FILEMANAGER, "Ctrl+F", FileManagerWindow, True),
            (MAPPA, "Ctrl+M", lambda: Viewer(MapTreeGrid()), False),
        ]

        for nome, shortcut, costruttore, is_singleton in azioni:
            azione = QAction(nome, self)
            azione.setShortcut(shortcut)
            azione.triggered.connect(
                lambda checked, n=nome, c=costruttore, s=is_singleton: 
                self.apri_widget(n, c, s)
            )
            menuFinestre.addAction(azione)

        azione_impostazioni = QAction("Impostazioni", self)
        azione_impostazioni.triggered.connect(self.apri_impostazioni)
        menuFinestre.addAction(azione_impostazioni)
        self.setDockOptions(QMainWindow.DockOption.AllowTabbedDocks | QMainWindow.DockOption.AnimatedDocks)
        # # ==== Tab centrale ====
        # self.icona_x = self.style().standardIcon(QStyle.StandardPixmap.SP_DialogCloseButton)
        # self.tab = DetachableTabWidget()
        # self.tab.setAcceptDrops(True)
        # self.setCentralWidget(self.tab)

    def apri_widget(self, titolo: str, costruttore, singleton: bool = True):
        if singleton:
            widget = self.singleton_aperti.get(titolo)
            if widget is None:
                widget = costruttore()
                self.singleton_aperti[titolo] = widget
                self._crea_e_aggancia_dock(widget, titolo)
        else:
            widget = costruttore()
            self._crea_e_aggancia_dock(widget, titolo)

    def _crea_e_aggancia_dock(self, widget: QWidget, titolo: str):
        """Delega la grafica al PannelloDock e lo inserisce nella UI"""
        
        dock = PannelloDock(titolo, widget, self)
        dock.chiuso.connect(self._gestisci_chiusura_pannello)
        
        dock.topLevelChanged.connect(
            lambda is_floating, d=dock:
                QTimer.singleShot(0, lambda: self._applica_snap(d))
                if not is_floating else None
        )

        # Posizionamento iniziale (Default)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, dock)


    def _applica_snap(self, dock:PannelloDock):
        """Gestisce i 3 casi di Snap in alto , destra e sinistra"""

        if dock.isFloating():
            return
        
        area = self.dockWidgetArea(dock)
        
        if area not in _SNAP_MAP:
            return
        
        area_opposta, orientazione = _SNAP_MAP[area]

        altri_dock = [
            d for d in self.findChildren(PannelloDock)
            if d is not dock and not d.isFloating()
            ]
        
        if not altri_dock:
            return
        
        ancora = altri_dock[0]
        self.addDockWidget(area_opposta, ancora)
        for d in altri_dock[1:]:
            self.tabifyDockWidget(ancora, d)
        ancora.raise_()
 
        meta = (self.width() if orientazione == Qt.Orientation.Horizontal
                else self.height()) // 2
 
        self.resizeDocks([dock, ancora], [meta, meta], orientazione)


    
    
    
    
    def _gestisci_chiusura_pannello(self, widget: QWidget, titolo: str):
        """Viene chiamata quando il PannelloDock emette il segnale 'chiuso'"""
        
        if titolo in self.singleton_aperti:
            del self.singleton_aperti[titolo]
            
        widget.deleteLater()
    def apri_impostazioni(self):
        changed = open_settings(parent=self)
        if changed:
            fm = self.singleton_aperti.get(FILEMANAGER)
            if fm is not None:
                fm.model.refresh_histories()
    # # ------------------------------------------------------------------
    # def apri_widget(self, titolo: str, costruttore, singleton: bool = True):
    #     if singleton:
    #         widget = self.singleton_aperti.get(titolo)
    #         if widget is None:
    #             widget = costruttore()
    #             self.singleton_aperti[titolo] = widget
    #             self._aggiungi_tab_interno(widget, titolo)
    #             # Pulisce il dizionario se il widget viene distrutto esternamente
    #             widget.destroyed.connect(lambda: self.singleton_aperti.pop(titolo, None))
    #     else:
    #         widget = costruttore()
    #         self._aggiungi_tab_interno(widget, titolo)

    # def _aggiungi_tab_interno(self, widget: QWidget, titolo: str):
    #     """Aggiunge il widget come tab e gli applica il bottone di chiusura."""
    #     indice = self.tab.addTab(widget, titolo)
    #     self._applica_bottone(indice, widget)

    # # ------------------------------------------------------------------
    # def _applica_bottone(self, indice: int, widget: QWidget):
    #     """
    #     Crea il bottone X e lo collega a chiudi_scheda passando il WIDGET,
    #     non l'indice — così funziona anche dopo riordini/rimozioni di tab.
    #     """
    #     btn_chiudi = QPushButton()
    #     btn_chiudi.setIcon(self.icona_x)
    #     btn_chiudi.setStyleSheet("background-color: transparent; border: none;")
    #     btn_chiudi.clicked.connect(lambda: self.chiudi_scheda(widget))
    #     self.tab.tabBar().setTabButton(indice, QTabBar.ButtonPosition.RightSide, btn_chiudi)

    # # ------------------------------------------------------------------
    # def chiudi_scheda(self, widget: QWidget):
    #     """Rimuove la tab corrispondente al widget e lo distrugge."""
    #     indice = self.tab.indexOf(widget)   # ✅ indice sempre aggiornato
    #     if indice != -1:
    #         self.tab.removeTab(indice)
    #     widget.deleteLater()                # ✅ rilascia la memoria correttamente

    # def safe_remove(self, widget: QWidget):
    #     """Rimozione sicura senza distruggere il widget (es. quando viene staccato)."""
    #     if widget is not None:
    #         indice = self.tab.indexOf(widget)
    #         if indice != -1:
    #             self.tab.removeTab(indice)

    # # ------------------------------------------------------------------
    # 

    # # ------------------------------------------------------------------
    # def aggiungi_tab(self, widget: QWidget, name: str):
    #     """API pubblica per aggiungere tab dall'esterno (es. tab staccate)."""
    #     self._aggiungi_tab_interno(widget, name)


if __name__ == "__main__":
    os.environ["QT_QPA_PLATFORM"] = "xcb"
    app = QApplication(sys.argv)
    window = Hub()
    window.show()
    sys.exit(app.exec())
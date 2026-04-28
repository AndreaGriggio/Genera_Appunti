
import sys
from src.GUI.Core.Manager import Manager
from src.GUI.MapTree.MapTreeGrid import Viewer, MapTreeGrid
from src.GUI.Core.SettingsDialog import open_settings
from src.GUI.MainHub.DockPanel import PannelloDock
from PyQt6.QtWidgets import QWidget, QMainWindow, QApplication
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QAction
import os
from pathlib import Path


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
            (FILEMANAGER, "Ctrl+F", Manager, True),
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
        

    def apri_widget(self, titolo: str, costruttore, singleton: bool = True):
        if singleton:
            widget = self.singleton_aperti.get(titolo)
            if widget is None:
                widget = costruttore()
                self.singleton_aperti[titolo] = widget
                self._crea_e_aggancia_dock(widget, titolo)
                if isinstance(widget,Manager):
                    widget.new_tab_ready.connect(self._crea_e_aggancia_dock)
                    widget.open_this_mappa.connect(self._open_mappa)
        else:
            widget = costruttore()
            self._crea_e_aggancia_dock(widget, titolo)
    def _open_mappa(self,file_path : str):
        
        path = Path(file_path)

        viewer = Viewer(
                        scene=MapTreeGrid(),
                        titolo = path.stem,
                        saving_path=path
                        )
        
        viewer.loader.process_file(path)
        
        self._crea_e_aggancia_dock(viewer,viewer.title)
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


if __name__ == "__main__":
    os.environ["QT_QPA_PLATFORM"] = "xcb"
    app = QApplication(sys.argv)
    window = Hub()
    window.show()
    sys.exit(app.exec())
from PyQt6.QtWidgets import QDockWidget, QWidget
from PyQt6.QtCore import pyqtSignal
from src.GUI.Core.Filemanager import FileManagerWindow
from src.GUI.MapTree.MapTreeGrid import Viewer

class PannelloDock(QDockWidget):
    chiuso = pyqtSignal(object, str) 

    def __init__(
            self,
            titolo: str,
            widget_interno: QWidget | FileManagerWindow | Viewer,
            parent=None
    ):
        super().__init__(titolo, parent)
        self.titolo = titolo
        self.widget_interno = widget_interno
        
        self.setWidget(self.widget_interno)
        
        self.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetClosable | 
            QDockWidget.DockWidgetFeature.DockWidgetMovable |
            QDockWidget.DockWidgetFeature.DockWidgetFloatable 
        )

    def closeEvent(self, event):
        self.chiuso.emit(self.widget_interno, self.titolo)
        super().closeEvent(event)
from PyQt6.QtWidgets import QTabWidget, QTabBar, QMainWindow
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QCursor

# 1. Creiamo una TabBar personalizzata che "ascolta" il mouse
class DetachableTabBar(QTabBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.drag_start_pos = QPoint()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_start_pos = event.pos()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if not self.drag_start_pos.isNull():
             if not self.contentsRect().contains(event.pos()):
                tab_index = self.tabAt(self.drag_start_pos)
                if tab_index >= 0:
                    self.parentWidget().detach_tab(tab_index, QCursor.pos())
                    self.drag_start_pos = QPoint() 
        super().mouseMoveEvent(event)

class DetachableTabWidget(QTabWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setTabBar(DetachableTabBar(self))
        self.detached_windows = []

    def detach_tab(self, index, global_pos):
        widget_to_detach = self.widget(index)
        tab_name = self.tabText(index)

        self.removeTab(index)

        widget_to_detach.setParent(None)
        

        widget_to_detach.setWindowTitle(tab_name)
        widget_to_detach.resize(800, 600)
        widget_to_detach.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)

        self.detached_windows.append(widget_to_detach)
        widget_to_detach.destroyed.connect(lambda: self.clean_detached_list(widget_to_detach))
        

        widget_to_detach.move(global_pos)
        widget_to_detach.show()
    def clean_detached_list(self, window_reference):
        """Pulisce la lista dalle finestre chiuse per non saturare la memoria."""
        if window_reference in self.detached_windows:
            self.detached_windows.remove(window_reference)
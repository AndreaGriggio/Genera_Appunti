from typing import Any

from PyQt6.QtWidgets import QGraphicsTextItem,QMenu,QInputDialog,QGraphicsItem
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QGraphicsTextItem, QGraphicsItem, QMenu, QStyleOptionGraphicsItem,QWidget
from PyQt6.QtGui import QPainter, QPen, QColor,QBrush
from PyQt6.QtCore import Qt,QPointF

class TextItem(QGraphicsTextItem):
    MARGIN = 10
    WIDTH = 1
    BORDER_COLOR = QColor(0,0,0)
    FILL_COLOR = QColor(50,50,50)
    def __init__(self,text:str,border_color : QColor | None,margin=None,fill=None):
        super().__init__(text)
        self.connected_lines = []
        self.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
        
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)
        
        self.forma = "rettangolo" 
        if border_color:
            self.border_color = border_color
        else :
            self.border_color = self.BORDER_COLOR
        if margin :
            self.margin = margin
        else :
            self.margin = self.MARGIN
        if fill:
            self.fill = fill
        else :
            self.fill = self.FILL_COLOR
        self.bordo = True
        self.document().setDocumentMargin(self.margin)

    def mouseDoubleClickEvent(self, event):
        self.setTextInteractionFlags(Qt.TextInteractionFlag.TextEditorInteraction)
        self.setFocus()
        super().mouseDoubleClickEvent(event)

    def focusOutEvent(self, event):
        self.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
        self.toPlainText()
        super().focusOutEvent(event)

    def paint(self, painter: QPainter | None, option : QStyleOptionGraphicsItem | None, widget : QWidget | None):
        
        
        sfondo = QBrush(self.FILL_COLOR)
        painter.setBrush(sfondo)
        rect = self.boundingRect()
        if self.bordo :
            pen = QPen(self.border_color)
            pen.setWidth(self.WIDTH)
            painter.setPen(pen)
        else :
            painter.setPen(Qt.PenStyle.NoPen)
        if self.forma == "rettangolo":
            painter.drawRect(rect)
        elif self.forma == "ellisse":
            painter.drawEllipse(rect)
            
        super().paint(painter, option, widget)

    def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value: Any) -> Any:
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange and self.scene():
            snap_strength = self.scene().SNAP
        
            nuova_x = round(value.x() / snap_strength) * snap_strength
            nuova_y = round(value.y() / snap_strength) * snap_strength
            
            for linea in self.connected_lines:
                linea.aggiorna_posizione()

            return QPointF(nuova_x, nuova_y)
        
        return super().itemChange(change,value)
    
    def contextMenuEvent(self,event):
        menu = QMenu()

        #==== Azioni del menu ====

        azione_modifica = menu.addAction("Modifica contenuto")
        azione_bordi = menu.addAction("Toggle Bordi")
        azione_forma = menu.addAction("Cambia Forma")
        azione_bordi.setShortcut("Ctrl+t")
        azione_forma.setShortcut("Ctrl+b")
        azione_modifica.setShortcut("Double Click")
        
        menu.addSeparator()
        azione_elimina = menu.addAction("Elimina")
        
        azione_scelta = menu.exec(event.screenPos())

        if azione_scelta == azione_modifica:
            nuovo_testo, confermato = QInputDialog.getText(
                None,                       
                "Modifica Blocco",          
                "Inserisci il nuovo testo:",
                text=self.toPlainText()     
            )

            if confermato:
                self.setPlainText(nuovo_testo)
        elif azione_scelta == azione_bordi:
            self.forma_bordo = "nessuno"
            self.update()
        
        elif azione_scelta == azione_forma :
            self.toggle_forma()
            
        elif azione_scelta == azione_elimina:

            if self.scene():
                self.scene().removeItem(self)
                
        event.accept()


    def toggle_forma(self):
        if self.forma == "rettangolo":
            self.forma = "ellisse"
        elif self.forma == "ellisse":
            self.forma = "rettangolo"
            
        self.update()
    
    def toggle_bordo(self):
        if self.bordo:
            self.bordo = False
        else :
            self.bordo = True

        self.update()






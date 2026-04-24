from typing import Any

from PyQt6.QtWidgets import QGraphicsTextItem,QMenu,QInputDialog,QGraphicsItem
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QGraphicsTextItem, QGraphicsItem, QMenu, QStyleOptionGraphicsItem,QWidget
from PyQt6.QtGui import QPainter, QPen, QColor,QBrush
from PyQt6.QtCore import Qt,QPointF
from src.GUI.MapTree.Element import Element
from src.GUI.MapTree.Node import Node
class TextItem(QGraphicsTextItem):
    MARGIN = 10
    WIDTH = 1
    BORDER_COLOR = QColor(0,0,0)
    FILL_COLOR = QColor(50,50,50)
    def __init__(self,text:str,border_color : QColor | None,margin=None ,fill=None,id = 0 ):
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
        self.id = id
        self.bordo = True
        self.is_pdf_export = False
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
        
        # 1. Scegliamo i colori in base allo stato attuale
        if getattr(self, 'is_pdf_export', False):
            sfondo = QBrush(Qt.GlobalColor.white)
            colore_bordo = Qt.GlobalColor.black
        else:
            sfondo = QBrush(self.fill)
            colore_bordo = self.border_color

        # 2. Applichiamo lo sfondo
        painter.setBrush(sfondo)
        
        # 3. Gestiamo il bordo
        rect = self.boundingRect()
        if self.bordo or getattr(self, 'is_pdf_export', False):
            # Forziamo il bordo visibile nel PDF per non perdere i confini dei nodi bianchi
            pen = QPen(colore_bordo)
            pen.setWidth(self.WIDTH)
            painter.setPen(pen)
        else:
            painter.setPen(Qt.PenStyle.NoPen)
            
        # 4. Disegniamo la forma
        if self.forma == "rettangolo":
            painter.drawRect(rect)
        elif self.forma == "ellisse":
            painter.drawEllipse(rect)
            
        # 5. Lasciamo che la classe madre disegni il testo sopra la forma
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
        azione_nascondi = menu.addAction("Nascondi connected")
        azione_mostra = menu.addAction("Mostra connected")

        
        azione_bordi.setShortcut("Ctrl+t")
        azione_forma.setShortcut("Ctrl+b")
        azione_modifica.setShortcut("Double Click")
        azione_nascondi.setShortcut("Ctrl+n")
        azione_mostra.setShortcut("Ctrl+m")

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
        elif azione_scelta == azione_nascondi:
            self.hide()
        elif azione_scelta == azione_mostra:
            self.show()       
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
    def hide(self,visitati = None):
        if visitati is None:
            visitati = set() 
            
        if self in visitati:
            return
            
        visitati.add(self)
        
        for linea in self.connected_lines:
            linea.setVisible(False)
            
            if linea.node_end and linea.node_end != self:
                linea.node_end.setVisible(False)
                linea.node_end.hide(visitati)
        
    def show(self,visitati=None):
        if visitati is None:
            visitati = set() 
            
        if self in visitati:
            return
            
        visitati.add(self)
        
        for linea in self.connected_lines:
            linea.setVisible(True)
            
            if linea.node_end and linea.node_end != self:
                linea.node_end.setVisible(True)
                linea.node_end.show(visitati)
            

    def getElement(self)->Element | None:

        pos = self.scenePos()

        border_hex = self.border_color.name() if hasattr(self.border_color, 'name') else str(self.border_color)
        fill_hex = self.fill.name() if hasattr(self.fill, 'name') else str(self.fill)

        return Element(pos.x(), pos.y(), border_hex, self.margin, fill_hex, self.id, self.toPlainText())
    def getNeighbours(self)->list[tuple[int,str]] | None:
        
        neighbours : list[tuple[int,str]] = []
        if not self.connected_lines:
            return None
        
        for line in self.connected_lines:
    
            #Ora devo controllare se il nodo di start sono io se si allora inserisco nella tupla il nodo end altrimenti no
            if line.node_start == self and line.node_end is not None:
                neighbours.append((line.node_end.id,line.tipo))
        return neighbours

    def getNode(self)-> Node:
        return Node(self.getElement(),self.getNeighbours())
    def prepara_per_pdf(self, in_esportazione: bool):
        """Attiva o disattiva la modalità di stampa in bianco e nero."""
        self.is_pdf_export = in_esportazione
        
        if in_esportazione:
            # Testo nero per il PDF
            self.setDefaultTextColor(Qt.GlobalColor.black)
        else:
            # Ripristina il testo chiaro (assumendo che il tuo default sia bianco/grigio)
            # Cambia questo colore se il tuo testo di base è diverso
            self.setDefaultTextColor(Qt.GlobalColor.white) 
            
        # Diciamo a Qt di ridisegnare l'elemento chiamando paint()
        self.update()

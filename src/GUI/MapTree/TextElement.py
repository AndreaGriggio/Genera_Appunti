
from PyQt6.QtWidgets import QGraphicsSceneMouseEvent, QGraphicsTextItem,QMenu,QInputDialog,QGraphicsItem
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QGraphicsTextItem, QGraphicsEllipseItem, QGraphicsItem, QMenu, QStyleOptionGraphicsItem,QWidget
from PyQt6.QtGui import QPainter, QPen, QColor,QBrush,QTextOption
from PyQt6.QtCore import Qt,QPointF
from src.GUI.MapTree.Element import Element
from src.GUI.MapTree.Node import Node,Connection
from src.GUI.MapTree.Point import Point
from enum import Enum
from typing import Any
class Orientation(Enum):
    N = "N"
    S = "S"
    E = "E"
    W = "W"
class AttachPoint(QGraphicsEllipseItem):
    RADIUS = 3

    def __init__(self, x:float = 0, y:float = 0, w:float = RADIUS, h:float = RADIUS, parent=None,orientation : Orientation = Orientation.N):
        super().__init__(x, y, w, h, parent)
        self.id = self._getParentId()
        self.setBrush(Qt.GlobalColor.black)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)
        self.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
        self.connected_lines: list  = []
        self.orientation: Orientation = orientation

    def attach_line(self,line):
        self.connected_lines.append(line)
    def detach_line(self,line):
        if line in self.connected_lines :
            self.connected_lines.remove(line)
    
    def _getParentId(self):
        parent = self.parentItem()
        if parent is not None:
            if isinstance(parent,TextItem):
                return parent.id
        return None

    def hide(self):
        self.setVisible(False)

    def show(self):
        self.setVisible(True)

    def getPoint(self)-> Point | None:
        pos = self.scenePos()
        if pos is not None:
            return Point(pos.x(),pos.y())
        else: 
            return None
class BaseItem:
    """
    Mixin che fornisce la logica di connessione (punti di attacco e linee)
    a qualsiasi QGraphicsItem.
    Presuppone che la classe figlia sia un QGraphicsItem (che possiede scenePos, boundingRect, ecc.).
    """
    
    def init_connections(self):
        """Da chiamare nell'__init__ della classe figlia dopo aver settato le dimensioni."""
        self._createPoints()
        self.hide_points()

    def get_nearest_point(self, pos: QPointF) -> 'AttachPoint | None':
        if not hasattr(self, 'attach_points') or not self.attach_points:
            return None
        
        nearest_point = None
        min_distance = float('inf')

        for _, point in self.attach_points.items():
            point_pos = point.scenePos() + QPointF(point.boundingRect().width() / 2, point.boundingRect().height() / 2)
            distance = (point_pos - pos).manhattanLength()

            if distance < min_distance:
                min_distance = distance
                nearest_point = point

        return nearest_point
    def distruggi_linee_connesse(self):
        """Trova tutte le linee connesse ai punti di questo item e le elimina dalla scena."""
        if not hasattr(self, 'attach_points'):
            return
            
        # 1. Raccogliamo in un set per evitare modifiche durante l'iterazione
        linee_da_rimuovere = set()
        for point in self.attach_points.values():
            for linea in point.connected_lines:
                linee_da_rimuovere.add(linea)
                
        # 2. Ordiniamo a ogni linea di fare la sua procedura di rimozione sicura
        for linea in linee_da_rimuovere:
            linea.rimuovi_sicuro()
    def _createPoints(self):
        r = AttachPoint.RADIUS
        self.attach_points: dict[Orientation, AttachPoint] = {}

        for orientation in Orientation:
            point = AttachPoint(-r, -r, 2*r, 2*r, parent=self, orientation=orientation)
            self.attach_points[orientation] = point

        self._update_points()

    def _update_points(self):
        if not hasattr(self, 'attach_points'):
            return

        r = AttachPoint.RADIUS
        rect = self.boundingRect()
        w = rect.width()
        h = rect.height()

        positions = {
            Orientation.N: QPointF(w / 2,  0),
            Orientation.S: QPointF(w / 2,  h),
            Orientation.E: QPointF(w,       h / 2),
            Orientation.W: QPointF(0,       h / 2),
        }

        for orientation, point in self.attach_points.items():
            point.setPos(positions[orientation])
            for line in point.connected_lines:
                line.aggiorna_posizione()

    def show_points(self):
        for _, point in self.attach_points.items():
            point.show()

    def hide_points(self):
        for _, point in self.attach_points.items():
            point.hide()

    def hide_connected(self, visitati=None):
        """Rinominato per non sovrascrivere il metodo hide() nativo di QGraphicsItem"""
        if visitati is None:
            visitati = set() 
            
        if self in visitati:
            return
            
        visitati.add(self)
        
        for point in self.attach_points.values():
            for linea in point.connected_lines:
                linea.setVisible(False)
                other = linea.node_end.parentItem() if linea.node_start is point else linea.node_start.parentItem()
                # Verifica basata sul Mixin, non sul TextItem
                if isinstance(other, BaseItem) and other != self:
                    other.setVisible(False)
                    other.hide_connected(visitati)

    def show_connected(self, visitati=None):
        """Rinominato per non sovrascrivere il metodo show() nativo di QGraphicsItem"""
        if visitati is None:
            visitati = set() 
            
        if self in visitati:
            return
            
        visitati.add(self)
        
        for point in self.attach_points.values():
            for linea in point.connected_lines:
                linea.setVisible(True)
                other = linea.node_end.parentItem() if linea.node_start is point else linea.node_start.parentItem()
                
                if isinstance(other, BaseItem) and other != self:
                    other.setVisible(True)
                    other.show_connected(visitati)

    def getNeighbours(self) -> list[Connection] | None:
        neighbours: list[Connection] = []

        for orientation, point in self.attach_points.items():
            for line in point.connected_lines:
                if line.node_start is point:
                    end_point = line.node_end
                    if end_point is None:
                        continue
                    parent = end_point.parentItem()
                    # Controlla se il vicino è collegabile (Testo o Immagine)
                    if isinstance(parent, ConnectableMixin):
                        neighbours.append(Connection(
                            target_id=parent.id,  # Assume che le classi figlie abbiano 'id'
                            tipo=line.tipo,
                            attachment={
                                "orientation_start": orientation.value,
                                "orientation_end": end_point.orientation.value
                            }
                        ))

        return neighbours if neighbours else None
class TextItem(QGraphicsTextItem,BaseItem):
    MARGIN = 10
    WIDTH = 1
    BORDER_COLOR = QColor(0,0,0)
    FILL_COLOR = QColor(50,50,50)
    def __init__(self,text:str,border_color : QColor | None,margin=None ,fill=None,id = 0 ):
        super().__init__(text)
        
        self.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
        
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)
        
        option = QTextOption()
        option.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.document().setDefaultTextOption(option)

        self.document().contentsChanged.connect(self.adjust_size)
        
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
        super().init_connections()  

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent | None) -> None:
        self.setFocus()
        self.show_points()
        return super().mousePressEvent(event)
    
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

        if self.bordo :
            # Forziamo il bordo visibile nel PDF per non perdere i confini dei nodi bianchi
            pen = QPen(colore_bordo)
            pen.setWidth(self.WIDTH)
            painter.setPen(pen)
        else :
            painter.setPen(Qt.PenStyle.NoPen)
 
            
        # 4. Disegniamo la forma
        if self.forma == "rettangolo":
            painter.drawRect(rect)
        elif self.forma == "ellisse":
            painter.drawEllipse(rect)
   
        # 5. Lasciamo che la classe madre disegni il testo sopra la forma
        super().paint(painter, option, widget)

    def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value: Any) -> Any:
        if change == QGraphicsItem.GraphicsItemChange.ItemSelectedChange and self.scene():
            if not value:  # sta per essere deselezionato
                self.hide_points()
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange and self.scene():
            snap_strength = self.scene().SNAP
        
            nuova_x = round(value.x() / snap_strength) * snap_strength
            nuova_y = round(value.y() / snap_strength) * snap_strength
            
            for _,points in self.attach_points.items():
                for line in points.connected_lines:
                    line.aggiorna_posizione()

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

        
        azione_bordi.setShortcut("Ctrl+h")
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
            self.toggle_bordo()
        
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

    def getElement(self)->Element | None:

        pos = self.scenePos()

        border_hex = self.border_color.name() if hasattr(self.border_color, 'name') else str(self.border_color)
        fill_hex = self.fill.name() if hasattr(self.fill, 'name') else str(self.fill)

        return Element(pos.x(), pos.y(), border_hex, self.margin, fill_hex, self.id, self.toPlainText())
    def getNeighbours(self) -> list[Connection] | None:
        from src.GUI.MapTree.Node import Connection
        neighbours: list[Connection] = []

        for orientation, point in self.attach_points.items():
            for line in point.connected_lines:
                if line.node_start is point:
                    end_point = line.node_end
                    if end_point is None:
                        continue
                    parent = end_point.parentItem()
                    if isinstance(parent, TextItem):
                        neighbours.append(Connection(
                            target_id=parent.id,
                            tipo=line.tipo,
                            arrow_start = line.arrow_start,
                            arrow_end = line.arrow_end,
                            attachment={
                                "orientation_start": orientation.value,
                                "orientation_end": end_point.orientation.value
                            }
                        ))

        return neighbours if neighbours else None

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
    def adjust_size(self):
        self.setTextWidth(-1)
        
        ideal_width = self.document().idealWidth()
        
        self.setTextWidth(ideal_width)
        
        self._update_points()





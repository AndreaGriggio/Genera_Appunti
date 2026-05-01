import math

from PyQt6.QtWidgets import QGraphicsPathItem, QGraphicsItem
from PyQt6.QtGui import QPainterPath, QPen, QColor,QPainterPathStroker, QPolygonF
from PyQt6.QtCore import QPointF,Qt
from src.GUI.MapTree.TextElement import TextItem,AttachPoint

class LineItem(QGraphicsPathItem):
    LINE_COLOR = QColor(0, 0, 0)

    def __init__(self, node_start  : AttachPoint | None = None,
                       node_end    : AttachPoint | None = None,
                       arrow_start : bool = False,
                       arrow_end   : bool = False,
                       tipo="spline"):
        super().__init__()
        self.node_start = node_start
        self.node_end = node_end
        self.tipo = tipo
        self.arrow_start = arrow_start
        self.arrow_end = arrow_end

        pen = QPen(self.LINE_COLOR)
        pen.setWidth(1)
        self.setPen(pen)
        self.setZValue(-1)
        self.aggiorna_posizione()
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.aggiorna_posizione()
    def _draw_arrow(self, painter, p_tip, p_base):
        """Funzione helper per disegnare una singola freccia date le coordinate della punta e della base."""
        dx = p_tip.x() - p_base.x()
        dy = p_tip.y() - p_base.y()
        angolo_radianti = math.atan2(dy, dx)

        arrow_size = 12.0
        arrow_head = QPolygonF([
            QPointF(0, 0),
            QPointF(-arrow_size, arrow_size / 2.5),
            QPointF(-arrow_size, -arrow_size / 2.5)
        ])

        painter.save()
        painter.translate(p_tip)
        painter.rotate(math.degrees(angolo_radianti))
        painter.setBrush(self.LINE_COLOR)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawPolygon(arrow_head)
        painter.restore()
    def paint(self, painter, option, widget=None):
        super().paint(painter, option, widget)

        path = self.path()
        if path.length() == 0 or self.node_start is None or self.node_end is None:
            return

        # Disegna freccia alla fine
        if self.arrow_end:
            p_end = path.pointAtPercent(1.0)
            p_before_end = path.pointAtPercent(0.99)
            self._draw_arrow(painter, p_end, p_before_end)

        
        if self.arrow_start:
            p_start = path.pointAtPercent(0.0)
            p_after_start = path.pointAtPercent(0.01)
            self._draw_arrow(painter, p_start, p_after_start)
    def rimuovi_sicuro(self):
        """Scollega la linea da entrambi i nodi e la rimuove dalla scena in sicurezza."""
        if self.node_start:
            try:
                self.node_start.detach_line(self)
            except RuntimeError:
                pass # Ignora se l'oggetto C++ è già stato distrutto
            self.node_start = None
            
        if self.node_end:
            try:
                self.node_end.detach_line(self)
            except RuntimeError:
                pass
            self.node_end = None
            
        if self.scene():
            self.scene().removeItem(self)
    def aggiorna_posizione(self):
        """Ricalcola il path usando i nodi collegati. Gestisce il caso in cui uno o entrambi siano None."""

        if self.node_start is not None and self.node_end is not None:

            self._draw_path(self.node_start.scenePos(),
                            self.node_end.scenePos())


    def update_using_qpoint(self, p1: QPointF, p2: QPointF):
        """Disegna il path tra due QPointF arbitrari (usato durante il trascinamento)."""
        self._draw_path(p1, p2)

    def _draw_path(self, centro_start: QPointF, centro_end: QPointF):
        path = QPainterPath() 
        path.moveTo(centro_start)

        if self.tipo == "spline":
            dx = centro_end.x() - centro_start.x()

            tensione = 0.5
            
            offset_x = dx * tensione

            p1 = QPointF(centro_start.x() + offset_x, centro_start.y())
            p2 = QPointF(centro_end.x()   - offset_x, centro_end.y())
            path.cubicTo(p1, p2, centro_end)
        elif self.tipo == "retta":
            delta_x = abs(centro_end.x() - centro_start.x())
            delta_y = abs(centro_end.y() - centro_start.y())
            if delta_x < delta_y and delta_x < 15:  # Soglia di 20px per forzare la perpendicolarità verticale
                centro_end.setX(centro_start.x())
            elif delta_y < delta_x and delta_y < 15:  # Soglia di 20px per forzare la perpendicolarità orizzontale
                centro_end.setY(centro_start.y())
            path.lineTo(centro_end)

        self.setPath(path)

    def is_click_near_node(self, node : AttachPoint | None, pos: QPointF, threshold: float =100) -> bool:
        """
        Restituisce True se 'pos' è entro 'threshold' pixel dal centro del nodo.
        Null-safe: se node è None restituisce False.
        La soglia default è 20px (molto più usabile di 5px).
        """
        if node is None:
            return False
        pos_node = node.scenePos() + node.boundingRect().center()
        dx = pos.x() - pos_node.x()
        dy = pos.y() - pos_node.y()
        return (dx * dx + dy * dy) ** 0.5 < threshold
    
    def shape(self) -> QPainterPath:
        """
        Area di click più larga del path visivo.
        QPainterPathStroker crea un'area attorno al path esistente.
        """
        stroker = QPainterPathStroker()
        stroker.setWidth(12)          
        stroker.setCapStyle(Qt.PenCapStyle.RoundCap)
        stroker.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        return stroker.createStroke(self.path())
    def hide(self):
        self.setVisible(False)

    def show(self):
        self.setVisible(True)
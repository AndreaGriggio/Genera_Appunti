from PyQt6.QtWidgets import QGraphicsPathItem, QGraphicsItem
from PyQt6.QtGui import QPainterPath, QPen, QColor
from PyQt6.QtCore import QPointF


class LineItem(QGraphicsPathItem):
    LINE_COLOR = QColor(0, 0, 0)

    def __init__(self, node_start=None, node_end=None, tipo="spline"):
        super().__init__()
        self.node_start = node_start
        self.node_end = node_end
        self.tipo = tipo

        pen = QPen(self.LINE_COLOR)
        pen.setWidth(1)
        self.setPen(pen)
        self.setZValue(-1)
        self.aggiorna_posizione()
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)

    def aggiorna_posizione(self):
        """Ricalcola il path usando i nodi collegati. Gestisce il caso in cui uno o entrambi siano None."""
        if isinstance(self.node_start, QGraphicsItem) and isinstance(self.node_end, QGraphicsItem):
            centro_start = self.node_start.scenePos() + self.node_start.boundingRect().center()
            centro_end   = self.node_end.scenePos()   + self.node_end.boundingRect().center()
            self._draw_path(centro_start, centro_end)

    def update_using_qpoint(self, p1: QPointF, p2: QPointF):
        """Disegna il path tra due QPointF arbitrari (usato durante il trascinamento)."""
        self._draw_path(p1, p2)

    def _draw_path(self, centro_start: QPointF, centro_end: QPointF):
        path = QPainterPath()
        path.moveTo(centro_start)

        if self.tipo == "spline":
            distanza_x = abs(centro_end.x() - centro_start.x()) / 2
            p1 = QPointF(centro_start.x() + distanza_x, centro_start.y())
            p2 = QPointF(centro_end.x()   - distanza_x, centro_end.y())
            path.cubicTo(p1, p2, centro_end)
        elif self.tipo == "retta":
            path.lineTo(centro_end)

        self.setPath(path)

    def is_click_near_node(self, node, pos: QPointF, threshold: float =100) -> bool:
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

    def hide(self):
        self.setVisible(False)

    def show(self):
        self.setVisible(True)
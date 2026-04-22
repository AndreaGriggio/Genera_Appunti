from PyQt6.QtWidgets import QGraphicsPathItem,QGraphicsItem
from PyQt6.QtGui import QPainterPath, QPen, QColor
from PyQt6.QtCore import QPointF

class LineItem(QGraphicsPathItem):
    LINE_COLOR = QColor(0,0,0)
    def __init__(self, node_start=None  , node_end=None,tipo="spline"):
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
        """Ricalcola il percorso della linea basandosi sulla posizione attuale dei nodi"""
        
        if isinstance(self.node_end,QGraphicsItem) and isinstance(self.node_start,QGraphicsItem): 
            #====Implementazione disegno linea con starting e ending point come TextItem====
            
            centro_start = self.node_start.scenePos() + self.node_start.boundingRect().center()
            centro_end = self.node_end.scenePos() + self.node_end.boundingRect().center()

            path = QPainterPath()
            path.moveTo(centro_start)

            if self.tipo == "spline":
                distanza_x = abs(centro_end.x() - centro_start.x()) / 2
                
                punto_controllo_1 = QPointF(centro_start.x() + distanza_x, centro_start.y())
                punto_controllo_2 = QPointF(centro_end.x() - distanza_x, centro_end.y())

                path.cubicTo(punto_controllo_1, punto_controllo_2, centro_end)
                
            elif self.tipo == "retta":
                path.lineTo(centro_end)
            self.setPath(path)
             
    def update_using_qpoint(self,p1:QPointF,p2:QPointF):
            centro_start = p1 
            centro_end = p2

            path = QPainterPath()
            path.moveTo(centro_start)

            distanza_x = abs(centro_end.x() - centro_start.x()) / 2
            
            punto_controllo_1 = QPointF(centro_start.x() + distanza_x, centro_start.y())
            punto_controllo_2 = QPointF(centro_end.x() - distanza_x, centro_end.y())

            path.cubicTo(punto_controllo_1, punto_controllo_2, centro_end)
            self.setPath(path)
    def hide(self):
        self.setVisible(False)

    def show(self):
        self.setVisible(True)
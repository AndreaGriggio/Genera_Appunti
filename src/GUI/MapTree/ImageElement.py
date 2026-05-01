from typing import Any
        
from PyQt6.QtWidgets import QGraphicsPixmapItem,QGraphicsItem,QGraphicsSceneMouseEvent
from PyQt6.QtGui import QPixmap
from src.GUI.MapTree.TextElement import BaseItem,AttachPoint,Orientation
from PyQt6.QtCore import Qt ,QPointF,QByteArray, QBuffer, QIODevice
import base64

class ImageItem(QGraphicsPixmapItem,BaseItem):
    def __init__(self, pixmap: QPixmap, id: int = 0):
        super().__init__(pixmap)
        self.vertices: dict[Orientation, AttachPoint] = {}
        self.id = id
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)
        self.setTransformationMode(Qt.TransformationMode.SmoothTransformation)
        self._pixmap_data: bytes = b""
        self._pixmap_copy: QPixmap = pixmap.copy()

        super().init_connections()
        self.create_points_on_vertices()
        self.show()
        self.resizing = False
        self.starting_pos = None
        # Dimensioni al momento del click, non del pixmap originale
        self._resize_start_w: int = pixmap.width()
        self._resize_start_h: int = pixmap.height()
        

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent | None) -> None:
        self.setFocus()
        self.show_points()
        
        pos = event.scenePos() 
        
        if event.button() == Qt.MouseButton.LeftButton:
            
            clicked_handle = self.get_resize_handle(pos)
            
            if clicked_handle is not None:
                self.resizing = True
                self.starting_pos = pos
                
                self.active_resize_handle = clicked_handle 
                
                self.original_width = self.pixmap().width()
                self.original_height = self.pixmap().height()
                
                event.accept()
                return
            
        return super().mousePressEvent(event)
    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent | None) -> None:
        if self.resizing:
            if self.starting_pos is None:
                return
            delta = event.scenePos() - self.starting_pos
            
           
            new_width = int(max(10, self.original_width + delta.x()))
            new_height = int(max(10, self.original_height + delta.y()))
            
            
            scaled_pixmap = self._pixmap_copy.scaled(
                new_width, 
                new_height, 
                Qt.AspectRatioMode.KeepAspectRatio, 
                Qt.TransformationMode.FastTransformation
            )
            self.setPixmap(scaled_pixmap)
            self.update_vertices()
            self._update_points()
            event.accept()
            return
        
        return super().mouseMoveEvent(event)
    def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value: Any) -> Any:
        if change == QGraphicsItem.GraphicsItemChange.ItemSelectedChange and self.scene():
            if not value:  # sta per essere deselezionato
                self.hide_points()
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange and self.scene():
            snap_strength = self.scene().SNAP
        
            nuova_x = round(value.x() / snap_strength) * snap_strength
            nuova_y = round(value.y() / snap_strength) * snap_strength
            
            return QPointF(nuova_x, nuova_y)

        # 2. Aggiorna le linee (avviene DOPO che lo spostamento e lo snap sono effettivi)
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            for _, points in self.attach_points.items():
                for line in points.connected_lines:
                    line.aggiorna_posizione()
        
        return super().itemChange(change,value)
        
    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent | None) -> None:
        if self.resizing:
            self.resizing = False
            if self.starting_pos is None:
                return
            
            delta = event.scenePos() - self.starting_pos
            new_width = int(max(10, self.original_width + delta.x()))
            new_height = int(max(10, self.original_height + delta.y()))
            
            final_pixmap = self._pixmap_copy.scaled(
                new_width, 
                new_height, 
                Qt.AspectRatioMode.KeepAspectRatio, 
                Qt.TransformationMode.SmoothTransformation
            )
            self.setPixmap(final_pixmap)
            self.update_vertices()
            self._update_points()
            self.hide_points()

            self.starting_pos = None

            
            event.accept()
            return
            
        return super().mouseReleaseEvent(event)

    def get_resize_handle(self, pos: QPointF, threshold: float = 15.0) -> Orientation | None:
        """
        Trova il vertice più vicino alla posizione del mouse.
        Restituisce l'Orientation corrispondente, oppure None se fuori soglia.
        """
        if not self.vertices:
            return None

        closest_orientation = None
        min_distance = float('inf')

        # Iteriamo dentro per trovare il minimo assoluto
        for orientation, point in self.vertices.items():
            distanza = (point.scenePos() - pos).manhattanLength()
            if distanza < min_distance:
                min_distance = distanza
                closest_orientation = orientation

        # Restituiamo il risultato solo se abbiamo cliccato abbastanza vicino
        if min_distance <= threshold:
            return closest_orientation
            
        return None
    @classmethod
    def from_file(cls, path: str, id: int = 0) -> "ImageItem":
        with open(path, "rb") as f:
            data = f.read()
        pixmap = QPixmap()
        pixmap.loadFromData(data)
        item = cls(pixmap, id)
        item._pixmap_data = data
        return item
    

    def to_dict(self) -> dict:
        
        byte_array = QByteArray()
        buffer = QBuffer(byte_array)
        buffer.open(QIODevice.OpenModeFlag.WriteOnly)
        self._pixmap_copy.save(buffer, "PNG") # Usa la copia originale incontaminata
        
        encoded = base64.b64encode(byte_array.data()).decode("utf-8")
        pos = self.scenePos()
        
        return {
            "type": "image",
            "id": self.id,
            "x": pos.x(),
            "y": pos.y(),
            "width": self.pixmap().width(),
            "height": self.pixmap().height(),
            "data": encoded            
        }

    @classmethod
    def from_dict(cls, d: dict) -> "ImageItem":
        raw = base64.b64decode(d["data"])
        pixmap = QPixmap()
        pixmap.loadFromData(raw, "PNG")
        
        item = cls(pixmap, d["id"])

        scaled_pixmap = item._pixmap_copy.scaled(
            d["width"], 
            d["height"], 
            Qt.AspectRatioMode.KeepAspectRatio, 
            Qt.TransformationMode.SmoothTransformation
        )
        item.setPixmap(scaled_pixmap)
        
        item.setPos(d["x"], d["y"])
        return item
    def create_points_on_vertices(self):
        r = AttachPoint.RADIUS
        
        for orientation in Orientation:
            point = AttachPoint( 0,0, r,r, parent=self, orientation=orientation)
            self.vertices[orientation] = point
        self.update_vertices()


    def update_vertices(self):  
        r = AttachPoint.RADIUS
        rect = self.pixmap().rect()
        if rect is None :
            return
        w = rect.width()
        h = rect.height()

        vertices =  {
            Orientation.N : QPointF(0,0),
            Orientation.E : QPointF(w,0),
            Orientation.S : QPointF(w,h),
            Orientation.W : QPointF(0,h)
        }
        for orientation, point in self.vertices.items():
            point.setPos(vertices[orientation])
            for line in point.connected_lines:
                line.aggiorna_posizione()
    def show_points(self):
        for point in self.vertices.values():
            point.show()
        for point in self.attach_points.values():
            point.show()
    def hide_points(self):
        for point in self.vertices.values():
            point.hide()
        for point in self.attach_points.values():
            point.hide()
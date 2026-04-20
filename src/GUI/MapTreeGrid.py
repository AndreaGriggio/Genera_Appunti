import sys
import math
from src.GUI.TextElement import TextItem
from src.GUI.LineElement import LineItem
from PyQt6.QtWidgets import (
    QGraphicsScene, QApplication, QGraphicsRectItem,
    QGraphicsView, QPushButton, QHBoxLayout, QVBoxLayout,
    QLabel, QWidget,QMenuBar,QMessageBox
)
from PyQt6.QtGui import QPen,QColor,QKeySequence,QCursor,QShortcut,QBrush,QTransform,QPainterPath
from PyQt6.QtCore import Qt


SHIFT = 40
RADIUS = 1
N_DOTS = 45

class MapTreeGrid(QGraphicsScene):
    SNAP = 10
    SCENE_COLOR = QColor(50,50,50)
    GRID_COLOR = QColor(200,200,200)
    SELECTION_COLOR = QColor(0, 150, 255, 50)
    GRID_WIDTH = 2
    
    def __init__(self):
        super().__init__()
        self.setSceneRect(-5000, -5000, 10000, 10000)
        self.setBackgroundBrush(QBrush(self.SCENE_COLOR))
        self.rettangolo_visivo = None
        self.linea_in_costruzione = None

    def drawBackground(self, painter, rect):

        super().drawBackground(painter, rect)

        pen = QPen(self.GRID_COLOR)
        pen.setWidth(self.GRID_WIDTH)
        painter.setPen(pen)
        
        left = int(math.floor(rect.left() / SHIFT) * SHIFT)
        right = int(math.ceil(rect.right() / SHIFT) * SHIFT)
        top = int(math.floor(rect.top() / SHIFT) * SHIFT)
        bottom = int(math.ceil(rect.bottom() / SHIFT) * SHIFT)

        # Disegno un puntino su ogni incrocio calcolato
        for x in range(left, right + SHIFT, SHIFT):
            for y in range(top, bottom + SHIFT, SHIFT):
                painter.drawPoint(x, y)

    def mousePressEvent(self, event) -> None:
        if event.modifiers() == Qt.KeyboardModifier.ShiftModifier and event.button() == Qt.MouseButton.LeftButton :

            obj_under_event = self.itemAt(event.scenePos(),QTransform())

            if isinstance(obj_under_event,TextItem):

                self.linea_in_costruzione = LineItem(node_start=obj_under_event,node_end=None )
                self.linea_in_costruzione.node_start.connected_lines.append(self.linea_in_costruzione)
                self.addItem(self.linea_in_costruzione)


            event.accept()
            return 
        
        if event.button() == Qt.MouseButton.RightButton:
            self.punto_inizio_selezione = event.scenePos()
            
            self.rettangolo_visivo = QGraphicsRectItem()
            penna = QPen(self.SELECTION_COLOR, 1, Qt.PenStyle.DashLine)
            pennello = QBrush(self.SELECTION_COLOR) # Azzurro molto trasparente
            self.rettangolo_visivo.setPen(penna)
            self.rettangolo_visivo.setBrush(pennello)
            
            self.addItem(self.rettangolo_visivo)
            event.accept()
            return
        return super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event) -> None:
        if self.linea_in_costruzione:
            self.linea_in_costruzione.update_using_qpoint(self.linea_in_costruzione.node_start.scenePos()+self.linea_in_costruzione.node_start.boundingRect().center(),event.scenePos())
            event.accept()
            return
        if self.rettangolo_visivo:
            punto_attuale = event.scenePos()
            
            x = min(self.punto_inizio_selezione.x(), punto_attuale.x())
            y = min(self.punto_inizio_selezione.y(), punto_attuale.y())
            w = abs(self.punto_inizio_selezione.x() - punto_attuale.x())
            h = abs(self.punto_inizio_selezione.y() - punto_attuale.y())
            
            self.rettangolo_visivo.setRect(x, y, w, h)
            event.accept()
            return
        return super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event) -> None:
        
        obj_under_event = self.itemAt(event.scenePos(),QTransform())
        if self.linea_in_costruzione:

            if isinstance(obj_under_event,TextItem) and obj_under_event != self.linea_in_costruzione.node_start:
                self.linea_in_costruzione.node_end = obj_under_event
                self.linea_in_costruzione.node_end.connected_lines.append(self.linea_in_costruzione)
                self.linea_in_costruzione.aggiorna_posizione()
            else:
                self.linea_in_costruzione.node_start.connected_lines.remove(self.linea_in_costruzione)
                self.removeItem(self.linea_in_costruzione)
            self.linea_in_costruzione = None
            event.accept()
            return
        if event.button() == Qt.MouseButton.RightButton and self.rettangolo_visivo:
            area_rettangolo = self.rettangolo_visivo.rect()
            
            if area_rettangolo.width() > 5 or area_rettangolo.height() > 5:
                percorso_selezione = QPainterPath()
                percorso_selezione.addRect(area_rettangolo)
                
                # Selezioniamo tutti gli item nell'area
                self.setSelectionArea(percorso_selezione)
                
                # Rimuoviamo il rettangolo visivo
                self.removeItem(self.rettangolo_visivo)
                self.rettangolo_visivo = None
                self.punto_inizio_selezione = None
                event.accept()
                return 
            self.removeItem(self.rettangolo_visivo)
            self.rettangolo_visivo = None

        return super().mouseReleaseEvent(event)
    


class Viewer(QWidget):
    ZOOM_FACTOR = 1.2
    BASE_ZOOM = 1.0
    def __init__(self, scene: QGraphicsScene):
        super().__init__()
        #==== Aggiunta della Scena Oggetti ====
        # La scena ci serve da contenitore per gli elementi della mappa
        self.view = QGraphicsView(scene)
        self.scene = scene
        #Impostazione di DRAG
        self.view.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)

        #==== Aggiunta Bottoni ====
        self.btn_zoom_more = QPushButton("+")
        self.btn_zoom_less = QPushButton("-")
        self.label_zoom = QLabel("100%")
        
        self.zoom_factor = self.ZOOM_FACTOR
        
        self.current_zoom = self.BASE_ZOOM

        self.btn_zoom_more.setShortcut(QKeySequence.StandardKey.ZoomIn)
        self.btn_zoom_less.setShortcut(QKeySequence.StandardKey.ZoomOut)

        self.btn_zoom_more.clicked.connect(self.zoom_in)
        self.btn_zoom_less.clicked.connect(self.zoom_out)


        #==== Menu Gestione Modellatore Mappe mentali ====
        barra = QMenuBar()
        
        menu_aggiunte = barra.addMenu("Aggiungi")
        

        action_testo = menu_aggiunte.addAction("Testo")
        menu_linee = menu_aggiunte.addMenu("Linee")


        action_linea = menu_linee.addAction("Spline")
        action_retta = menu_linee.addAction("Retta")
        
        action_testo.setShortcut("Ctrl+t")
        action_linea.setShortcut("Ctrl+l")
        action_retta.setShortcut("Ctrl+r")

        action_testo.triggered.connect(self.add_testo)
        action_linea.triggered.connect(self.add_linea)
        #==== Tooltips Comandi ====
        menu_doc = barra.addMenu("Documentazione")
        action_guida = menu_doc.addAction("Manuale e Comandi")
        action_guida.setShortcut("F1") # Tasto standard per l'aiuto
        action_guida.triggered.connect(self.mostra_documentazione)

        #==== Unione elementi e aggiunta al Widget====
        vbox_bottoni = QHBoxLayout()
        vbox_bottoni.addWidget(self.btn_zoom_more)
        vbox_bottoni.addWidget(self.label_zoom)
        vbox_bottoni.addWidget(self.btn_zoom_less)
        vbox_bottoni.addStretch() 

        main_layout = QVBoxLayout(self)
        
        
        main_layout.addWidget(barra)
        main_layout.addLayout(vbox_bottoni)
        main_layout.addWidget(self.view)
        #==== Creazione Shortcut Globali ====
        self.shortcut_elimina = QShortcut(QKeySequence.StandardKey.Delete, self)
        self.shortcut_elimina.activated.connect(self.elimina_selezionati)

        self.shorcut_elimina_backspace = QShortcut(Qt.Key.Key_Backspace,self)
        self.shorcut_elimina_backspace.activated.connect(self.elimina_selezionati)


        self.shortcut_bordi = QShortcut(QKeySequence("Ctrl+B"), self)
        self.shortcut_bordi.activated.connect(self.cambia_bordi_selezionati)

        self.shortcut_togli_bordi = QShortcut(QKeySequence("Ctrl+F"),self)
        self.shortcut_togli_bordi.activated.connect(self.togli_bordi_selezionati)

    
    #==== Gestione dello zoom ====
    def zoom_in(self):
        
        self.view.scale(self.zoom_factor, self.zoom_factor)
        
        self.current_zoom *= self.zoom_factor
        self.update_zoom_label()

    def zoom_out(self):
        self.view.scale(1.0 / self.zoom_factor, 1.0 / self.zoom_factor)
        
        self.current_zoom /= self.zoom_factor
        self.update_zoom_label()

    def update_zoom_label(self):
        percentuale = int(self.current_zoom * 100)
        self.label_zoom.setText(f"{percentuale}%")

    #==== Gestione Di inserimento elementi ====
    def add_testo(self):
        item = TextItem("Nuovo Blocco di testo",None)

        pos_monitor = QCursor.pos()
    
        pos_view = self.view.mapFromGlobal(pos_monitor)
        
        pos_mappa = self.view.mapToScene(pos_view)

        item.setPos(pos_mappa)

        scene = self.view.scene()
        scene.addItem(item)

    def add_linea(self):
        
        nodo_a = TextItem("Partenza",None)
        nodo_b = TextItem("Arrivo",None)

        
        scene = self.view.scene()
        scene.addItem(nodo_a)
        scene.addItem(nodo_b)
        cursor_pos = QCursor.pos()
        nodo_a.setPos(cursor_pos.x(),cursor_pos.y())
        nodo_b.setPos(400, 200)
        # Crei la linea passandole i nodi
        mia_linea = LineItem(nodo_a, nodo_b)

        # Aggiungi la linea alla scena
        scene.addItem(mia_linea)

        # Salvi la linea dentro ai nodi per farli comunicare
        nodo_a.connected_lines.append(mia_linea)
        nodo_b.connected_lines.append(mia_linea)
        print("Aggiungo Linea")
        scene.update()

    #==== Gestione Shortcuts ====
    def elimina_selezionati(self):
        for item in self.scene.selectedItems():
            if not item.hasFocus():
                
                if isinstance(item, TextItem):
                    for linea in list(item.connected_lines):
                        
                        if linea.node_start == item:
                            linea.node_start = None
                            
                            linea.orfano_start = item.scenePos() + item.boundingRect().center()
                        
                        
                        elif linea.node_end == item:
                            linea.node_end = None
                            linea.orfano_end = item.scenePos() + item.boundingRect().center()
                            
                        linea.aggiorna_posizione()
                        
                    item.connected_lines.clear()

                self.scene.removeItem(item)

    def cambia_bordi_selezionati(self):
        for item in self.scene.selectedItems():
            if hasattr(item, 'toggle_forma'):
                item.toggle_forma()

    def togli_bordi_selezionati(self):
        for item in self.scene.selectedItems():
            if hasattr(item,'toggle_bordo'):
                item.toggle_bordo()

    #==== Documentazione dei comandi ====
    def mostra_documentazione(self):
        # Usiamo l'HTML base per fare una formattazione pulita e leggibile
        testo_guida = """
        <h3>Guida all'Editor di Mappe Mentali</h3>
        
        <b>📝 Nodi e Testo</b>
        <ul>
            <li><b>Ctrl+T</b>: Aggiungi un nuovo blocco di testo al centro della visuale.</li>
            <li><b>Doppio Clic</b>: Entra in modalità modifica per cambiare il testo di un blocco.</li>
            <li><b>Clic + Trascina</b>: Sposta liberamente un blocco sulla griglia (con Snap automatico).</li>
        </ul>
        
        <b>🔗 Linee e Collegamenti</b>
        <ul>
            <li><b>Ctrl+L</b>: Strumento Linea Curva (Spline).</li>
            <li><b>Ctrl+R</b>: Strumento Linea Retta.</li>
            <li><b>Shift + Clic e Trascina</b>: <i>(In arrivo)</i> Crea dinamicamente un collegamento tra due nodi.</li>
        </ul>
        
        <b>🎨 Stile e Rimozione</b>
        <ul>
            <li><b>Ctrl+B</b>: Cambia la forma del blocco selezionato (Rettangolo / Ellisse).</li>
            <li><b>Ctrl+F</b>: Nascondi o mostra i bordi del blocco selezionato.</li>
            <li><b>Canc / Backspace</b>: Elimina i nodi o le linee attualmente selezionate.</li>
        </ul>
        
        <b>🔍 Navigazione</b>
        <ul>
            <li><b>Rotellina Mouse</b>: Usa le barre di scorrimento (o premi la rotellina per trascinare la mappa).</li>
            <li><b>Tasti + / -</b>: Effettua Zoom In e Zoom Out.</li>
        </ul>
        """
        
        QMessageBox.information(self, "Manuale dei Comandi", testo_guida)
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Istanziamo la scena
    map_scene = MapTreeGrid()
    item = TextItem("Ciao sono del testo di prova",None)
    map_scene.addItem(item)
    
    # Istanziamo il nostro Widget Contenitore
    viewer = Viewer(map_scene)
    viewer.resize(800, 600)
    viewer.setWindowTitle("Editor Mappe")
    viewer.show()
    
    sys.exit(app.exec())
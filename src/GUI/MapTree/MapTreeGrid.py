import sys
import math
from src.GUI.MapTree.TextElement import TextItem,AttachPoint,Orientation,BaseItem
from src.GUI.MapTree.LineElement import LineItem
from src.GUI.MapTree.Node import Node
from src.GUI.MapTree.ImageElement import ImageItem

from pathlib import Path
import json

from PyQt6.QtWidgets import (
    QGraphicsScene, QApplication, QGraphicsRectItem, QGraphicsSceneDragDropEvent,
    QGraphicsView, QPushButton, QHBoxLayout, QVBoxLayout,
    QLabel, QWidget,QMenuBar,QMessageBox,QFileDialog
)
from PyQt6.QtGui import (
    QPen,QColor,QKeySequence,QCursor,
    QShortcut,QBrush,QTransform,
    QPainterPath,QPageLayout,QPageSize,
    QPainter,QPdfWriter,QPixmap
)
from PyQt6.QtCore import QPointF, Qt,pyqtSignal,QRectF


SHIFT = 40
RADIUS = 1
N_DOTS = 45

class MapTreeGrid(QGraphicsScene):
    SNAP = 10
    SCENE_COLOR = QColor(50,50,50)
    GRID_COLOR = QColor(200,200,200)
    SELECTION_COLOR = QColor(0, 150, 255, 50)
    GRID_WIDTH = 2
    images_dropped = pyqtSignal(list, QPointF)

    def __init__(self):
        super().__init__()
        self.setSceneRect(-5000, -5000, 10000, 10000)
        self.setBackgroundBrush(QBrush(self.SCENE_COLOR))
        self.rettangolo_visivo = None
        self.linea_in_costruzione = None
        self.immagine_in_costruzione = False
        self.tipo_linea = "spline"
        self.nascondi_sfondo_pdf = False
        self.image_id = 0
    
    def dragEnterEvent(self, event: QGraphicsSceneDragDropEvent | None) -> None:
        if event is None :
            return super().dragEnterEvent(event)
        if event.mimeData().hasUrls() or event.mimeData().hasImage():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event: QGraphicsSceneDragDropEvent| None)  -> None:
        if event is None :
            return super().dragMoveEvent(event)
        if event.mimeData().hasUrls() or event.mimeData().hasImage():
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)
    def dropEvent(self,event: QGraphicsSceneDragDropEvent| None) -> None:
        if event is None :
            return super().dropEvent(event)
        
        mime = event.mimeData()
        posizione_rilascio = event.scenePos() 

        pixmap_da_inserire:list[QPixmap] = []

        
        if mime.hasUrls():
            for url in mime.urls():
                if url.isLocalFile():
                    percorso = url.toLocalFile()
                    if percorso.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp')):
                        pixmap_da_inserire.append(QPixmap(percorso))
                        continue

        
        elif mime.hasImage():
            image_data = mime.imageData()
            pixmap_da_inserire.append(QPixmap.fromImage(image_data))

        
        if pixmap_da_inserire :

            self.images_dropped.emit(pixmap_da_inserire,posizione_rilascio)

            event.acceptProposedAction()
        else:
            super().dropEvent(event)
        
    def drawBackground(self, painter, rect):

        if getattr(self, 'nascondi_sfondo_pdf', False):
            # Se stiamo esportando, mettiamo uno sfondo bianco pulito
            painter.fillRect(rect, Qt.GlobalColor.white)
            return
        # ------------------

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

            if isinstance(obj_under_event,BaseItem):
                nearest_point = obj_under_event.get_nearest_point(event.scenePos())
                if nearest_point is not None:
                    self.linea_in_costruzione = LineItem(node_start=nearest_point,node_end=None ,tipo = self.tipo_linea)
                    self.linea_in_costruzione.node_start.attach_line(self.linea_in_costruzione)
                    self.addItem(self.linea_in_costruzione)
            event.accept()
            return 
    
        if event.button() == Qt.MouseButton.RightButton :
            if isinstance(self.itemAt(event.scenePos(),QTransform()),BaseItem):
                return super().mousePressEvent(event)
            self.punto_inizio_selezione = event.scenePos()
            
            self.rettangolo_visivo = QGraphicsRectItem()
            penna = QPen(self.SELECTION_COLOR, 1, Qt.PenStyle.DashLine)
            pennello = QBrush(self.SELECTION_COLOR) # Azzurro molto trasparente
            self.rettangolo_visivo.setPen(penna)
            self.rettangolo_visivo.setBrush(pennello)
            
            self.addItem(self.rettangolo_visivo)
            event.accept()
            return
        #L'idea che ci sta dietro è che dobbiamo modificare la linea permettendoci flessibilità durante la modifica
        if event.button() == Qt.MouseButton.LeftButton:
            obj = self.itemAt(event.scenePos(), QTransform())

            if isinstance(obj, LineItem):
                line = obj
                near_start = line.is_click_near_node(line.node_start, event.scenePos())
                near_end   = line.is_click_near_node(line.node_end,   event.scenePos())

                if near_start:
                    self.linea_in_costruzione = line
                    line.node_start.detach_line(line)
                    line.node_start = None
                    event.accept()
                    return
                elif near_end:
                    self.linea_in_costruzione = line
                    line.node_end.detach_line(line)
                    line.node_end = None
                    event.accept()
                    return

        return super().mousePressEvent(event)



    def mouseMoveEvent(self, event) -> None:
        if self.linea_in_costruzione:
            line = self.linea_in_costruzione

            if line.node_start is not None and line.node_end is None:
                line.update_using_qpoint(line.node_start.scenePos(), event.scenePos())
            elif line.node_end is not None and line.node_start is None:
                line.update_using_qpoint(event.scenePos(), line.node_end.scenePos())

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
        if self.linea_in_costruzione:
            line = self.linea_in_costruzione
            obj  = self.itemAt(event.scenePos(), QTransform())

            # Risolvi il target: potrebbe essere AttachPoint o TextItem
            target = obj.parentItem() if isinstance(obj, AttachPoint) else obj

            if line.node_end is None:
                # Stavo spostando/creando il capo end
                if isinstance(target, BaseItem) and target is not line.node_start.parentItem():
                    punto = target.get_nearest_point(event.scenePos())
                    line.node_end = punto
                    punto.attach_line(line)
                    line.aggiorna_posizione()
                else:
                    line.node_start.detach_line(line)
                    self.removeItem(line)

            elif line.node_start is None:
                # Stavo spostando il capo start
                if isinstance(target, BaseItem) and target is not line.node_end.parentItem():
                    punto = target.get_nearest_point(event.scenePos())
                    line.node_start = punto
                    punto.attach_line(line)
                    line.aggiorna_posizione()
                else:
                    line.node_end.detach_line(line)
                    self.removeItem(line)

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
    """ Visualizza le mappe mentali, ne gestisce il salvataggio con classi helper """
    new_tab_ready = pyqtSignal(QWidget,str)
    ZOOM_FACTOR = 1.2
    BASE_ZOOM = 1.0
    def __init__(self, scene: MapTreeGrid,titolo:str|None ="",saving_path:Path| None = None ):
        self.usable_id = 0
        super().__init__()
        self.saving_path = saving_path
        self.title = titolo if titolo else "Nuova Mappa"
        self.setWindowTitle(f"Edito Mappe - {self.title}")
        #==== Aggiunta della Scena Oggetti ====
        # La scena ci serve da contenitore per gli elementi della mappa
        self.view = QGraphicsView(scene)
        self.scene = scene
        self.scene.images_dropped.connect(self.add_images)
        self.saver = MapSaver(self)
        self.loader = MapLoader(self)

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
        

        action_testo   = menu_aggiunte.addAction("Testo")
        menu_linee     = menu_aggiunte.addMenu("Linee")
        menu_utility   = barra.addMenu("Utilita")
        menu_salva     = barra.addMenu("Esporta")

        action_load    = barra.addAction("Carica")
        action_salva   = menu_salva.addAction("Salva in .Mappa")
        action_pdf     = menu_salva.addAction("Salva come pdf")
        action_copia   = menu_utility.addAction("Copia")
        action_incolla = menu_utility.addAction("Incolla")

        action_mostra_nodi = menu_utility.addAction("Mostra Tutti i Nodi")
        action_mostra_nodi.triggered.connect(self.mostra_tutti_i_nodi)

        action_linea = menu_linee.addAction("Spline")
        action_retta = menu_linee.addAction("Retta")
        
        action_testo.setShortcut("Ctrl+t")
        action_linea.setShortcut("Ctrl+l")
        action_retta.setShortcut("Ctrl+r")
        action_salva.setShortcut("Ctrl+s")
        action_copia.setShortcut("Ctrl+c")
        action_incolla.setShortcut("Ctrl+v")


        action_testo.triggered.connect(lambda x : self.add_testo(None))
        action_linea.triggered.connect(self.spline_type)
        action_retta.triggered.connect(self.rect_type)
        action_salva.triggered.connect(self.salva)
        action_pdf.triggered.connect(self.pdf)
        action_load.triggered.connect(self.carica)
        action_copia.triggered.connect(self.copia_selezionati)
        action_incolla.triggered.connect(self.incolla)

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

        self.shortcut_togli_bordi = QShortcut(QKeySequence("Shift+b"),self)
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
    # ==== Gestione Appunti (Copia/Incolla) ====
    def copia_selezionati(self):
        items = self.scene.selectedItems()
        if not items:
            return
        
        # Sfrutta il serializzatore
        dati_serializzati = self.serialize_items(items)
        dati_serializzati["_clipboard"] = True # Flag di sicurezza
        
        payload = json.dumps(dati_serializzati)
        QApplication.clipboard().setText(payload)

        
    def incolla(self):
        clipboard = QApplication.clipboard()
        mime_data = clipboard.mimeData()

        # Calcoliamo la posizione del mouse per centrare il drop
        pos_monitor = QCursor.pos()
        pos_view = self.view.mapFromGlobal(pos_monitor)
        pos_mappa = self.view.mapToScene(pos_view)

        # 1. PRIORITÀ MASSIMA: Payload interno dell'app (Nodi, Linee, Immagini interne)
        # Verifichiamo se è il nostro JSON testuale prima di tutto il resto.
        if mime_data.hasText():
            testo = mime_data.text()
            try:
                data = json.loads(testo)
                if isinstance(data, dict) and "_clipboard" in data:
                    self.deserialize_items(data, pos_offset=pos_mappa, remap_ids=True)
                    return  # Se abbiamo incollato il nostro formato, fermati qui.
            except json.JSONDecodeError:
                pass  # Non è JSON, potrebbe essere testo semplice. Procediamo.

        # 2. Immagine Nativa (Es. Screenshot, o 'Copia Immagine' dal browser)
        if mime_data.hasImage():
            image_data = mime_data.imageData()
            pixmap = QPixmap.fromImage(image_data)
            if not pixmap.isNull():
                self.add_images([pixmap], pos_mappa)
            return

        # 3. File copiati dal Sistema Operativo (Es. File .jpg copiato dal Desktop)
        if mime_data.hasUrls():
            pixmaps = []
            for url in mime_data.urls():
                if url.isLocalFile():
                    percorso = url.toLocalFile()
                    # Filtro di sicurezza sulle estensioni
                    if percorso.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp')):
                        pixmaps.append(QPixmap(percorso))
            if pixmaps:
                self.add_images(pixmaps, pos_mappa)
                return

        # 4. Testo Semplice (Es. copiato da Wikipedia o Blocco Note)
        if mime_data.hasText():
            testo = mime_data.text().strip()
            if testo:  # Evitiamo di incollare blocchi di testo vuoti
                self.add_testo(testo, posizione=pos_mappa)
    
    #==== Gestione Di inserimento elementi ====
    def add_testo(self,testo:str |None = None, posizione: QPointF | None = None):
        if testo is None:
            testo = "Nuovo Blocco di testo"
            
        item = TextItem(testo, None, id=self.usable_id)
        self.usable_id += 1

        # Se non passiamo una posizione (es. uso via shortcut Ctrl+T), la calcola
        if posizione is None:
            pos_monitor = QCursor.pos()
            pos_view = self.view.mapFromGlobal(pos_monitor)
            posizione = self.view.mapToScene(pos_view)

        item.setPos(posizione)
        self.scene.addItem(item)
    
    def add_images(self, images: list[QPixmap], posizione: QPointF):
        offset = 0
        for image in images:
            nuova_immagine = ImageItem(image, id=self.usable_id)
            nuova_immagine.setPos(posizione.x(),posizione.y()+offset)
            self.scene.addItem(nuova_immagine)
            self.usable_id += 1
            offset = image.height()+10
    #==== Gestione Shortcuts ====
    def elimina_selezionati(self):
        elementi_selezionati = self.scene.selectedItems()
        if not elementi_selezionati:
            return

        
        for item in elementi_selezionati:
            if isinstance(item, LineItem):
                item.rimuovi_sicuro()

        
        for item in elementi_selezionati:
            if isinstance(item, BaseItem):
                item.distruggi_linee_connesse()
                if item.scene():
                    self.scene.removeItem(item)
                    
            elif isinstance(item, ImageItem): # Se ImageItem non usa BaseItem
                if item.scene():
                    self.scene.removeItem(item)
    def spline_type(self):
        self.scene.tipo_linea = "spline"
    def rect_type(self):
        self.scene.tipo_linea = "retta"
    def cambia_bordi_selezionati(self):
        for item in self.scene.selectedItems():
            if isinstance(item, TextItem):
                item.toggle_forma()

    def togli_bordi_selezionati(self):
        for item in self.scene.selectedItems():
            if isinstance(item, TextItem):
                item.toggle_bordo()
    #==== Utilities ====
    def mostra_tutti_i_nodi(self):
        for item in self.scene.items():
            item.setVisible(True)

    def getGraph(self)-> list[Node] | None:

        text_items = [
            item for item in self.scene.items()
            if isinstance(item, TextItem)
            ]
        if text_items == [] :
            return None
        
        graph : list[Node] = []
        for child in text_items :
            graph.append(child.getNode())
        
        return graph
    # ==== SERIALIZZAZIONE CENTRALIZZATA ====

    def serialize_items(self, items: list) -> dict:
        """Trasforma una lista di oggetti grafici in un dizionario puro."""
        dati = {"nodi": [], "immagini": []}
        # Teniamo traccia di cosa stiamo serializzando per non salvare linee a metà
        id_validi = {item.id for item in items if hasattr(item, 'id')}

        for item in items:
            if isinstance(item, TextItem): # Presumo TextItem erediti da BaseItem/Connectable
                node_dict = item.getNode().nodeToDict()
                if node_dict:
                    # Conserva solo le linee che puntano ad altri elementi nella lista
                    node_dict["n"] = [c for c in node_dict["n"] if c["target"] in id_validi]
                    dati["nodi"].append(node_dict)
            elif isinstance(item, ImageItem):
                dati["immagini"].append(item.to_dict())

        return dati

    def deserialize_items(self, data: dict, pos_offset: QPointF = None, remap_ids: bool = False):
        """
        Ricostruisce gli elementi sulla scena a partire da un dizionario.
        - pos_offset: se fornito, sposta gli elementi rispetto al loro centro originale (usato per l'incolla).
        - remap_ids: se True, genera nuovi ID ignorando quelli salvati (usato per l'incolla).
        """
        id_map: dict[int, int] = {}
        nodi_creati: dict[int, TextItem] = {}
        max_id = self.usable_id - 1

        # Calcola il riquadro degli elementi originali per incollare centrato al mouse
        min_x, min_y = float('inf'), float('inf')
        if pos_offset:
            for n in data.get("nodi", []):
                min_x = min(min_x, n["element"].get("x", float('inf')))
                min_y = min(min_y, n["element"].get("y", float('inf')))
            for i in data.get("immagini", []):
                min_x = min(min_x, i.get("x", float('inf')))
                min_y = min(min_y, i.get("y", float('inf')))
            if min_x == float('inf'): min_x, min_y = 0, 0

        # --- 1. Istanziazione Nodi e Immagini ---
        for nodo_data in data.get("nodi", []):
            elem = nodo_data.get("element")
            if not elem: continue

            vecchio_id = elem.get("id", 0)
            nuovo_id = self.usable_id if remap_ids else vecchio_id
            if remap_ids: self.usable_id += 1
            max_id = max(max_id, nuovo_id)
            id_map[vecchio_id] = nuovo_id

            nuovo_nodo = TextItem(elem.get("text", ""), QColor(elem.get("border")), 
                                  elem.get("margin"), QColor(elem.get("fill")), nuovo_id)
            
            x, y = elem.get("x", 0.0), elem.get("y", 0.0)
            if pos_offset:
                x = pos_offset.x() + (x - min_x)
                y = pos_offset.y() + (y - min_y)
            nuovo_nodo.setPos(x, y)
            
            self.scene.addItem(nuovo_nodo)
            nodi_creati[nuovo_id] = nuovo_nodo

        for img_data in data.get("immagini", []):
            vecchio_id = img_data.get("id", 0)
            nuovo_id = self.usable_id if remap_ids else vecchio_id
            if remap_ids: self.usable_id += 1
            max_id = max(max_id, nuovo_id)
            id_map[vecchio_id] = nuovo_id

            img_data_copy = img_data.copy()
            img_data_copy["id"] = nuovo_id
            
            x, y = img_data.get("x", 0.0), img_data.get("y", 0.0)
            if pos_offset:
                img_data_copy["x"] = pos_offset.x() + (x - min_x)
                img_data_copy["y"] = pos_offset.y() + (y - min_y)

            img_item = ImageItem.from_dict(img_data_copy)
            self.scene.addItem(img_item)

        # --- 2. Ricostruzione Linee ---
        for nodo_data in data.get("nodi", []):
            elem = nodo_data.get("element")
            vicini = nodo_data.get("n", [])
            if not elem or not vicini: continue

            nodo_start = nodi_creati.get(id_map.get(elem.get("id", 0), 0))
            if not nodo_start: continue

            for vicino in vicini:
                target_id = id_map.get(vicino.get("target"), 0)
                nodo_end = nodi_creati.get(target_id)
                if not nodo_end: continue

                orient_start = Orientation(vicino["attachment"].get("orientation_start", "E"))
                orient_end = Orientation(vicino["attachment"].get("orientation_end", "W"))

                punto_start = nodo_start.attach_points.get(orient_start)
                punto_end = nodo_end.attach_points.get(orient_end)

                if punto_start and punto_end:
                    linea = LineItem(node_start=punto_start,
                                     node_end=punto_end,
                                     tipo=vicino.get("tipo"),
                                     arrow_start=vicino.get("arrow_start", False),
                                     arrow_end=vicino.get("arrow_end", False))
                    punto_start.attach_line(linea)
                    punto_end.attach_line(linea)
                    self.scene.addItem(linea)
                    linea.aggiorna_posizione()

        # Aggiorna ID utilizzabile per i salvataggi (quando non rimappi)
        if not remap_ids:
            self.usable_id = max_id + 1
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
    #==== Salvataggio della mappa ====
    def salva(self):
        self.saver.salva_mappa(self.title,self.saving_path)
    def carica(self):
        self.loader.carica_mappa(self.saving_path)
    def pdf(self):
        self.saver.esporta_pdf(self.title,self.saving_path)

class MapSaver():
    def __init__(self,mapTree :Viewer):
        self.map = mapTree
    def esporta_pdf(self, titolo:str |None="Mappa_Concettuale",saving_path :Path | None = None):
        """
        Esporta il contenuto della scena in un file PDF, ignorando UI e griglia.
        """
        if not titolo:
            titolo = "Nuova_Mappa"
            

        if saving_path is not None:

            percorso = str(saving_path.with_suffix('.pdf'))
        else:
            percorso = f"{titolo}.pdf"

        path, _ = QFileDialog.getSaveFileName(
            None, 
            "Salva Mappa come PDF",
            percorso, 
            "Tutti i file (*)"
        )
        
        if not path:
            return

        # Configura il PDF Writer
        writer = QPdfWriter(path)
        writer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
        writer.setPageOrientation(QPageLayout.Orientation.Landscape)
        writer.setCreator("Generatore Appunti")
        writer.setTitle(titolo)

        painter = QPainter(writer)
        
        # 1. Troviamo il riquadro esatto che contiene i nodi (ignorando i -5000 vuoti)
        area_nodi = self.map.scene.itemsBoundingRect()
        
        # Se la mappa è vuota, crea un PDF bianco e fermati
        if area_nodi.isNull():
            painter.end()
            return
            
        # Aggiungiamo un po' di margine (es. 20 pixel) attorno ai nodi per non attaccarli ai bordi del PDF
        area_nodi.adjust(-20, -20, 20, 20)

        # 2. Spegniamo la griglia scura
        self.map.scene.nascondi_sfondo_pdf = True

        for item in self.map.scene.items():
            if isinstance(item, TextItem):
                if hasattr(item, 'prepara_per_pdf'):
                    item.prepara_per_pdf(True)

        # 3. Definiamo l'area del foglio A4 dove andremo a disegnare
        area_foglio = QRectF(painter.viewport())

        # 4. SCATTIAMO LA FOTO ALLA SCENA (NON AL WIDGET)
        # Passando aspectRatioMode, Qt scala la mappa in automatico per farla stare perfettamente nell'A4
        self.map.scene.render(
            painter, 
            target=area_foglio, 
            source=area_nodi, 
            mode=Qt.AspectRatioMode.KeepAspectRatio
        )
        
        painter.end()
        
        # 5. Riaccendiamo la griglia scura per l'utente
        self.map.scene.nascondi_sfondo_pdf = False
        for item in self.map.scene.items():
            if isinstance(item, TextItem):
                item.prepara_per_pdf(False)
        self.map.view.viewport().update() # Forza l'aggiornamento visivo a schermo

        QMessageBox.information(None, "Successo", f"Mappa salvata correttamente in:\n{path}")

    def salva_mappa(self,titolo : str|None = "Mappa Mentale",saving_path : Path | None = None):
        if titolo is None:
            titolo = "Mappa Mentale"
            

        if saving_path is not None:
            percorso = str(saving_path)
        else:
            percorso = f"{titolo}.mappa"

        nome_file, _ = QFileDialog.getSaveFileName(
            self.map, 
            "Salva Mappa Mentale",  
            percorso,
            "Tutti i file (*)"
        )
        
        contents =self.process_file(nome_file)
        
        self.dump_contents(contents,nome_file)
                
    def process_file(self, nome_file)-> dict| None:
        if not nome_file:
            return 
        
        # Salva TUTTO usando la logica centralizzata
        items_scena = self.map.scene.items()
        dati_mappa = self.map.serialize_items(items_scena)
        
        if not dati_mappa["nodi"] and not dati_mappa["immagini"]:
            QMessageBox.warning(self.map, "Attenzione", "La mappa è vuota.")
            return None

        return dati_mappa

        
        
    def dump_contents(self,contents:dict | None,nome_file:str):
        try:
            with open(nome_file, 'w', encoding='utf-8') as file:
                json.dump(contents, file, indent=4)
            print(f"Mappa salvata con successo in: {nome_file}")
            nuovo_path = Path(nome_file)
            self.map.saving_path = nuovo_path
            self.map.title = nuovo_path.stem  
            self.map.setWindowTitle(self.map.title)
            QMessageBox.information(self.map, "Successo", "Mappa salvata correttamente!")
        except Exception as e:
            print(f"Errore durante il salvataggio: {e}")
            QMessageBox.critical(self.map, "Errore", f"Impossibile salvare il file:\n{e}")
class MapLoader():

    def __init__(self,mapTree: Viewer):
        self.map = mapTree

    def carica_mappa(self,path : Path| None = None):
        percorso = str(path.parent) if path and path.exists() else ""
            
        nome_file, _ = QFileDialog.getOpenFileName(
            self.map,
            "Carica Mappa Mentale",
            percorso,
            "Mappa  (*.mappa);;Tutti i file (*)"
        )
        
        if not nome_file:
            return
        
        if self.process_file(nome_file):
            
            nuovo_path = Path(nome_file)
            self.map.saving_path = nuovo_path
            self.map.title = nuovo_path.stem
            self.map.setWindowTitle(self.map.title)

    def process_file(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                dati_mappa = json.load(file)
        except Exception as e:
            QMessageBox.critical(self.map, "Errore", f"Impossibile leggere il file:\n{e}")
            return

        self.map.scene.clear()
        
        # Deserializza: NO offset (finisce a coordinate originali), NO remap (mantiene vecchi ID)
        self.map.deserialize_items(dati_mappa, pos_offset=None, remap_ids=False)
        
        QMessageBox.information(self.map, "Successo", "Mappa caricata correttamente!")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Istanziamo la scena
    map_scene = MapTreeGrid()
    item = TextItem("Ciao sono del testo di prova",None)
    map_scene.addItem(item)
    
    # Istanziamo il nostro Widget Contenitore
    viewer = Viewer(scene=map_scene,titolo=None,)
    viewer.resize(800, 600)
    viewer.setWindowTitle("Editor Mappe")
    viewer.show()
    
    sys.exit(app.exec())
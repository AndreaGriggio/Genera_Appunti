import sys
import math
from src.GUI.MapTree.TextElement import TextItem
from src.GUI.MapTree.LineElement import LineItem
from src.GUI.MapTree.Node import Node
from src.GUI.MapTree.Element import Element
from pathlib import Path
import json

from PyQt6.QtWidgets import (
    QGraphicsScene, QApplication, QGraphicsRectItem,
    QGraphicsView, QPushButton, QHBoxLayout, QVBoxLayout,
    QLabel, QWidget,QMenuBar,QMessageBox,QGraphicsItem,
    QFileDialog
)
from PyQt6.QtGui import (
    QPen,QColor,QKeySequence,QCursor,
    QShortcut,QBrush,QTransform,
    QPainterPath,QPageLayout,QPageSize,
    QPainter,QPdfWriter,QPainterPathStroker
)
from PyQt6.QtCore import Qt,pyqtSignal,QRectF


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
        self.tipo_linea = "spline"
        self.nascondi_sfondo_pdf = False

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

            if isinstance(obj_under_event,TextItem):

                self.linea_in_costruzione = LineItem(node_start=obj_under_event,node_end=None ,tipo = self.tipo_linea)
                self.linea_in_costruzione.node_start.connected_lines.append(self.linea_in_costruzione)
                self.addItem(self.linea_in_costruzione)


            event.accept()
            return 
    
        if event.button() == Qt.MouseButton.RightButton :
            if isinstance(self.itemAt(event.scenePos(),QTransform()),TextItem):
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

                if near_start or near_end:
                    self.linea_in_costruzione = line

                    if near_start:

                        self._moving_end = "start"
                        line.node_start.connected_lines.remove(line)
                        line.node_start = None
                    else:

                        self._moving_end = "end"
                        line.node_end.connected_lines.remove(line)
                        line.node_end = None
                    event.accept()
                    return
    
        return super().mousePressEvent(event)


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
    def mouseMoveEvent(self, event) -> None:
        if self.linea_in_costruzione:
            line = self.linea_in_costruzione

            if line.node_start is None and line.node_end is not None:
  
                anchor = line.node_end.scenePos() + line.node_end.boundingRect().center()
                line.update_using_qpoint(event.scenePos(), anchor)
    
            elif line.node_end is None and line.node_start is not None:

                anchor = line.node_start.scenePos() + line.node_start.boundingRect().center()
                line.update_using_qpoint(anchor, event.scenePos())
    
            elif line.node_start is None and line.node_end is None:
                # Entrambi staccati (non dovrebbe accadere, ma gestiamo il caso)
                pass
    
            else:
                # Nuova linea in creazione: node_start è fisso, end segue il mouse
                anchor = line.node_start.scenePos() + line.node_start.boundingRect().center()
                line.update_using_qpoint(anchor, event.scenePos())
    
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
            if self.linea_in_costruzione:
                line = self.linea_in_costruzione

                if line.node_start is None:
                    if isinstance(obj_under_event, TextItem) and obj_under_event != line.node_end:
                        line.node_start = obj_under_event
                        obj_under_event.connected_lines.append(line)
                        line.aggiorna_posizione()
                    else:
                        if line.node_end is not None:
                            line.node_end.connected_lines.remove(line)
                        self.removeItem(line)
  
                elif line.node_end is None:
                    if isinstance(obj_under_event, TextItem) and obj_under_event != line.node_start:
                        line.node_end = obj_under_event
                        obj_under_event.connected_lines.append(line)
                        line.aggiorna_posizione()
                    else:
  
                        if line.node_start is not None:
                            line.node_start.connected_lines.remove(line)
                        self.removeItem(line)
        
                self.linea_in_costruzione = None
                self._moving_end = None
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
        

        action_testo = menu_aggiunte.addAction("Testo")
        menu_linee = menu_aggiunte.addMenu("Linee")
        menu_utility = barra.addMenu("Utilita")
        menu_salva = barra.addMenu("Esporta")

        action_load = barra.addAction("Carica")
        action_salva = menu_salva.addAction("Salva in .Mappa")
        action_pdf = menu_salva.addAction("Salva come pdf")

        action_mostra_nodi = menu_utility.addAction("Mostra Tutti i Nodi")
        action_mostra_nodi.triggered.connect(self.mostra_tutti_i_nodi)

        action_linea = menu_linee.addAction("Spline")
        action_retta = menu_linee.addAction("Retta")
        
        action_testo.setShortcut("Ctrl+t")
        action_linea.setShortcut("Ctrl+l")
        action_retta.setShortcut("Ctrl+r")
        action_salva.setShortcut("Ctrl+s")



        action_testo.triggered.connect(self.add_testo)
        action_linea.triggered.connect(self.spline_type)
        action_retta.triggered.connect(self.rect_type)
        action_salva.triggered.connect(self.salva)
        action_pdf.triggered.connect(self.pdf)
        action_load.triggered.connect(self.carica)

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
        item = TextItem("Nuovo Blocco di testo",None,id=self.usable_id)
        self.usable_id = self.usable_id + 1

        pos_monitor = QCursor.pos()
    
        pos_view = self.view.mapFromGlobal(pos_monitor)
        
        pos_mappa = self.view.mapToScene(pos_view)

        item.setPos(pos_mappa)

        scene = self.view.scene()
        scene.addItem(item)


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
    def spline_type(self):
        self.scene.tipo_linea = "spline"
    def rect_type(self):
        self.scene.tipo_linea = "retta"
    def cambia_bordi_selezionati(self):
        for item in self.scene.selectedItems():
            if hasattr(item, 'toggle_forma'):
                item.toggle_forma()

    def togli_bordi_selezionati(self):
        for item in self.scene.selectedItems():
            if hasattr(item,'toggle_bordo'):
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
                if hasattr(item, 'prepara_per_pdf'):
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
        
                
        if not nome_file:
            return 

        dati_grafo = self.map.getGraph()
        
        if dati_grafo is None:
            QMessageBox.warning(self.map, "Attenzione", "La mappa è vuota, nulla da salvare.")
            return

        dati_mappa = {
            "nodi": []
        }

        for nodo in dati_grafo:
            nodo_dict = nodo.nodeToDict()
            if nodo_dict is not None:
                dati_mappa["nodi"].append(nodo_dict)
        
        try:
            with open(nome_file, 'w', encoding='utf-8') as file:
                json.dump(dati_mappa, file, indent=4)
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

        if "nodi" not in dati_mappa:
            QMessageBox.warning(self.map, "Formato Non Valido", "Il file non contiene una mappa compatibile.")
            return

        self.map.scene.clear()
        
        nodi_creati = {}  
        max_id = -1      

        for nodo_data in dati_mappa["nodi"]:
            elem = nodo_data.get("element")
            if not elem:
                continue

            node_id = elem.get("id", 0)
            max_id = max(max_id, node_id)
            testo = elem.get("text", "")
  
            border_color = QColor(elem.get("border", "#000000"))
            fill_color = QColor(elem.get("fill", "#323232"))
            margin = elem.get("margin", 10)

            nuovo_nodo = TextItem(testo, border_color, margin, fill_color, node_id)
            nuovo_nodo.setPos(elem.get("x", 0.0), elem.get("y", 0.0))
            
            self.map.scene.addItem(nuovo_nodo)
            nodi_creati[node_id] = nuovo_nodo
        
        for nodo_data in dati_mappa["nodi"]:
            elem = nodo_data.get("element")
            vicini = nodo_data.get("n", [])
            
            if not elem or not vicini:
                continue

            start_id = elem.get("id")
            nodo_start = nodi_creati.get(start_id)

            if not nodo_start:
                continue

            for vicino in vicini:
                # 'vicino' è una lista tipo: [target_id, "tipo_linea"]
            
                target_id = vicino.get("target")
                tipo_linea = vicino.get("tipo")

                nodo_end = nodi_creati.get(target_id)
                
                if nodo_end:
                    
                    linea = LineItem(node_start=nodo_start, node_end=nodo_end, tipo=tipo_linea)
                    
                    
                    nodo_start.connected_lines.append(linea)
                    nodo_end.connected_lines.append(linea)
                    
                    
                    self.map.scene.addItem(linea)
                    linea.aggiorna_posizione()

        self.map.usable_id = max_id + 1

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
import sys
from src.GUI.Filemanager import FileManagerWindow
from src.GUI.SettingsDialog import open_settings
from src.GUI.DeatachableTabBar import DetachableTabWidget
from PyQt6.QtWidgets import QWidget,QPushButton,QMainWindow,QApplication,QStyle,QTabBar


from PyQt6.QtGui import QAction

WIDTH = 1200
HEIGHT = 600

class Hub(QMainWindow):

    def __init__(self):
        super().__init__()
        icona_x = self.style().standardIcon(QStyle.StandardPixmap.SP_DialogCloseButton)
        self.setWindowTitle("Main Hub")
        self.resize(WIDTH,HEIGHT)

        #====Sezione di Creazione MenuBar====
        menuBar = self.menuBar()
        menuFinestre = menuBar.addMenu("Strumenti")

        #Definizione azioni
        action_Filemanager = QAction("Nuovo Filemanager",self)
        action_impostazioni = QAction("Impostazioni",self)
        
        #Shortcuts
        action_Filemanager.setShortcut("Ctrl+F")

        #Cliccando sopra alle azioni collegamento con funzioni
        action_Filemanager.triggered.connect(self.apri_FileManager)
        action_impostazioni.triggered.connect(self.apri_impostazioni)

        #Menu tendina
        menuFinestre.addAction(action_Filemanager)

        #Aggiunta di impostazioni
        menuBar.addAction(action_impostazioni)
        
        #====Lazy Loading di Filemanager====
        """ Filemanager e tutte le altre funzioni rimangono caricate in memoria anche quando non vengono utilizzate"""
        self.Filemanager = FileManagerWindow()
        self.Filemanager.destroyed.connect(lambda: self.tab.removeTab(self.tab.indexOf(self.Filemanager)))
        self.Filemanager.new_tab_ready.connect(self.aggiungi_tab)


        #====Sezione per la gestione Finestre====
        self.tab = DetachableTabWidget()

        self.tab.setTabsClosable(True)

        self.setCentralWidget(self.tab)
        self.icona_x = self.style().standardIcon(QStyle.StandardPixmap.SP_DialogCloseButton)
    
    #===Sezione Funzioni collegate alle Azioni====
    def apri_FileManager(self):
        if self.Filemanager == None:
            self.Filemanager = FileManagerWindow()
            self.Filemanager.destroyed.connect(lambda: self.tab.removeTab(self.tab.indexOf(self.Filemanager)))


        indice = self.tab.addTab(self.Filemanager, "File Manager")

            

        btn_chiudi = QPushButton()
        btn_chiudi.setIcon(self.icona_x)
        btn_chiudi.setStyleSheet("background-color: transparent; border: none;")
        btn_chiudi.clicked.connect(lambda: self.chiudi_scheda(indice))

        self.tab.tabBar().setTabButton(indice, QTabBar.ButtonPosition.RightSide, btn_chiudi)               
        
    def apri_impostazioni(self):
        """
        Apre il dialogo impostazioni in modalità modale.
        Blocca la finestra principale fino alla chiusura.
        Se l'utente salva, aggiorna i colori nel model.
        """
        
        changed = open_settings(parent=self)
        print(f"2 - dopo open_settings, changed={changed}")
        if changed:
            self.Filemanager.model.refresh_histories()
    def chiudi_scheda(self, indice):
        self.tab.removeTab(indice)

    def aggiungi_tab(self,widget :QWidget,name: str):
        
        btn_chiudi = QPushButton()
        btn_chiudi.setIcon(self.icona_x)
        btn_chiudi.setStyleSheet("background-color: transparent; border: none;")

        indice = self.tab.addTab(widget,name)
        self.tab.tabBar().setTabButton(indice, QTabBar.ButtonPosition.RightSide, btn_chiudi)
        btn_chiudi.clicked.connect(lambda: self.chiudi_scheda(indice))

    def drag_event(self,widget):
        self.tab.removeTab(self.tab.get)
        

if __name__ ==  "__main__":
    app = QApplication(sys.argv)
    window =  Hub()
    window.show()
    sys.exit(app.exec())
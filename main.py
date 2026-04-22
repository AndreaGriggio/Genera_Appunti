import sys
from PyQt6.QtWidgets import QApplication
from src.GUI.Core.Filemanager import FileManagerWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FileManagerWindow()
    window.show()
    sys.exit(app.exec())
    
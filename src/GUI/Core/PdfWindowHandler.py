from pathlib import Path

from PyQt6.QtCore import QObject, pyqtSignal

from src.GUI.MainHub.PDFViewer import PDFViewerWidget


class PdfWindowHandler(QObject):
    """
    Tiene traccia delle finestre PDF aperte ed evita che PyQt le distrugga
    prematuramente (il garbage collector Python rilascia l'oggetto se non
    c'è nessun riferimento Python vivo, anche se la finestra è visibile).

    Emette:
      - new_tab_ready(QWidget, str): quando una nuova finestra è pronta
        (usato dall'Hub per aggiungerla come tab se necessario)
    """

    new_tab_ready = pyqtSignal(object, str)  # (PDFViewerWidget, titolo)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._windows: list[PDFViewerWidget] = []

    # ── API pubblica ────────────────────────────────────────────────────────

    def open(self, file_path: str) -> None:
        """Apre un PDF in una nuova finestra viewer."""
        try:
            viewer = PDFViewerWidget(file_path)
        except Exception as exc:
            print(f"[PdfWindowPool] impossibile aprire '{file_path}': {exc}")
            return

        name = Path(file_path).name
        viewer.setWindowTitle(name)
        self._windows.append(viewer)
        viewer.destroyed.connect(self._cleanup)
        viewer.show()
        viewer.activateWindow()
        viewer.raise_()
        viewer.setFocus()
        self.new_tab_ready.emit(viewer, name)

    def close_all(self) -> None:
        """Chiude tutte le finestre aperte. Da chiamare nel closeEvent."""
        for w in list(self._windows):
            try:
                w.close()
            except RuntimeError:
                pass
        self._windows.clear()

    # ── Interni ─────────────────────────────────────────────────────────────

    def _cleanup(self) -> None:
        """Rimuove dal registro le finestre che sono state distrutte."""
        alive: list[PDFViewerWidget] = []
        for w in self._windows:
            try:
                if w is not None and not w.isHidden():
                    alive.append(w)
            except RuntimeError:
                pass
        self._windows = alive
import sys
from pathlib import Path

from PyQt6.QtCore import QEvent, QPointF, Qt
from PyQt6.QtGui import QKeySequence, QShortcut
from PyQt6.QtPdf import QPdfDocument
from PyQt6.QtPdfWidgets import QPdfView
from PyQt6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class NativePdfView(QPdfView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._zoom_in_handler = None
        self._zoom_out_handler = None
        self.viewport().installEventFilter(self)

    def bind_zoom_handlers(self, zoom_in_handler, zoom_out_handler):
        self._zoom_in_handler = zoom_in_handler
        self._zoom_out_handler = zoom_out_handler

    def eventFilter(self, obj, event):
        if obj == self.viewport() and event.type() == QEvent.Type.Wheel:
            if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
                if event.angleDelta().y() > 0 and self._zoom_in_handler is not None:
                    self._zoom_in_handler()
                elif event.angleDelta().y() < 0 and self._zoom_out_handler is not None:
                    self._zoom_out_handler()
                return True
        return super().eventFilter(obj, event)


class PDFViewerWidget(QWidget):
    ZOOM_STEP = 1.25
    MIN_ZOOM = 0.3
    MAX_ZOOM = 3.0

    def __init__(self, pdf_path: str, parent=None):
        super().__init__(parent)

        self.pdf_path = Path(pdf_path)
        if not self.pdf_path.exists():
            raise FileNotFoundError(f"PDF non trovato: {pdf_path}")

        self.document = QPdfDocument(self)
        load_error = self.document.load(str(self.pdf_path))
        if load_error != QPdfDocument.Error.None_:
            raise RuntimeError(f"Impossibile aprire il PDF: {load_error.name}")

        self.current_page = 0
        self.zoom_factor = 1.0

        self._setup_ui()
        self._connect_signals()
        self._apply_zoom(self.zoom_factor)
        self._update_controls()

    def _setup_ui(self):
        self.setWindowTitle(self.pdf_path.name)
        self.resize(1000, 800)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(8, 8, 8, 8)

        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)

        self.prev_btn = QPushButton("◀ Prev")
        self.prev_btn.setFixedWidth(90)
        self.prev_btn.clicked.connect(self.prev_page)
        toolbar.addWidget(self.prev_btn)

        self.next_btn = QPushButton("Next ▶")
        self.next_btn.setFixedWidth(90)
        self.next_btn.clicked.connect(self.next_page)
        toolbar.addWidget(self.next_btn)

        toolbar.addStretch()

        self.zoom_out_btn = QPushButton("Zoom -")
        self.zoom_out_btn.setFixedWidth(80)
        self.zoom_out_btn.clicked.connect(self.zoom_out)
        toolbar.addWidget(self.zoom_out_btn)

        self.zoom_label = QLabel()
        self.zoom_label.setFixedWidth(55)
        self.zoom_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.zoom_label.setStyleSheet("color: #f2f2f2; font-weight: 600;")
        toolbar.addWidget(self.zoom_label)

        self.zoom_in_btn = QPushButton("Zoom +")
        self.zoom_in_btn.setFixedWidth(80)
        self.zoom_in_btn.clicked.connect(self.zoom_in)
        toolbar.addWidget(self.zoom_in_btn)

        toolbar.addStretch()

        self.page_label = QLabel()
        self.page_label.setStyleSheet(
            "padding: 4px 10px; "
            "background: #2f3238; "
            "color: #f3f4f6; "
            "border: 1px solid #4a4f57; "
            "border-radius: 6px; "
            "font-weight: 600;"
        )
        toolbar.addWidget(self.page_label)

        layout.addLayout(toolbar)

        self.pdf_view = NativePdfView(self)
        self.pdf_view.setDocument(self.document)
        self.pdf_view.setPageMode(QPdfView.PageMode.MultiPage)
        self.pdf_view.setZoomMode(QPdfView.ZoomMode.Custom)
        self.pdf_view.setPageSpacing(12)
        self.pdf_view.bind_zoom_handlers(self.zoom_in, self.zoom_out)
        self.pdf_view.setStyleSheet("background: #232323;")
        layout.addWidget(self.pdf_view)

        self.shortcut_zoom_in = QShortcut(QKeySequence("Ctrl++"), self)
        self.shortcut_zoom_in.activated.connect(self.zoom_in)
        self.shortcut_zoom_in_alt = QShortcut(QKeySequence("Ctrl+="), self)
        self.shortcut_zoom_in_alt.activated.connect(self.zoom_in)
        self.shortcut_zoom_out = QShortcut(QKeySequence("Ctrl+-"), self)
        self.shortcut_zoom_out.activated.connect(self.zoom_out)
        self.shortcut_next_right = QShortcut(QKeySequence(Qt.Key.Key_Right), self)
        self.shortcut_next_right.activated.connect(self.next_page)
        self.shortcut_next_down = QShortcut(QKeySequence(Qt.Key.Key_Down), self)
        self.shortcut_next_down.activated.connect(self.next_page)
        self.shortcut_next_pagedown = QShortcut(QKeySequence(Qt.Key.Key_PageDown), self)
        self.shortcut_next_pagedown.activated.connect(self.next_page)
        self.shortcut_prev_left = QShortcut(QKeySequence(Qt.Key.Key_Left), self)
        self.shortcut_prev_left.activated.connect(self.prev_page)
        self.shortcut_prev_up = QShortcut(QKeySequence(Qt.Key.Key_Up), self)
        self.shortcut_prev_up.activated.connect(self.prev_page)
        self.shortcut_prev_pageup = QShortcut(QKeySequence(Qt.Key.Key_PageUp), self)
        self.shortcut_prev_pageup.activated.connect(self.prev_page)

    def _connect_signals(self):
        navigator = self.pdf_view.pageNavigator()
        navigator.currentPageChanged.connect(self._on_current_page_changed)
        self.pdf_view.zoomFactorChanged.connect(self._on_zoom_factor_changed)

    def _page_text(self) -> str:
        return f"Page {self.current_page + 1} / {self.document.pageCount()}"

    def _apply_zoom(self, zoom_factor: float):
        self.zoom_factor = max(self.MIN_ZOOM, min(self.MAX_ZOOM, zoom_factor))
        self.pdf_view.setZoomMode(QPdfView.ZoomMode.Custom)
        self.pdf_view.setZoomFactor(self.zoom_factor)
        self._update_controls()

    def _jump_to_page(self, page_index: int):
        page_index = max(0, min(self.document.pageCount() - 1, page_index))
        self.current_page = page_index
        self.pdf_view.pageNavigator().jump(page_index, QPointF(), self.zoom_factor)
        self._update_controls()

    def _update_controls(self):
        page_count = self.document.pageCount()
        self.prev_btn.setEnabled(self.current_page > 0)
        self.next_btn.setEnabled(self.current_page < page_count - 1)
        self.zoom_out_btn.setEnabled(self.zoom_factor > self.MIN_ZOOM)
        self.zoom_in_btn.setEnabled(self.zoom_factor < self.MAX_ZOOM)
        self.zoom_label.setText(f"{int(self.zoom_factor * 100)}%")
        self.page_label.setText(self._page_text())

    def _on_current_page_changed(self, page_index: int):
        self.current_page = max(0, page_index)
        self._update_controls()

    def _on_zoom_factor_changed(self, zoom_factor: float):
        self.zoom_factor = zoom_factor
        self._update_controls()

    def prev_page(self):
        self._jump_to_page(self.current_page - 1)

    def next_page(self):
        self._jump_to_page(self.current_page + 1)

    def zoom_in(self):
        self._apply_zoom(self.zoom_factor * self.ZOOM_STEP)

    def zoom_out(self):
        self._apply_zoom(self.zoom_factor / self.ZOOM_STEP)

    def keyPressEvent(self, event):
        key = event.key()
        if key in (Qt.Key.Key_Right, Qt.Key.Key_Down, Qt.Key.Key_PageDown):
            self.next_page()
            event.accept()
        elif key in (Qt.Key.Key_Left, Qt.Key.Key_Up, Qt.Key.Key_PageUp):
            self.prev_page()
            event.accept()
        elif key in (Qt.Key.Key_Plus, Qt.Key.Key_Equal):
            self.zoom_in()
            event.accept()
        elif key == Qt.Key.Key_Minus:
            self.zoom_out()
            event.accept()
        else:
            super().keyPressEvent(event)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python PDFViewer.py <percorso_pdf>")
        sys.exit(1)

    app = QApplication(sys.argv)
    try:
        viewer = PDFViewerWidget(sys.argv[1])
    except Exception as exc:
        QMessageBox.critical(None, "Errore PDF Viewer", str(exc))
        sys.exit(1)

    viewer.show()
    sys.exit(app.exec())

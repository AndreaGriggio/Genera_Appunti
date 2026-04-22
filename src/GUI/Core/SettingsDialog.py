"""
SettingsDialog.py
-----------------
Dialogo modale per le impostazioni dell'applicazione.
Blocca la finestra principale fino alla chiusura (QDialog.exec()).

Sezioni:
  1. Colori — colori dei file nel tree view
  2. Parametri — valori di config.py (temperature, max_tokens, system prompt)
  3. Chiavi API — NOTION_TOKEN, BASE_ID, GEMINI_TOKEN
"""

from PyQt6.QtGui import QColor, QFont, QPalette
from PyQt6.QtCore import Qt
import json
import os
from pathlib import Path
import re
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget,
    QWidget, QLabel, QPushButton, QLineEdit,
    QTextEdit, QDoubleSpinBox, QSpinBox,
    QColorDialog, QFrame, QScrollArea,
    QFormLayout, QSizePolicy, QMessageBox,
    QTableWidget, QTableWidgetItem, QHeaderView,   # ← aggiungi
    QCheckBox, QAbstractItemView                    # ← aggiungi
)
from PyQt6.QtCore import Qt
from src.GUI.config import FREE_MODELS as _DEFAULTS_MODELS
class _ModelsTab(QWidget):
    def __init__(self, settings: dict, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(16, 16, 16, 16)

        # Nota esplicativa
        note = QLabel(
            "I modelli vengono scelti automaticamente in ordine di lista: "
            "il primo disponibile viene usato, se fallisce si passa al successivo.\n"
            "I modelli Gemini sono più capaci, i Gemma sono più leggeri. "
            "Ordina dalla riga più in alto (priorità massima) verso il basso."
        )
        note.setWordWrap(True)
        layout.addWidget(note)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(sep)

        # Bottone fetch
        btn_fetch = QPushButton("🔄  Recupera modelli da Google")
        btn_fetch.setFixedWidth(260)
        btn_fetch.clicked.connect(self._fetch_models)
        layout.addWidget(btn_fetch, alignment=Qt.AlignmentFlag.AlignLeft)

        self._status = QLabel("")
        self._status.setStyleSheet("color: gray; font-size: 11px;")
        layout.addWidget(self._status)

        # Tabella
        self._table = QTableWidget(0, 4)
        self._table.setHorizontalHeaderLabels(["Nome", "PDF", "JSON", "Abilitato"])
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self._table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self._table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self._table.setColumnWidth(1, 50)
        self._table.setColumnWidth(2, 50)
        self._table.setColumnWidth(3, 80)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        layout.addWidget(self._table)

        btn_reset = QPushButton("↩  Ripristina modelli default")
        btn_reset.setFixedWidth(220)
        btn_reset.clicked.connect(self._reset_default)
        layout.addWidget(btn_reset, alignment=Qt.AlignmentFlag.AlignLeft)

        # Carica modelli esistenti da settings
        models = settings.get("FREE_MODELS", _DEFAULTS_MODELS)
        self._populate_table(models)

    def _make_checkbox_cell(self, checked: bool) -> QWidget:
        """Crea un widget centrato con una checkbox."""
        container = QWidget()
        h = QHBoxLayout(container)
        h.setContentsMargins(0, 0, 0, 0)
        h.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cb = QCheckBox()
        cb.setChecked(checked)
        h.addWidget(cb)
        return container

    def _populate_table(self, models: list):
        self._table.setRowCount(0)
        for m in models:
            row = self._table.rowCount()
            self._table.insertRow(row)

            self._table.setItem(row, 0, QTableWidgetItem(m["name"]))
            self._table.setCellWidget(row, 1, self._make_checkbox_cell(m.get("pdf", False)))
            self._table.setCellWidget(row, 2, self._make_checkbox_cell(m.get("config", False)))
            self._table.setCellWidget(row, 3, self._make_checkbox_cell(m.get("available", True)))

    def _fetch_models(self):
        self._status.setText("Recupero modelli in corso...")

        saved = _load_settings()
        api_key = saved.get("GEMINI_TOKEN", "")

        try:
            from google.genai import Client
            client = Client(api_key=api_key)
            remote = list(client.models.list())

            # Filtra solo modelli generativi
            generativi = [
                m for m in remote
                if hasattr(m, 'supported_actions') and 'generateContent' in (m.supported_actions or [])
            ]

            # Costruisci lista con default intelligenti
            models = []
            for m in generativi:
                name = str(m.name).replace("models/", "")
                is_gemini = "gemini" in name
                models.append({
                    "name": name,
                    "pdf": is_gemini,
                    "text": True,
                    "available": True,
                    "config": is_gemini,
                })

            models = _sort_models(models)
            self._populate_table(models)
            self._status.setText(f"{len(models)} modelli trovati.")

        except Exception as e:
            self._status.setText(f"Errore: {e}")

    def _reset_default(self):
        from src.GUI.config import FREE_MODELS
        self._populate_table(FREE_MODELS)
        self._status.setText("↩ Modelli ripristinati ai default.")

    def collect(self) -> dict:
        models = []
        for row in range(self._table.rowCount()):
            name = self._table.item(row, 0).text()

            def get_cb(col):
                w = self._table.cellWidget(row, col)
                return w.findChild(QCheckBox).isChecked()

            models.append({
                "name": name,
                "pdf": get_cb(1),
                "text": True,
                "available": get_cb(3),
                "config": get_cb(2),
            })
        return {"FREE_MODELS": models}
def _sort_models(models: list) -> list:
    gemini, gemma, altri = [], [], []

    for m in models:
        name = m["name"]
        if "gemini" in name:
            gemini.append(m)
        elif "gemma" in name:
            gemma.append(m)
        else:
            altri.append(m)

    def gemini_key(m):
        match = re.search(r'(\d+\.\d+)', m["name"])
        version = float(match.group(1)) if match else 0
        name = m["name"]
        if "pro" in name:       tier = 2
        elif "flash-lite" in name: tier = 0
        else:                   tier = 1
        return (-version, -tier)

    def gemma_key(m):
        match = re.search(r'(\d+)b', m["name"])
        params = int(match.group(1)) if match else 0
        return -params

    gemini.sort(key=gemini_key)
    gemma.sort(key=gemma_key)
    return gemini + gemma + altri



# ---------- Percorso settings ----------
from src.GUI.config import (
    SETTINGS_PATH        as _SETTINGS_PATH,
    NOTION_TOKEN         as _DEF_NOTION_TOKEN,
    BASE_ID              as _DEF_BASE_ID,
    GEMINI_TOKEN         as _DEF_GEMINI_TOKEN,
    TEMPERATURE          as _DEF_TEMPERATURE,
    MAX_TOKENS           as _DEF_MAX_TOKENS,
    COLOR_LOADED         as _DEF_COLOR_LOADED,
    COLOR_CREATED        as _DEF_COLOR_CREATED,
    NOTION_SYSTEM_INSTRUCTION as _DEF_SYSTEM_PROMPT,
)
# Valori di default (specchio di config.py)
_DEFAULTS = {
    "NOTION_TOKEN":  _DEF_NOTION_TOKEN  or "",
    "BASE_ID":       _DEF_BASE_ID       or "",
    "GEMINI_TOKEN":  _DEF_GEMINI_TOKEN  or "",
    "SYSTEM_PROMPT": _DEF_SYSTEM_PROMPT,
    "TEMPERATURE":   _DEF_TEMPERATURE,
    "MAX_TOKENS":    _DEF_MAX_TOKENS,
    "COLOR_LOADED":  _DEF_COLOR_LOADED,
    "COLOR_CREATED": _DEF_COLOR_CREATED,
}



def _load_settings() -> dict:
    """Legge settings.json; se non esiste restituisce i default."""
    if _SETTINGS_PATH.exists():
        try:

            with open(_SETTINGS_PATH, "r", encoding="utf-8") as f:
                saved = json.load(f)
            merged = _DEFAULTS.copy()
            merged.update(saved)
            return merged
        except Exception:
            pass
    return _DEFAULTS.copy()


def _save_settings(data: dict) -> bool:
    """Scrive settings.json e aggiorna os.environ per le API key."""
    try:
        _SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(_SETTINGS_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

        # Aggiorna subito le variabili d'ambiente nella sessione corrente
        for env_key, setting_key in [
            ("GEMINI_API_KEY", "GEMINI_TOKEN"),
            ("NOTION_API_KEY", "NOTION_TOKEN"),
        ]:
            val = data.get(setting_key, "")
            if val:
                os.environ[env_key] = val

        return True
    except Exception as e:
        print(f"Errore salvataggio settings: {e}")
        return False


# ============================================================
#  Widget riutilizzabile: selettore colore
# ============================================================
class _ColorPicker(QWidget):
    """Riga con etichetta, anteprima colore e bottone 'Scegli'."""

    def __init__(self, label: str, initial_hex: str, parent=None):
        super().__init__(parent)
        self._color = QColor(initial_hex)

        row = QHBoxLayout(self)
        row.setContentsMargins(0, 4, 0, 4)

        lbl = QLabel(label)
        lbl.setMinimumWidth(220)
        row.addWidget(lbl)

        self._preview = QFrame()
        self._preview.setFixedSize(36, 24)
        self._preview.setFrameShape(QFrame.Shape.Box)
        self._preview.setStyleSheet(f"background-color: {self._color.name()}; border: 1px solid #555;")
        row.addWidget(self._preview)

        self._hex_label = QLabel(self._color.name())
        self._hex_label.setMinimumWidth(80)
        row.addWidget(self._hex_label)

        btn = QPushButton("Scegli…")
        btn.setFixedWidth(80)
        btn.clicked.connect(self._pick)
        row.addWidget(btn)
        row.addStretch()

    def _pick(self):
        chosen = QColorDialog.getColor(self._color, self, "Scegli colore")
        if chosen.isValid():
            self._color = chosen
            hex_val = chosen.name()
            self._preview.setStyleSheet(f"background-color: {hex_val}; border: 1px solid #555;")
            self._hex_label.setText(hex_val)

    def hex_color(self) -> str:
        return self._color.name()


# ============================================================
#  Sezione 1 — Colori
# ============================================================
class _ColorsTab(QWidget):
    def __init__(self, settings: dict, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        header = QLabel("Personalizza i colori dei file nel pannello di navigazione.")
        header.setWordWrap(True)
        layout.addWidget(header)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(sep)

        self._loaded = _ColorPicker(
            "File caricato su Notion",
            settings.get("COLOR_LOADED", _DEFAULTS["COLOR_LOADED"])
        )
        layout.addWidget(self._loaded)

        self._created = _ColorPicker(
            "File con appunti generati (non ancora su Notion)",
            settings.get("COLOR_CREATED", _DEFAULTS["COLOR_CREATED"])
        )
        layout.addWidget(self._created)

        note = QLabel(
            "I file non elaborati rimangono con il colore predefinito del sistema."
        )
        note.setStyleSheet("color: gray; font-size: 11px;")
        note.setWordWrap(True)
        layout.addWidget(note)
        layout.addStretch()

    def collect(self) -> dict:
        return {
            "COLOR_LOADED": self._loaded.hex_color(),
            "COLOR_CREATED": self._created.hex_color(),
        }


# ============================================================
#  Sezione 2 — Parametri modello
# ============================================================
class _ParamsTab(QWidget):
    def __init__(self, settings: dict, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        header = QLabel(
            "Questi parametri controllano il comportamento del modello Gemini "
            "e il prompt di sistema usato per generare gli appunti."
        )
        header.setWordWrap(True)
        layout.addWidget(header)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(sep)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form.setSpacing(10)

        # Temperature
        self._temp = QDoubleSpinBox()
        self._temp.setRange(0.0, 2.0)
        self._temp.setSingleStep(0.05)
        self._temp.setDecimals(2)
        self._temp.setValue(float(settings.get("TEMPERATURE", _DEFAULTS["TEMPERATURE"])))
        self._temp.setToolTip(
            "Controlla la creatività delle risposte.\n"
            "0.0 = deterministico, 2.0 = molto creativo.\n"
            "Per appunti tecnici si consiglia 0.1–0.3."
        )
        form.addRow("Temperature:", self._temp)

        # Max tokens
        self._max_tok = QSpinBox()
        self._max_tok.setRange(256, 65536)
        self._max_tok.setSingleStep(256)
        self._max_tok.setValue(int(settings.get("MAX_TOKENS", _DEFAULTS["MAX_TOKENS"])))
        self._max_tok.setToolTip("Numero massimo di token nella risposta generata.")
        form.addRow("Max output tokens:", self._max_tok)

        layout.addLayout(form)

        # System prompt
        prompt_lbl = QLabel("System Prompt (istruzioni di ruolo per Gemini):")
        layout.addWidget(prompt_lbl)

        self._prompt = QTextEdit()
        self._prompt.setPlainText(
            settings.get("SYSTEM_PROMPT", _DEFAULTS["SYSTEM_PROMPT"])
        )
        self._prompt.setMinimumHeight(180)
        self._prompt.setFont(QFont("Courier New", 10))
        layout.addWidget(self._prompt)

        reset_btn = QPushButton("↩  Ripristina default")
        reset_btn.setFixedWidth(160)
        reset_btn.clicked.connect(self._reset_prompt)
        layout.addWidget(reset_btn, alignment=Qt.AlignmentFlag.AlignLeft)

    def _reset_prompt(self):
        self._prompt.setPlainText(_DEFAULTS["SYSTEM_PROMPT"])
        self._temp.setValue(_DEFAULTS["TEMPERATURE"])
        self._max_tok.setValue(_DEFAULTS["MAX_TOKENS"])

    def collect(self) -> dict:
        return {
            "TEMPERATURE": self._temp.value(),
            "MAX_TOKENS": self._max_tok.value(),
            "SYSTEM_PROMPT": self._prompt.toPlainText(),
        }


# ============================================================
#  Sezione 3 — Chiavi API
# ============================================================
class _ApiKeysTab(QWidget):
    def __init__(self, settings: dict, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        header = QLabel(
            "Inserisci le tue chiavi API. Vengono salvate in "
            "<b>settings.json</b> nella cartella del progetto "
            "e hanno la precedenza sulle variabili d'ambiente."
        )
        header.setWordWrap(True)
        layout.addWidget(header)

        warn = QLabel("⚠️  Non condividere questo file con nessuno.")
        warn.setStyleSheet("color: #c0392b; font-weight: bold;")
        layout.addWidget(warn)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(sep)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form.setSpacing(14)

        def _make_key_field(placeholder: str, current: str) -> QLineEdit:
            field = QLineEdit()
            field.setPlaceholderText(placeholder)
            field.setText(current)
            field.setEchoMode(QLineEdit.EchoMode.Password)
            field.setMinimumWidth(380)
            return field

        self._notion = _make_key_field(
            "secret_xxxx…",
            settings.get("NOTION_TOKEN", "")
        )
        form.addRow("Notion API Token:", self._notion)

        self._base_id = _make_key_field(
            "ID pagina radice Notion (es. 2a68f1de…)",
            settings.get("BASE_ID", "")
        )
        self._base_id.setEchoMode(QLineEdit.EchoMode.Normal)   # L'ID non è segreto
        form.addRow("Notion Base Page ID:", self._base_id)

        self._gemini = _make_key_field(
            "AIzaSy…",
            settings.get("GEMINI_TOKEN", "")
        )
        form.addRow("Gemini API Key:", self._gemini)

        layout.addLayout(form)

        # Toggle mostra/nascondi
        toggle_btn = QPushButton("Mostra / Nascondi chiavi")
        toggle_btn.setFixedWidth(200)
        toggle_btn.setCheckable(True)
        toggle_btn.toggled.connect(self._toggle_visibility)
        layout.addWidget(toggle_btn, alignment=Qt.AlignmentFlag.AlignLeft)

        note = QLabel(
            "Lascia un campo vuoto per continuare a usare la variabile d'ambiente corrispondente."
        )
        note.setStyleSheet("color: gray; font-size: 11px;")
        note.setWordWrap(True)
        layout.addWidget(note)
        layout.addStretch()

    def _toggle_visibility(self, visible: bool):
        mode = QLineEdit.EchoMode.Normal if visible else QLineEdit.EchoMode.Password
        self._notion.setEchoMode(mode)
        self._gemini.setEchoMode(mode)
        # BASE_ID rimane sempre visibile

    def collect(self) -> dict:
        return {
            "NOTION_TOKEN": self._notion.text().strip(),
            "BASE_ID": self._base_id.text().strip(),
            "GEMINI_TOKEN": self._gemini.text().strip(),
        }


# ============================================================
#  Dialogo principale
# ============================================================
class SettingsDialog(QDialog):
    """
    Dialogo modale per le impostazioni.

    Uso:
        dialog = SettingsDialog(parent=self)
        dialog.exec()   # blocca la finestra principale

    Dopo exec() puoi chiamare dialog.settings_changed per sapere
    se l'utente ha salvato qualcosa.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Impostazioni")
        self.setMinimumSize(620, 520)
        self.setModal(True)   # blocca la finestra padre

        self.settings_changed = False
        self._data = _load_settings()

        self._build_ui()
        self._apply_style()

    # ----------------------------------------------------------
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setSpacing(0)
        root.setContentsMargins(0, 0, 0, 0)

        # ---- Header ----
        header_widget = QWidget()
        header_widget.setObjectName("header")
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(20, 14, 20, 14)

        title = QLabel("Impostazioni")
        title.setObjectName("title")
        header_layout.addWidget(title)
        header_layout.addStretch()
        root.addWidget(header_widget)

        # ---- Tabs ----
        self._tabs = QTabWidget()
        self._tabs.setDocumentMode(True)

        self._tab_colors = _ColorsTab(self._data)
        self._tab_params = _ParamsTab(self._data)
        self._tab_keys   = _ApiKeysTab(self._data)
        self._tab_models = _ModelsTab(self._data)

        for tab_widget, label in [
            (self._tab_colors, "Colori"),
            (self._tab_params, "Modello"),
            (self._tab_keys,   "Chiavi API"),
            (self._tab_models, "Modelli AI"), 
        ]:
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setWidget(tab_widget)
            scroll.setFrameShape(QFrame.Shape.NoFrame)
            self._tabs.addTab(scroll, label)

        root.addWidget(self._tabs)

        # ---- Footer con bottoni ----
        footer = QWidget()
        footer.setObjectName("footer")
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(16, 12, 16, 12)
        footer_layout.setSpacing(10)

        footer_layout.addStretch()

        btn_cancel = QPushButton("Annulla")
        btn_cancel.setObjectName("btn_cancel")
        btn_cancel.setFixedWidth(100)
        btn_cancel.clicked.connect(self.reject)
        footer_layout.addWidget(btn_cancel)

        btn_save = QPushButton("💾  Salva")
        btn_save.setObjectName("btn_save")
        btn_save.setFixedWidth(110)
        btn_save.clicked.connect(self._save)
        footer_layout.addWidget(btn_save)

        root.addWidget(footer)

    # ----------------------------------------------------------
    def _save(self):
        """Raccoglie i dati da tutti i tab e salva."""
        merged = {}
        merged.update(self._tab_colors.collect())
        merged.update(self._tab_params.collect())
        merged.update(self._tab_keys.collect())
        merged.update(self._tab_models.collect()) 

        if _save_settings(merged):
            self._data = merged
            self.settings_changed = True
            QMessageBox.information(
                self,
                "Salvato",
                "Impostazioni salvate.\n\n"
                "Riavvia l'applicazione per applicare le modifiche alle chiavi API."
            )
            self.accept()
        else:
            QMessageBox.critical(self, "Errore", "Impossibile salvare le impostazioni.")

    # ----------------------------------------------------------
    def _apply_style(self):
        self.setStyleSheet("""
            QPushButton#btn_save {
                font-weight: bold;
            }
        """)


# ============================================================
#  Funzione di utilità per aprire il dialogo dalla GUI
# ============================================================
def open_settings(parent=None) -> bool:
    """
    Apre il dialogo impostazioni in modalità modale.
    Restituisce True se l'utente ha salvato qualcosa.
    """
    dialog = SettingsDialog(parent)
    dialog.exec()
    return dialog.settings_changed


# ============================================================
#  Test standalone
# ============================================================
if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    changed = open_settings()
    print("Impostazioni cambiate:", changed)
    sys.exit(0)

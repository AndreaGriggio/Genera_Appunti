# -*- mode: python ; coding: utf-8 -*-
# PyInstaller .spec per Generatore Appunti — TARGET: Linux (max compatibilità)
#
# WORKFLOW CORRETTO:
#   1. python download_whisper_model.py     <- scarica il modello UNA VOLTA
#   2. pyinstaller Filemanager.spec         <- builda l'app
#   3. Testa: dist/GeneratoreAppunti/GeneratoreAppunti
#
# PER MASSIMA COMPATIBILITÀ DISTRO:
#   Builda dentro Docker (Ubuntu 22.04) invece che sulla tua macchina.
#   Vedi Dockerfile.build nella stessa cartella.

import sys
import os
from pathlib import Path
from PyInstaller.utils.hooks import (
    collect_data_files,
    collect_submodules,
    collect_dynamic_libs,
)

PROJECT_ROOT = Path(SPECPATH)
MAIN_SCRIPT  = str(PROJECT_ROOT / "src" / "GUI" / "Filemanager.py")

# Cartella del modello Whisper creata da download_whisper_model.py
WHISPER_MODEL_DIR = PROJECT_ROOT / "faster-whisper-tiny"

if not WHISPER_MODEL_DIR.exists():
    raise FileNotFoundError(
        f"\n\n❌ Modello Whisper non trovato in: {WHISPER_MODEL_DIR}\n"
        "   Esegui prima: python download_whisper_model.py\n"
    )

# =============================================================================
# DATAS
# =============================================================================
datas = []

# Plugin Qt (xcb, wayland, ecc.) — obbligatori per aprire la finestra
datas += collect_data_files("PyQt6")

# Asset interni di faster-whisper e ctranslate2
datas += collect_data_files("faster_whisper")
datas += collect_data_files("ctranslate2")

try:
    datas += collect_data_files("tokenizers")
except Exception:
    pass

# ─── Modello Whisper bundlato ────────────────────────────────────────────────
# Copia tutta la cartella faster-whisper-tiny/ dentro il bundle.
# A runtime whisperProcess.py la cercherà in sys._MEIPASS/faster-whisper-tiny/
datas += [(str(WHISPER_MODEL_DIR), "faster-whisper-tiny")]

# =============================================================================
# BINARIES
# =============================================================================
binaries = []

# ctranslate2 usa .so che PyInstaller non rileva automaticamente
binaries += collect_dynamic_libs("ctranslate2")

# =============================================================================
# HIDDEN IMPORTS
# =============================================================================
hidden_imports = [
    # PyQt6
    "PyQt6", "PyQt6.QtCore", "PyQt6.QtGui", "PyQt6.QtWidgets", "PyQt6.sip",

    # Google Generative AI
    "google.genai",
    "google.auth",
    "google.auth.transport",
    "google.auth.transport.requests",
    "httpx",
    "httpcore",

    # Notion
    "notion_client",
    "notion_client.errors",

    # Whisper stack
    "faster_whisper",
    *collect_submodules("faster_whisper"),
    "ctranslate2",
    *collect_submodules("ctranslate2"),
    "tokenizers",
    *collect_submodules("tokenizers"),
    "huggingface_hub",
    *collect_submodules("huggingface_hub"),

    # PDF
    "fitz",
    "pymupdf",

    # Pandoc
    "pypandoc",
    "pytinytex",

    # Pydantic
    "pydantic",
    "pydantic.v1",
    *collect_submodules("pydantic"),

    # Multiprocessing (fork su Linux, ma meglio includerli)
    "multiprocessing",
    "multiprocessing.spawn",
    "multiprocessing.resource_tracker",
]

# =============================================================================
# EXCLUDES
# =============================================================================
excludes = [
    "tkinter", "_tkinter",
    "scipy",
    "IPython", "jupyter", "notebook",
    "pytest", "unittest",
    "xmlrpc", "doctest", "pdb",
    "matplotlib",   # importato in NotionToMarkdown.py ma non usato
]

block_cipher = None

# =============================================================================
# ANALYSIS
# =============================================================================
a = Analysis(
    [MAIN_SCRIPT],
    pathex=[
        str(PROJECT_ROOT),
        str(PROJECT_ROOT / "src"),
    ],
    binaries=binaries,
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# =============================================================================
# EXE — one-folder
#
# Perché non one-file:
#   Con Whisper bundlato il bundle supera i 400MB.
#   One-file li estrae TUTTI in /tmp ad ogni avvio (5-15 secondi).
#   One-folder si avvia in meno di 1 secondo.
# =============================================================================
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="GeneratoreAppunti",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,        # NON mettere True: rompe ctranslate2
    upx=False,          # NON mettere True su Linux: rompe i .so
    console=True,       # Tienilo True finché testi; poi metti False
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="GeneratoreAppunti",
)

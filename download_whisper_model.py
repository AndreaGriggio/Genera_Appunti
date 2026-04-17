#!/usr/bin/env python3
"""
Esegui questo script UNA VOLTA prima di fare il build PyInstaller.
Scarica il modello faster-whisper-tiny nella cartella del progetto
in modo che possa essere bundlato nell'eseguibile.

Uso:
    python download_whisper_model.py
"""
from pathlib import Path
from faster_whisper import WhisperModel
import shutil
import os

MODEL_NAME  = "medium"
DEST_FOLDER = Path(__file__).parent / f"faster-whisper-{MODEL_NAME}"

print(f"Scarico il modello '{MODEL_NAME}' nella cache HuggingFace...")
# Questo scarica il modello in ~/.cache/huggingface/hub/
model = WhisperModel(MODEL_NAME, device="cuda", compute_type="float32")

# Trova dove HuggingFace ha salvato il modello
from huggingface_hub import snapshot_download
cache_path = snapshot_download(
    repo_id=f"Systran/faster-whisper-{MODEL_NAME}",
    local_files_only=False,
)

print(f"Modello trovato in: {cache_path}")

# Copia nella cartella del progetto (accanto a questo script e al .spec)
if DEST_FOLDER.exists():
    print(f"Cartella {DEST_FOLDER} già esistente, la sovrascrivo...")
    shutil.rmtree(DEST_FOLDER)

shutil.copytree(cache_path, DEST_FOLDER)
print(f"✅ Modello copiato in: {DEST_FOLDER}")
print(f"   Dimensione: {sum(f.stat().st_size for f in DEST_FOLDER.rglob('*') if f.is_file()) / 1e6:.1f} MB")
print()
print("Ora puoi lanciare: pyinstaller Filemanager.spec")

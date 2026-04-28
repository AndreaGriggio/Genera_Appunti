# Generatore Appunti

Applicazione desktop per **generare appunti strutturati da PDF o tracce audio** e caricarli su Notion, con supporto alla generazione di **mappe mentali interattive**. Usa le API di Google Gemini per estrarre e strutturare il contenuto, le API di Notion per pubblicarlo e Faster-Whisper per trascrivere l'audio localmente.

---

## Funzionalità

- **Generazione appunti** — Invia un PDF o un file audio a Gemini e ricevi un documento strutturato pronto per Notion (heading, paragrafi, liste, tabelle, equazioni LaTeX).
- **Mappe mentali** — Genera e modifica visualmente mappe concettuali a partire da documenti. Le mappe si salvano in un formato `.mappa` proprietario e si esportano in PDF.
- **Sincronizzazione Notion** — Specchia la struttura delle pagine Notion in cartelle locali e carica gli appunti come sotto-pagine con un clic.
- **Trascrizione audio** — Trascrive file MP3, MP4, WAV, M4A e OGG in locale con Faster-Whisper prima di passarli a Gemini.
- **Gestione modelli** — Seleziona e ordina i modelli Gemini disponibili dal pannello Impostazioni. Il sistema scala automaticamente al modello successivo in caso di rate limit.
- **Scarica PDF** — Scarica il contenuto di una pagina Notion e lo converte in PDF tramite Pandoc e XeLaTeX.

---

## Flusso di utilizzo

```
[Aggiorna] → struttura cartelle locale da Notion
     ↓
Trascina PDF o audio nella cartella giusta
     ↓
[Crea Appunti] → file .json  |  [Crea Mappa] → file .mappa
     ↓
[Carica] → nuova sotto-pagina su Notion
     ↓
[Pulisci] → rimuove PDF e .json già caricati
```

---

## Struttura del progetto

```
Genera_Appunti/
├── main.py                        # Entry point
├── requirements.txt
├── download_whisper_model.py      # Script per scaricare il modello Whisper
├── faster-whisper-tiny/           # Modello Whisper bundlato (tiny)
├── faster-whisper-medium/         # Modello Whisper bundlato (medium)
└── src/
    └── GUI/
        ├── config.py              # Costanti, caricamento settings.json
        ├── Core/
        │   ├── Manager.py             # Finestra principale (QWidget)
        │   ├── FileActionHandler.py   # Business logic delle azioni utente
        │   ├── WorkerHandler.py       # Orchestrazione QThread e stato busy
        │   ├── WhisperHandler.py      # Processo Whisper multiprocessing
        │   ├── PdfWindowHandler.py    # Gestione finestre PDF aperte
        │   ├── ColorFileSystemModel.py # TreeView con colori di stato
        │   ├── DeleteWorker.py        # Pulizia file elaborati
        │   ├── DeleteSync.py          # Worker Qt per pulizia
        │   └── SettingsDialog.py      # Dialogo impostazioni
        ├── Gen/
        │   ├── GeminiAsker.py         # Chiamate API Gemini
        │   ├── GeminiAnswer.py        # Salvataggio risposte su disco
        │   ├── GeminiSync.py          # Worker Qt per Gemini
        │   └── ModelManager.py        # Gestione modelli e rate limit
        ├── Notion/
        │   ├── NotionBrancher.py      # Lettura albero Notion (threading)
        │   ├── NotionLoader.py        # Caricamento pagine su Notion
        │   ├── NotionParser.py        # JSON strutturato → blocchi Notion API
        │   ├── NotionSchema.py        # Schema Pydantic per la risposta Gemini
        │   ├── NotionDownloader.py    # Download blocchi da Notion
        │   ├── NotionSyncBrancher.py  # Worker Qt per sync struttura
        │   ├── NotionSyncLoader.py    # Worker Qt per upload
        │   └── NotionDownloaderSync.py # Worker Qt per download PDF
        ├── MapTree/
        │   ├── MapTreeGrid.py         # Scena e viewer dell'editor mappe
        │   ├── TextElement.py         # Nodo testo (QGraphicsTextItem)
        │   ├── LineElement.py         # Connessione tra nodi (QGraphicsPathItem)
        │   ├── Node.py / Element.py   # Strutture dati del grafo
        │   └── MapSchema.py           # Schema Pydantic per mappe generate da Gemini
        ├── MainHub/
        │   ├── Hub.py                 # Finestra principale con dock panel
        │   ├── DockPanel.py           # Pannello agganciabile
        │   └── PDFViewer.py           # Visualizzatore PDF interno
        ├── Convert/
        │   ├── NotionToMarkdown.py    # Blocchi Notion → Markdown
        │   └── MarkdownToPDF.py       # Markdown → PDF via Pandoc/XeLaTeX
        └── Transcribe/
            ├── whisperProcess.py      # Processo Whisper (multiprocessing)
            └── TranscribeWorker.py    # Trascrizione singolo file
```

---

## Prerequisiti

- Python **3.11+**
- [Pandoc](https://pandoc.org/installing.html) installato nel sistema
- Una distribuzione LaTeX con XeLaTeX (es. [TinyTeX](https://yihui.org/tinytex/) o TeX Live) con i pacchetti `amsmath`, `amssymb`, `cancel`, `mathtools`
- Un account **Google AI Studio** con API Key
- Un account **Notion** con Integration Token e ID della pagina radice

---

## Configurazione

Al primo avvio, apri **Strumenti → Impostazioni** e compila le tre sezioni:

| Campo | Dove trovarlo |
|---|---|
| **Gemini API Key** | [aistudio.google.com](https://aistudio.google.com) → Get API Key |
| **Notion API Token** | [notion.so/my-integrations](https://www.notion.so/my-integrations) → New Integration → copia il token `secret_xxx` |
| **Notion Base Page ID** | Apri la pagina radice → `...` → Copy link → stringa esadecimale nell'URL (es. `2a68f1dee7b6807789d1ebd7e3a87fb0`) |

> ⚠️ Ricorda di **condividere la pagina radice** con la tua Integration su Notion (tasto "Connect to" nella pagina stessa).

Le impostazioni vengono salvate in `src/GUI/settings.json`. Non aggiungere questo file a repository pubblici.

---

## Avvio

```bash
python main.py
```

---

## Colori nel pannello file

| Colore | Significato |
|---|---|
| 🟢 Verde | File caricato su Notion con successo |
| 🟡 Arancione | Appunti generati, non ancora caricati su Notion |
| Bianco/Default | File non ancora elaborato |

---

## Note importanti

**File `.id`** — Ogni cartella sincronizzata con Notion contiene un file nascosto `.id` con l'ID della corrispondente pagina Notion. Non modificare né eliminare questi file: l'applicazione li usa per associare cartelle locali a pagine remote. Su Linux non sono visibili nei file manager standard — questo è il comportamento atteso.

**Modelli Whisper** — Le cartelle `faster-whisper-tiny/` e `faster-whisper-medium/` contengono i pesi del modello per la trascrizione offline. Il modello da usare si configura in `whisperProcess.py`. Per scaricare un modello diverso usa `download_whisper_model.py`.

**Rate limit Gemini** — In caso di errore 429, il sistema scala automaticamente al modello successivo nella lista configurata in Impostazioni → Modelli AI. L'ordine della lista determina la priorità.

**Trascrizione audio** — Il processo Whisper gira in un sottoprocesso separato (`multiprocessing`) per non bloccare la UI. Se l'applicazione viene chiusa durante una trascrizione, il sottoprocesso viene terminato automaticamente.

**Scarica PDF** — Richiede Pandoc e XeLaTeX installati nel sistema. Se la conversione fallisce, controlla che i pacchetti LaTeX `amsmath`, `amssymb`, `cancel` e `mathtools` siano presenti.

---

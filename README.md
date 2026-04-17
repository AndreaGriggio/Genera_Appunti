#Generatore Appunti

Applicazione desktop per **generare appunti strutturati partendo da un PDF o una traccia audio ** e caricarli su Notion. Usa le API di Google Gemini per estrarre e strutturare il contenuto, e l'API di Notion per inserire la risposta all'interno della piattaforma.

---

## Flusso di utilizzo

```
[Aggiorna]-> Trova cartelle di Notion -> drag&drop un PDF o traccia audio→ [Crea] → appunti .json → [Carica] → pagina Notion

```

1. **Aggiorna** — Sincronizza la struttura di cartelle locale con l'albero di pagine Notion. Va fatto con , o quando aggiungi nuove pagine su Notion. **Attenzione** è necessario avere inserito un id base corretto all'intenro delle impostazioni 
2. **Crea** — Seleziona uno o più PDF e genera gli appunti con Gemini. I file risultanti vengono salvati nella stessa cartella del PDF come `.json`.
3. **Carica** — Seleziona i PDF (o i file già elaborati) e carica gli appunti come nuove sotto-pagine in Notion.
4. **Pulisci** — Elimina i PDF e i file `.json` già caricati su Notion con successo.

---

## Prerequisiti

- Python **3.11+**
- Un account **Google AI Studio** con una API Key per un progetto qualsiasi
- Un account **Notion** con una Integration Token e l'ID della pagina radice

### Dipendenze Python

```bash
pip install PyQt6 google-genai notion-client pymupdf
```

---

## Configurazione

Al primo avvio, apri **Impostazioni** dalla barra del menu e compila:

| Campo | Dove trovarlo |
|---|---|
| **Gemini API Key** | [aistudio.google.com](https://aistudio.google.com) → Get API Key |
| **Notion API Token** | [notion.so/my-integrations](https://www.notion.so/my-integrations) → New Integration → copia il token `secret_xxx` |
| **Notion Base Page ID** | Apri la pagina radice su Notion → clic su `...` → Copy link → l'ID è la stringa esadecimale nell'URL (es. `2a68f1dee7b6807789d1ebd7e3a87fb0`) |

> ⚠️ Assicurati di aver **condiviso la pagina radice** con la tua Integration su Notion (tasto "Connect to" nella pagina).

Le impostazioni vengono salvate in `settings.json` nella cartella del progetto. Non condividere questo file.

---

## Avvio

```bash
python -m src.GUI.Filemanager
```

oppure, se lanci direttamente:

```bash
python Filemanager.py
```

---

## Struttura del progetto

```
progetto/
├── src/GUI/
│   ├── Filemanager.py          # Finestra principale
│   ├── config.py               # Configurazione e costanti
│   ├── GeminiAsker.py          # Chiamate API Gemini
│   ├── GeminiAnswer.py         # Salvataggio risposte
│   ├── GeminiSync.py           # Worker Qt per Gemini
│   ├── ModelManager.py         # Gestione modelli e rate limit
│   ├── NotionBrancher.py       # Lettura albero Notion
│   ├── NotionLoader.py         # Caricamento pagine su Notion
│   ├── NotionParser.py         # Parsing JSON → blocchi Notion
│   ├── NotionSyncBrancher.py   # Worker Qt per sync Notion
│   ├── NotionSyncLoader.py     # Worker Qt per upload Notion
│   ├── FolderUpdater.py        # Crea cartelle locali da albero Notion
│   ├── ColorFileSystemModel.py # TreeView con colori di stato
│   ├── DeleteWorker.py         # Pulizia file elaborati
│   ├── DeleteSync.py           # Worker Qt per pulizia
│   └── SettingsDialog.py       # Dialogo impostazioni
├── Data/                       # Generata automaticamente
│   ├── dict_notion.json        # Albero Notion (generato da Aggiorna)
│   ├── history_pdf.json        # PDF elaborati da Gemini
│   ├── history_loaded.json     # File caricati su Notion
│   └── [struttura cartelle]/   # Specchio dell'albero Notion
│       └── .id                 # ID Notion della cartella (file nascosto) NON MODIFICARE O ELMINARE 
└── settings.json               # Configurazione utente (generato al salvataggio)
```

---

## Colori nel pannello file

| Colore | Significato |
|---|---|
| 🟢 Verde | File caricato su Notion con successo |
| 🟡 Arancione/Giallo | Appunti generati, non ancora caricati su Notion |
| Bianco/Default | File non ancora elaborato |

---

## Note importanti

- I file `.id` nelle cartelle sono **file nascosti** (iniziano con `.`). Su Linux non sono visibili nei file manager standard — questo è il comportamento atteso, non un errore.NON DEVONO ESSERE MODIFICATI O CANCELLATI . Vengono utilizzati dall'applicazione per fare un' associazione [Cartella in locale]->[Cartella su Notion]
- Se dopo "Aggiorna" le cartelle non vengono create, controlla che `Data/dict_notion.json` sia stato generato. Se non esiste, c'è un problema con il token Notion o il `BASE_ID`.
- Il modello Gemini viene scelto automaticamente in ordine di priorità dalla lista in Impostazioni → Modelli AI. In caso di rate limit (errore 429), il sistema scala automaticamente al modello successivo.

# Progetto Genera Appunti

- [x]  Implementare un visualizzatore pdf interno
- [ ]  Gestione di finestre funzioni specializzate → una per il file system e selezione e generazione di materiale , una per la visualizzazione dei pdf internamente all’applicazione, e anche quella per la generazione di mappe concettuali
- [ ]  Implementare un sistema per la costruzione di maptrees
- [ ]  Modifica filemanager

### Implementazione visualizzazione pdf interno

> Molto probabilmente semplice non credo sia difficile nativamente pyqt6 permette di visualizzare i pdf all’interno del file system
> 
- E’ necessario strutturare un sistema che faccia le seguenti operazioni

**Comportamenti**

1. Shortcut o keybinds per capire quando l’utente vuole aprire un pdf
2. Analogamente a quello che succede su un browser si apre una seconda finestra che si occupa di visualizzazione del pdf 
3. Cose in più :
    1. Possibilità di zoomare ingrandire dimensionare
    2. Switchare tra le pagine del pdf

### Gestione di finestre

> E’ collegata con il processo di visualizzazione del pdf questa attività ha sicuramente la priorità
> 
- E’ necessario strutturare l’applicazione in modo che sia staccata
- E’ necessario creare una pagina “menu” deve essere semplice
- L’idea potrebbe anche quella di introdurre più opzioni nella barra superiore

| File | Visualizzazione | impostazioni |
| --- | --- | --- |
- **File :** deve dare la possibilità di :
    1.  aprire file manager , pdf , risposte come un’editor
    2. importare altri file
    3. rinominare il file corrente aperto

- **Visualizzazione :** l’idea è che potrebbe essere utile dare la possibilità di personalizzare il workflow dell’applicazione, introdurre la possibilità di dividere in più facciate lo schermo , più finestre
- **Impostazioni :**  Rimane uguale a prima da vedere cosa aggiungere potrebbe essere utile creare campi per modificare i tipi file accettati al fly vediamo cosa si può aggiungere

**Comporamenti**

1. Come in un browser l’utente può cambiare finestre cliccandoci sopra
2. Il filemanager e il sistema per la creazione degli appunti può essere chiuso  

### Implementare un sistema per la costruzione di maptrees

> L’idea è ispirata a come gemini crea le mappe mentali dovrebbe essere un json scritto quindi qualsiasi blocco o azione effettivamente modifica un certo file json utilizzato per visualizzare il contenuto
> 
- E’ necessario avere un visualizzatore grafico json → schema
- E’ un progetto a parte vorrei farlo in c++
- E’ necessario strutturare il sistema in modo che sia semplice , pochi colori , poche funzionalità essenziali per costruire mappe mentali
- E’ una funzionalità molto interessante si potrebbe implementare utilizzando gemini uno schema per permettergli di generare automaticamente le mappe sarà quindi necessario modificare prompt , schema dei blocchi che può scegliere , temperatura ,altri parametri

**Oggetti**

- Blocco base → può essere un blocco di testo normalissimo
    1. Sicuramente abbiamo bisogno di contenere dimensioni , posizione, colore bordi, contenuto, identificativo, per fare tutto più semplice possibile farei in modo che il visualizzatore non permetta la modifica del testo all’intenro dello schema 
    2. L’utente cliccando tasto destro su un blocco fa aprire un meno a tendina che contiene : 
        1. Modifica il contenuto → scrive dentro al blocco di testo 
        2. Toggle bordi saranno ellissi
        3. Elimina
    3. La connessione dei blocchi deve essere semplice quindi un unico tool per collegarli → keybinds, shortcut e pulsante
- Blocco riga → è una connessione tra due blocchi o tra riga blocco o riga riga
    1. Tool separato permette all’utente di creare una linea che colleghi due oggetti all’interno del creatore di schemi
    2. Bisogna vedere come vengono creati molto probabilmente basta una regola abbastanza semplice 3 punti il primo per dire dove collegarsi , il secondo per modificare la forma della riga (parobola ,spline ), il terzo invece per dire dove si attacca 
- Griglia → è la base del progetto vorrei che aiutasse gli utenti a rendere il più regolare possibile lo schema quindi bisogna implementare :
    - funzione per decidere quale è il punto più vicino a cui fare lo snap e connettere l’oggetto manipolato qualcosa che si può togglare

**Comportamenti**

> I comportamenti che devono essere previsti sono
> 
1. Creazione blocchi
2. Creazione riga
3. drag and connect oggetti all’intenro del sistema
4. menu a tendina per ogni oggetto per la riga la possibilità di aggiungere un punto per da cui far passare il collegamento
5. Toggle di snap ad oggetto

### Modifica del Filemanager

> Non deve essere più l’intero programma ma essere contenuto all’interno di un altra classe wrapper gestore dell’applicazione → necessario che corra su un thread separato anche lui
> 

**Da modificare :**

1. messaggi visualizzati vorrei che fossero simili a quelli che escono su vscode
2. possibilità di nascondere o mostrare i messaggi
3. possibilità di nascondere o mostrare l’anteprima
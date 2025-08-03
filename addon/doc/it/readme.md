# nvda-word-nav
L'add-on WordNav per NVDA migliora la navigazione integrata per parola, aggiungendo anche comandi di navigazione per parole con diverse definizioni di parola. Fornisce inoltre comandi per la selezione delle parole.

La maggior parte degli editor di testo supporta i comandi Control+FrecciaSinistra/Destra per la navigazione per parola. Tuttavia, la definizione di parola cambia da un programma all'altro. Questo è particolarmente vero per gli editor di testo moderni basati sul web, come Monaco. NVDA dovrebbe conoscere la definizione di parola nel programma usato per pronunciare correttamente le parole. Se NVDA non conosce la definizione esatta, alcune parole potrebbero essere saltate oppure pronunciate più volte. Inoltre, alcuni editor web-based posizionano il cursore alla fine della parola anziché all'inizio, rendendo l’editing più difficile per gli utenti ipovedenti. Per contrastare questo problema, ho creato comandi di navigazione per parola migliorati, che usano la definizione di parola di Notepad++ e non si basano sulla definizione del programma, ma analizzano le righe in parole direttamente da NVDA. Il comando Control+FrecciaSinistra/Destra non viene nemmeno inviato al programma, garantendo così coerenza nella lettura.

## Navigazione per parola e definizioni di parola

Attualmente WordNav supporta cinque definizioni di parola, assegnate a diverse combinazioni di tasti:

- `Ctrl sinistro+Freccia`: definizione di Notepad++, che considera come parole i caratteri alfanumerici e anche i segni di punteggiatura adiacenti come parole a sé stanti. Questa è la definizione di parola più comoda per la maggior parte degli utenti.
- `Ctrl destro+Freccia`: definizione fine che suddivide `camelCaseIdentifiers` e `underscore_separated_identifiers` in parti separate, permettendo di muovere il cursore all’interno di identificatori lunghi.
- `Ctrl sinistro+Windows+Freccia`: definizione ampia che tratta quasi tutti i simboli di punteggiatura adiacenti al testo come parte di una singola parola; ad esempio, tratterebbe percorsi come `C:\directory\subdirectory\file.txt` come un’unica parola.
- `Ctrl destro+Windows+Freccia`: definizione multi-parola, che raggruppa insieme più parole. Il numero di parole raggruppate è configurabile.
- Non assegnata: definizione di parola personalizzata tramite espressione regolare, che permette all’utente di definire i propri confini di parola.

Le combinazioni di tasti sono personalizzabili nel pannello impostazioni di WordNav.

## Selezione di parole

La selezione di parole è supportata a partire dalla versione 2.0 di WordNav. Basta aggiungere il modificatore `shift` a qualsiasi combinazione di navigazione per parola per selezionare le parole. Esiste anche una combinazione aggiuntiva per la selezione:

* `control+shift+numpad1` e `control+windows+shift+numpad1` selezionano la parola a destra, simile ai comandi con la freccia destra, ma includono anche gli spazi finali nella selezione.

Si prega di notare che le API di accessibilità attualmente in uso hanno diversi problemi riguardo la selezione delle parole. Ecco una lista di problemi noti e soluzioni temporanee:

* Le applicazioni UIA (es. Notepad, Visual Studio, Microsoft Word) non supportano il posizionamento del cursore all'inizio della selezione. In queste applicazioni la posizione del cursore è gestita da WordNav. Come effetto collaterale, i comandi di navigazione per parola potrebbero non funzionare bene insieme ai comandi di selezione di linea o paragrafo (`shift+freccia su/giù`, `ctrl+shift+freccia su/giù`) e i risultati potrebbero essere imprevedibili. Per comodità, i comandi di selezione carattere (`shift+freccia sinistra/destra`) sono stati aggiornati in WordNav per le applicazioni UIA e dovrebbero funzionare correttamente.
* I controlli di modifica Windows a singola riga non consentono di posizionare il cursore davanti alla selezione, quindi il problema precedente si applica anche a questi. Ciò riguarda tutte le caselle di testo a singola riga in NVDA.
* IAccessible2 non permette di impostare selezioni che coprono più paragrafi. Non esiste una soluzione nota per questo problema. Ciò interessa le caselle di modifica ricche multilinea in Chrome e Firefox, come l’area di composizione email in GMail e la finestra di composizione email in Thunderbird.
* In Notepad++ i messaggi di aggiornamento della selezione arrivano con ritardo. Come soluzione temporanea, WordNav annuncia la selezione lato NVDA per i comandi di selezione parola e ignora notifiche ritardate per 0.5 secondi. Di conseguenza, se si preme un comando di selezione parola seguito rapidamente da un altro comando (es. selezione carattere), si potrebbe perdere la notifica della seconda selezione se arriva entro 0.5 secondi dalla prima.
* Nelle caselle di testo multilinea che supportano l’interfaccia TOM, NVDA identifica erroneamente la posizione del cursore quando è presente una selezione. Questo è stato corretto in nvaccess/nvda#16455, che sarà incluso in NVDA v2024.2. Prima di quella versione, i comandi di selezione parola non funzioneranno correttamente nelle caselle TOM, come il visualizzatore log di NVDA.

## Note

- Se vuoi usare la funzionalità dei desktop virtuali di Windows 10, ricorda di disabilitare le scorciatoie Control+Windows+Freccia in WordNav (nel pannello impostazioni) o nelle gesture di input di NVDA.
- La compatibilità con VSCode richiede che sia installato l’add-on IndentNav v2.0 o superiore in NVDA. Inoltre, è necessario installare l’estensione per VSCode [Accessibility for NVDA IndentNav](https://marketplace.visualstudio.com/items?itemName=TonyMalykh.nvda-indent-nav-accessibility).

## Download

Si prega di installare l’ultima versione dallo store degli add-on di NVDA.

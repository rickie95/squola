## Why

Un orario generato va quasi sempre ritoccato a mano: un docente chiede di
spostare un'ora, una classe ha un'esigenza particolare. Oggi l'unica strada e'
rigenerare tutto, perdendo l'orario che andava bene, oppure correggere l'export
Excel fuori dall'applicazione senza alcun controllo sui vincoli. Serve uno
strumento che proponga solo cambi che l'orario puo' permettersi.

## What Changes

- **Nuova pagina "Cambi"** aperta a partire da un orario salvato. Mostra la
  griglia globale dell'export Excel (righe = docenti, colonne = giorni x ore,
  classi nelle celle). Selezionata una cella, la pagina elenca i cambi possibili
  per quella lezione.
- **Il cambio lavora su due slot.** Scelti la lezione (docente T, slot s1) e un
  secondo slot s2, ogni docente della catena coinvolta scambia la propria lezione
  di s1 con quella di s2. La catena e' determinata dall'orario: ne nascono scambi
  a due, a tre o piu' docenti. Il monte ore settimanale di ogni classe e materia
  resta invariato e ogni classe conserva esattamente i suoi slot occupati.
- **Solo candidati validi.** Sono scartati i cambi che scoprono un'ora di una
  classe, spostano una lezione fissa o violano un vincolo hard del generatore.
  I cambi che peggiorano un criterio soft (ore di buco oltre la franchigia,
  filate di 4 ore) restano proposti ma con un avviso, dopo quelli puliti.
- **Bozza lato pagina, copia solo al salvataggio.** I cambi si accumulano in una
  bozza con possibilita' di annullarli. L'orario di partenza non viene mai
  modificato: salvare crea un nuovo orario salvato.
- **Gli orari salvati portano anche gli id** di docente, classe, materia e
  assegnazione, oltre ai nomi. Gli orari salvati in precedenza vengono
  ricollegati per nome ai dati attuali; se il ricollegamento fallisce la pagina
  lo segnala e non consente cambi.

## Capabilities

### New Capabilities
- `schedule-swaps`: modifica manuale di un orario salvato tramite cambi a catena
  su due slot, con suggerimenti validati sui vincoli e salvataggio come nuovo
  orario.

### Modified Capabilities
<!-- Nessuna: il formato di salvataggio si estende in modo compatibile. -->

## Impact

- `src/squola/routers/scheduling.py`: endpoint per i suggerimenti di cambio e
  per salvare un orario modificato.
- Nuovo modulo backend per la ricerca e la validazione delle catene; riusa le
  regole e le costanti di `src/squola/scheduler.py` (tetto giornaliero, fasce
  0/2-5 ore, requisiti delle materie) senza passare dal solver.
- `src/squola/scheduler.py`: gli slot salvati includono gli id.
- `frontend/src/pages/`: nuova pagina con griglia globale e bozza; ingresso da
  `SchedulingPage.tsx`, rotta in `App.tsx`.
- Nessuna migrazione: `schedule_data` e' JSON e i nuovi campi sono aggiuntivi.

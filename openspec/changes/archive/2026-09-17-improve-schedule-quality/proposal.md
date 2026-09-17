## Why

Gli insegnanti hanno segnalato che gli orari generati sono legali ma di bassa
qualita': avvicendamenti ripetuti fra classi nella stessa mattina (`3C 2C 3C 2C`),
ore della stessa classe spezzate da un buco (`3B - - 3B`), lezioni della stessa
materia ripetute nella stessa giornata dopo un'interruzione, e giornate
sbilanciate rispetto al monte ore settimanale.

La causa e' nel modello: la funzione obiettivo del solver non contiene alcun
termine che descriva la *forma* della giornata di un docente. `MINIMIZE_GAPS` ha
coefficiente `hour - 1`, cioe' e' `EARLY` traslato, e nel modello non esiste
nessuna variabile che rappresenti un buco. Un docente con preferenza `NONE` (il
default) non contribuisce con alcun termine: quando tutti i docenti sono `NONE` e
nessuno chiede il giorno libero, `objective_terms` e' vuoto e CP-SAT restituisce
la prima soluzione ammissibile che incontra. "Legale ma non interessante" e' il
comportamento nominale del codice attuale, non un caso limite.

## What Changes

- **Nuovo vincolo hard**: ogni `ClassMatterAssignment` puo' occupare al massimo
  3 ore in una singola giornata. **BREAKING**: sostituisce
  `_add_at_most_three_hours_per_single_lesson_constraint`, che vincolava solo le
  finestre di 4 ore consecutive e lasciava passare `3 + buco + 1`. Il nuovo tetto
  e' strettamente piu' forte e puo' rendere infeasible una configurazione che
  oggi genera.
- **Nuovi termini soft** nella funzione obiettivo, attivi per ogni docente
  indipendentemente dalla sua `SchedulePreference`:
  - inizi di blocco-classe per (docente, classe, giorno) — penalizza sia
    l'avvicendamento fra classi sia la stessa classe ripresa dopo un'interruzione;
  - ore di buco, con penalita' fortemente crescente oltre la prima ora;
  - finestre di 4 ore consecutive di lezione, per rendere possibile lo stacco
    nelle giornate da 4 e 5 ore;
  - scostamento del carico giornaliero da una banda calcolata sul monte ore.
- **Riscalatura di `EARLY` e `LATE`**. Oggi un docente con 20 ore e preferenza
  oraria contribuisce fino a `20 x 6 = 120`, un ordine di grandezza sopra ai nuovi
  termini: senza riscalatura i docenti con preferenza oraria riceverebbero
  sistematicamente gli orari peggiori sulle nuove dimensioni.
- **`MINIMIZE_GAPS` e `MAXIMIZE_GAPS` diventano modulatori** dei pesi sui termini
  di buco e contiguita' (rispettivamente amplificazione e attenuazione), non piu'
  formulazioni autonome. L'enum `SchedulePreference` resta invariato: nessuna
  migrazione, nessun dato utente perso.
- **Rimozione del termine lessicografico sul giorno libero flessibile**. Il giorno
  libero resta garantito dal vincolo hard `sum(works_on_day) <= 4`; la
  distribuzione sui giorni residui passa alla banda di bilanciamento. Il peso
  `preference_upper_bound + 1` dovrebbe altrimenti dominare sei termini invece di
  uno, degradando il rilassamento LP.
- **Diagnostica di qualita'** nella risposta di generazione: totali per dimensione
  e peggiori (docente, giorno), per rendere misurabile un difetto oggi
  verificabile solo leggendo le griglie a mano.

## Capabilities

### New Capabilities
- `teacher-day-shape`: come sono disposte le ore di un docente dentro una giornata
  — contiguita' delle ore della stessa classe, buchi, lunghezza delle filate di
  lezione consecutive.
- `matter-daily-limits`: quante ore della stessa assegnazione materia-classe
  possono ricadere in una singola giornata.
- `schedule-quality-metrics`: la diagnostica di qualita' esposta dalla generazione.

### Modified Capabilities
- `teacher-workweek-distribution`: il carico giornaliero non e' piu' solo
  confinato nell'intervallo legale 2-5, ma tende a una banda derivata dal monte
  ore settimanale e dai giorni lavorabili.
- `teacher-flexible-day-off`: il requisito di precedenza del giorno libero sulle
  altre preferenze viene rimosso; il giorno libero resta un vincolo hard, mentre la
  massimizzazione dei giorni di lezione passa da garanzia lessicografica a
  preferenza forte.

## Impact

- `src/squola/scheduler.py`: `ScheduleGenerator._add_preference_objectives` e i due
  metodi gaps riscritti; `_add_at_most_three_hours_per_single_lesson_constraint`
  rimosso e sostituito; nuove variabili ausiliarie (stima ~5.000 su ~3.000
  esistenti per 20 docenti / 15 classi / 100 assegnazioni); `GeneratedSchedule`
  estesa con le metriche.
- `src/squola/routers/scheduling.py`: le metriche nella risposta di generazione.
- Prestazioni: la generazione passa da problema di soddisfacibilita' a problema di
  ottimizzazione reale. `OPTIMAL` diventera' raro e `FEASIBLE` la norma entro il
  limite di tempo — da comunicare in UI, altrimenti si legge come un peggioramento.
- `tests/`: i test esistenti passano `time_limit_seconds: 3`, budget che con un
  obiettivo denso puo' produrre esiti instabili.
- Documentazione: `docs/vincoli.md` e `specs/07 - generation.md`.
- Nessuna migrazione Alembic: le metriche non vengono persistite (registrato in
  `TODO.md`).

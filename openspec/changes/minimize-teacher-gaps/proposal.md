## Why

I criteri sui buchi oggi nel modello sono stati scritti come uno dei tanti
termini di forma della giornata, non come una regola a se'. Gli insegnanti li
vivono invece in modo molto piu' netto: un'ora di buco in una giornata lunga e'
uno stacco desiderato, due ore di buco o due buchi separati nello stesso giorno
sono inaccettabili, e chi ha poche ore non dovrebbe averne affatto.

La taratura attuale non regge questa lettura. `W_EXTRA_GAP = 12` sta sotto al
costo di due inizi di blocco-classe (20) e sotto a `W_DAILY_BALANCE` (16): il
solver compra volentieri un secondo buco per raddrizzare un avvicendamento.
Nessun termine scala con il monte ore, quindi un docente da 8 ore settimanali
riceve lo stesso trattamento di un full time. Gli slot di indisponibilita'
vengono conteggiati come buchi anche se in quelle ore il docente non e' a
scuola. E `MINIMIZE_GAPS` / `MAXIMIZE_GAPS` agiscono dentro la singola giornata,
mentre la richiesta reale e' settimanale: "uno stacco al giorno tutti i giorni",
non "tanti buchi in un giorno".

## What Changes

- **Gli slot di indisponibilita' smettono di essere buchi.** Un'ora in cui il
  docente non puo' lavorare non e' un'attesa: non genera penalita' e non spezza
  la giornata. `ScheduleGenerator.unavailable` e' gia' disponibile nel modello.
- **La franchigia di un'ora di buco diventa condizionata alla lunghezza della
  giornata.** Oggi ogni giornata ha diritto alla prima ora di buco a prezzo
  ridotto; diventa un diritto delle sole giornate da almeno `LONG_RUN_WINDOW`
  ore. Il buco serve a spezzare le giornate lunghe, quindi se lo guadagna la
  giornata lunga. La proporzionalita' al monte ore chiesta dagli insegnanti
  emerge da qui senza una seconda manopola: chi ha poche ore ha giornate corte,
  chi ha giornate corte non matura la franchigia.
- **Il superamento della franchigia diventa dominante.** Il peso sulle ore di
  buco eccedenti deve superare quanto l'insieme degli altri termini puo' muovere
  in una giornata, altrimenti "da evitare a tutti i costi" resta una frase.
  **BREAKING**: orari oggi generati con due ore di buco in una giornata
  verranno generati diversamente, con perdite possibili su contiguita' e
  bilanciamento.
- **`MINIMIZE_GAPS` e `MAXIMIZE_GAPS` passano dal giorno alla settimana.**
  Smettono di modulare i pesi di forma della giornata e diventano un termine
  proprio sul numero di giornate che usano il loro stacco. `MAXIMIZE_GAPS`
  esprime "uno stacco su ogni giornata lunga", non "piu' buchi in una giornata":
  quest'ultima lettura e' comunque vietata dalla regola assoluta.
  **BREAKING**: il segno sulla prima ora di buco si inverte per
  `MAXIMIZE_GAPS`, che oggi la penalizza solo piu' debolmente.
- **La modulazione sulla contiguita' delle classi viene rimossa.** Le preferenze
  sui buchi non dicono nulla su come le ore di una stessa classe si raggruppano;
  `W_CLASS_BLOCK` torna uniforme e `_shape_weight` sparisce.
- **L'invariante fra stacco e filata lunga viene verificata sul peso effettivo.**
  L'assert `W_LONG_RUN > W_GAP + 2 * W_TIME_PREFERENCE` confronta oggi il peso
  base con una soglia, ma il modello applica il peso modulato: per un docente
  `MINIMIZE_GAPS` con preferenza oraria vale `6 > 4 + 2`, falso, e lo stacco
  nella giornata da quattro ore non viene mai comprato. L'assert passa
  dichiarando una garanzia che il modello non offre.
- **La diagnostica separa il difetto dalla scelta.** `gap_hours` e' una somma
  piatta che non distingue dieci docenti con un buono stacco da cinque docenti
  con due ore di buco. Si scompone in ore eccedenti la franchigia (difetto),
  giornate che usano lo stacco (neutro) e giornate lunghe senza stacco (difetto
  solo per `MAXIMIZE_GAPS`).

## Capabilities

### New Capabilities
<!-- Nessuna: tutto ricade in capability gia' definite. -->

### Modified Capabilities
- `teacher-day-shape`: la definizione di buco esclude gli slot di
  indisponibilita'; la franchigia di un'ora e' condizionata alla lunghezza della
  giornata; il superamento della franchigia diventa invalicabile in pratica; le
  preferenze sui buchi cambiano dominio dalla giornata alla settimana e non
  modulano piu' la contiguita' delle classi.
- `schedule-quality-metrics`: la dimensione sui buchi si scompone in tre
  grandezze distinte e solo quelle che indicano un difetto entrano nella
  classifica dei peggiori.

## Impact

- **Ordine di lavorazione**: entrambe le capability modificate esistono oggi
  solo come delta dentro il change `improve-schedule-quality` (28/28 task
  completi, non archiviato). `openspec/specs/` non le contiene ancora. Questo
  change va sincronizzato **dopo** l'archiviazione di `improve-schedule-quality`,
  altrimenti i suoi `MODIFIED` non trovano il requisito da modificare.
- `src/squola/scheduler.py`: `_add_gap_terms` riscritto (esclusione degli slot
  indisponibili, bool di franchigia per coppia docente-giorno, termine
  settimanale sulle preferenze); `_add_class_block_terms` demodulato;
  `_shape_weight` rimosso; costanti di peso ritarate; assert riformulato.
- `compute_quality_metrics`: firma estesa con la mappa delle indisponibilita' -
  i buchi non sono ricostruibili dai soli slot, per lo stesso motivo per cui
  `eligible_workdays` gli viene gia' passato a mano. `QUALITY_DIMENSIONS`
  aggiornato.
- `src/squola/routers/scheduling.py`: le nuove dimensioni nella risposta di
  generazione.
- Prestazioni: una bool in piu' per coppia docente-giorno, trascurabile rispetto
  alle variabili gia' presenti. Il peso dominante irrigidisce il rilassamento LP
  su una dimensione sola, quindi l'effetto netto sul tempo di soluzione va
  misurato, non assunto.
- `tests/test_teacher_day_shape.py` e `tests/test_schedule_quality_metrics.py`:
  i test che oggi fissano la curva di costo dei buchi vanno riscritti.
- Documentazione: `docs/vincoli.md` (tabella dei pesi, tabella delle preferenze,
  sezione diagnostica).
- Nessuna migrazione: `SchedulePreference` resta invariato come enum, cambia
  solo cosa il solver ne fa. Le metriche non sono persistite.

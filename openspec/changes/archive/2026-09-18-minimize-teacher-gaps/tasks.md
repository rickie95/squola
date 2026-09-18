## 1. Definizione di buco

- [x] 1.1 In `_add_gap_terms` (`src/squola/scheduler.py:843`) non creare la `gap` var per gli slot presenti in `self.unavailable` (popolato in `__init__`, `scheduler.py:491`), lasciando invariate le catene `before` / `after`. Verificare con due test in `tests/test_teacher_day_shape.py`: una lezione prima e una dopo uno slot indisponibile non produce buchi; uno slot libero accanto a uno slot indisponibile fra due lezioni produce un buco solo.

## 2. Franchigia e peso dominante

- [x] 2.1 Aggiungere in `_add_gap_terms` una bool `allowance[teacher, day]` reificata su `sum(occupied) >= LONG_RUN_WINDOW` e sostituire `extra >= sum(day_gaps) - 1` con `extra >= sum(day_gaps) - allowance[day]`. Verificare che una giornata da 4 ore ammetta l'ora di stacco senza penalita' di eccedenza e che una giornata da 3 ore venga generata contigua.
- [x] 2.2 Sostituire `W_EXTRA_GAP` con `W_EXCESS_GAP`, scritto come espressione derivata dagli altri pesi secondo la formula in `design.md` - Decisions 3, non come letterale. Verificare con un'asserzione di modulo che `W_EXCESS_GAP` superi la somma settimanale massima di tutti gli altri termini, cosi' che la costante non possa scollarsi se un altro peso cambia.
- [x] 2.3 Rimuovere `W_GAP` come costo della prima ora di buco: la prima ora e' regolata dalla franchigia e dal termine sulle preferenze, non da un peso proprio. Verificare che `tests/test_teacher_day_shape.py` non importi piu' `W_GAP` e che la suite compili.
- [x] 2.4 Aggiungere in `tests/test_teacher_day_shape.py` i casi della franchigia: un docente con monte ore che produce solo giornate corte riceve una settimana priva di buchi; nessuna giornata supera mai un'ora di buco; una disposizione con due ore di buco non viene generata nemmeno quando migliorerebbe contiguita' o bilanciamento. Asserire proprieta' dell'orario, non disposizioni esatte.

## 3. Preferenze settimanali

- [x] 3.1 Rimuovere `_shape_weight` (`src/squola/scheduler.py:760`) e `SHAPE_SENSITIVITY_PERCENT`, e usare `W_CLASS_BLOCK` non modulato in `_add_class_block_terms`. Verificare con un test che due docenti con lo stesso carico e preferenze sui buchi diverse ricevano la stessa intensita' di criterio sulla contiguita' delle classi.
- [x] 3.2 Aggiungere una bool `break_day[teacher, day]` ("questa giornata usa la sua franchigia") e il termine per preferenza descritto in `design.md` - Decisions 4: `NONE` e `MINIMIZE_GAPS` penalizzano `break_day` con pesi diversi, `MAXIMIZE_GAPS` penalizza `allowance AND NOT break_day`. Verificare che per `MAXIMIZE_GAPS` lo stacco compaia su piu' giornate lunghe anziche' concentrarsi, e che `MINIMIZE_GAPS` riduca il numero di giornate con stacco rispetto a `NONE`.
- [x] 3.3 Verificare con un test che nessuna preferenza superi la franchigia: un docente `MAXIMIZE_GAPS` non riceve alcuna giornata con due ore di buco ne' alcun buco in una giornata corta.
- [x] 3.4 Riformulare l'assert `W_LONG_RUN > W_GAP + 2 * W_TIME_PREFERENCE` (`scheduler.py:46`) sulle costanti nuove, in modo che verifichi la relazione effettivamente applicata dal modello e non un peso base poi modulato. Verificare con un test che un docente `MINIMIZE_GAPS` con preferenza oraria ottenga comunque lo stacco nella giornata da quattro ore - il caso che oggi fallisce silenziosamente.

## 4. Diagnostica

- [x] 4.1 Estendere `compute_quality_metrics` (`src/squola/scheduler.py:308`) con un argomento per le indisponibilita', sulla falsariga di `eligible_workdays`, e aggiornare ogni call site. Verificare che la metrica non conti come buco uno slot indisponibile fra due lezioni.
- [x] 4.2 Scomporre la dimensione `gap_hours` in `excess_gap_hours`, `break_days` e `missed_break_days`, aggiornando `QUALITY_DIMENSIONS` (`scheduler.py:305`) con la sola `excess_gap_hours` fra le dimensioni che alimentano la classifica `worst`. Verificare in `tests/test_schedule_quality_metrics.py` che una giornata lunga con il solo stacco previsto non compaia fra le peggiori e che una giornata oltre la franchigia vi compaia con il numero di ore eccedenti.
- [x] 4.3 Riportare le tre grandezze nella risposta di `POST /api/scheduling/generate` (`src/squola/routers/scheduling.py`). Verificare con un test API che i tre valori siano presenti e distinti in una generazione riuscita.
- [x] 4.4 Sostituire `gap_hours` con le nuove grandezze in `ScheduleQuality` (`frontend/src/types/index.ts`) e nella riga di qualita' di `frontend/src/pages/SchedulingPage.tsx`, che altrimenti mostrerebbe `undefined ore di buco`. Verificare con `npx tsc --noEmit` e `npm run build`.

## 5. Verifica d'insieme

- [x] 5.1 Eseguire `uv run --extra dev pytest tests/` e verificare che l'intera suite passi, riscrivendo su proprieta' i test che asserivano la vecchia curva di costo dei buchi.
- [x] 5.2 Misurare il tempo di generazione su un carico realistico prima e dopo il change, e verificare che il peso dominante non lo peggiori in modo inaccettabile. Se lo fa, registrarlo prima di procedere anziche' assumere il contrario (`design.md` - Risks).

## 6. Documentazione

- [x] 6.1 Aggiornare `docs/vincoli.md`: tabella dei pesi (`W_GAP` e `W_EXTRA_GAP` sostituiti, franchigia condizionata), tabella delle preferenze (`MINIMIZE_GAPS` / `MAXIMIZE_GAPS` non sono piu' modulatori), sezione diagnostica con le tre grandezze sui buchi. Verificare che non resti alcun riferimento a `_shape_weight` o alla modulazione della contiguita'.
- [x] 6.2 Aggiornare `specs/05 - constraints.md` e `specs/07 - generation.md` con la regola "al massimo un'ora di buco al giorno, e solo nelle giornate lunghe". Verificare che si leggano coerentemente con i delta spec di questo change.

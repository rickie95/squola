## 1. Id negli orari salvati

- [x] 1.1 In `GeneratedSchedule._group_by_class/_by_teacher/_by_day` (`src/squola/scheduler.py:245-296`) aggiungere a ogni voce `teacher_id`, `class_id`, `matter_id`, `assignment_id`. Verificare con un test in `tests/test_schedule_swaps.py` che un orario generato e salvato contenga gli id in `schedule_data`, e che la suite esistente resti verde.
- [x] 1.2 Aggiungere in `src/squola/swaps.py` il caricamento di un orario salvato in lezioni `(teacher_id, class_id, matter_id, assignment_id, day, hour)`: con gli id li usa, senza id ricollega per `(nome docente, nome classe, nome materia)` ai dati attuali e riporta le lezioni con zero o piu' corrispondenze. Verificare con test: orario con id, orario vecchio ricollegabile, orario vecchio con docente rinominato, assegnazione cancellata. (Gli omonimi non possono collidere: `uq_class_matter` rende unica la chiave docente-classe-materia.)

## 2. Regole condivise col generatore

- [x] 2.1 Estrarre a livello di modulo in `scheduler.py` le regole oggi solo inline nel modello CP-SAT (dominio giornaliero `{2,3,4,5}` a `scheduler.py:682`, calcolo del giorno libero flessibile, giorni totalmente indisponibili per docente) e usarle dal generatore. Verificare che `uv run pytest tests/` passi invariato.

## 3. Catena e validazione

- [x] 3.1 Implementare in `swaps.py` la catena di `(T, s1, s2)` come componente del grafo docenti-classi sui due slot, con lo scarto delle catene contenenti una classe di grado 1 o una lezione fissa, e dei cambi senza effetto. Verificare con test: scambio semplice, ciclo a tre docenti (scenario della spec), classe presente in un solo slot, lezione fissa, docente con due materie nella stessa classe.
- [x] 3.2 Implementare il conteggio delle violazioni hard per `(vincolo, entita', giorno)` su un orario concreto, ristretto a docenti e assegnazioni della catena e ai giorni di s1 e s2: sovrapposizione docente, indisponibilita', ore giornaliere 0 o 2-5, giorno libero flessibile, tetto giornaliero dell'assegnazione, `at_least_twice_per_week`, blocchi da 2h e 3h. Il cambio e' scartato se un conteggio cresce. Verificare con un test per vincolo, piu' il caso "violazione gia' presente e non peggiorata" che non scarta.
- [x] 3.3 Implementare gli avvisi confrontando per docente-giorno prima e dopo `excess_gap_hours` e `long_runs`, riusando le grandezze di `compute_quality_metrics`. Verificare con un test che un cambio che apre un secondo buco produca l'avviso con docente, giorno e criterio.
- [x] 3.4 Implementare `suggest(orario, applied, T, s1)`: riapplica `applied` rivalidandoli, prova ogni s2 != s1, ordina senza avvisi prima e poi per numero di docenti. Verificare con un test sull'ordinamento e con un test che un `applied` non valido sia rifiutato indicandone la posizione.
- [x] 3.5 Test di coerenza col generatore: per gli orari prodotti dai test esistenti del generatore, il conteggio delle violazioni hard di `swaps.py` e' zero. Verificare che il test fallisca se si abbassa a mano il tetto giornaliero nel solo validatore.

## 4. API

- [x] 4.1 Aggiungere `POST /api/scheduling/schedules/{id}/swaps/draft` (lezioni della bozza) e `POST /api/scheduling/schedules/{id}/swaps/suggest` in `src/squola/routers/scheduling.py` con schemi Pydantic in `schemas.py`; 404 per orario di altro workspace, 409 con elenco delle lezioni non ricollegate, 422 per `applied` non valido. Verificare con test httpx, incluso l'isolamento fra workspace.
- [x] 4.2 Aggiungere `POST /api/scheduling/schedules/{id}/swaps/save`: riapplica e rivalida, crea un nuovo `SavedSchedule` con `status = "MANUAL"`, `solve_time_seconds = 0`, nickname di default `"<origine> (cambi)"`, `schedule_data` con id; rifiuta `applied` vuoto. Verificare con test che l'origine resti identica e che il nuovo orario abbia monte ore per classe-materia uguale all'origine.

## 5. Frontend

- [x] 5.1 Estrarre da `frontend/src/utils/globalTeacherTimetableExcel.ts` la conversione slot -> righe docente x (giorno, ora) in una funzione condivisa, usata dall'export. Verificare che l'export Excel produca lo stesso file di prima e che `npm run build` passi.
- [x] 5.2 Aggiungere tipi e chiamate API per suggest/save in `frontend/src/types` e `frontend/src/api/index.ts`. Verificare con `npm run build`.
- [x] 5.3 Creare la pagina `SwapsPage` sulla rotta `/scheduling/:id/swaps`: griglia globale con colori classe, selezione cella, lista suggerimenti con docenti prima/dopo e avvisi, evidenziazione nella griglia al passaggio su un suggerimento, applica, annulla ultimo, salva con nickname. Mostrare l'errore 409 elencando le lezioni non ricollegate. Verificare a mano con `uv run squola` + `npm run dev` il percorso completo: applica due cambi, annulla uno, salva, il nuovo orario compare nella lista e l'origine e' invariata.
- [x] 5.4 Aggiungere in `SchedulingPage.tsx` il bottone "Cambi" sull'orario salvato che porta alla nuova pagina. Verificare la navigazione a mano.

## 6. Documentazione

- [x] 6.1 Creare `docs/cambi.md` con il modello a catena su due slot, il criterio "introduce una violazione", gli avvisi e il formato degli endpoint. Verificare che i riferimenti a file e funzioni corrispondano al codice.

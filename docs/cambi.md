# Cambi manuali sull'orario

Pagina `/scheduling/:id/swaps` (`frontend/src/pages/SwapsPage.tsx`), raggiunta dal
bottone "Cambi" nella lista degli orari salvati. Logica in `src/squola/swaps.py`,
endpoint in `src/squola/routers/scheduling.py`. Requisiti:
`openspec/changes/add-schedule-swaps/specs/schedule-swaps/spec.md`.

## Il modello: catena su due slot

Un cambio e' `(docente T, slot s1, slot s2)`. La catena e' la componente di T nel
grafo bipartito docenti-classi costruito sulle sole lezioni di s1 e s2
(`find_chain`). Ogni nodo ha grado al piu' 2, quindi la componente e' un cammino
o un ciclo; il cambio porta ogni sua lezione nell'altro slot (`apply_chain`).

```
  s1:  GV-1B   RM-3A   MG-2C          s1:  GV-2C   RM-1B   MG-3A
  s2:  GV-2C   RM-1B   MG-3A   -->    s2:  GV-1B   RM-3A   MG-2C
```

Ogni lezione tiene docente, classe e materia: il monte ore settimanale non cambia
per costruzione. La catena non si sceglie, la determina l'orario: per una cella
ci sono al massimo 29 candidati (uno per s2).

Scartati subito da `find_chain`:
- una classe della catena ha lezione in un solo dei due slot (resterebbe scoperta);
- la catena contiene una `FixedClassLesson`;
- il cambio non modifica nulla (stesse assegnazioni nei due slot per ogni classe).

## Vincoli hard: "introduce una violazione"

`count_violations` conta le violazioni per `(vincolo, entita', giorno)` sui docenti
della catena e le loro assegnazioni: sovrapposizione, indisponibilita', ore
giornaliere (`WORKDAY_TEACHING_HOURS`, 0 ammesso solo con giorno libero
flessibile), giorno libero flessibile, tetto giornaliero (`resolve_daily_cap`),
`at_least_twice_per_week`, blocchi da 2h/3h. `check_swap` scarta il cambio se un
conteggio cresce rispetto a prima: un orario che viola gia' qualcosa (dati cambiati
dopo la generazione) resta modificabile, ma nessun cambio puo' peggiorarlo.

Le regole vengono da `scheduler.py` (`WORKDAY_TEACHING_HOURS`,
`uses_flexible_day_off`, `fully_unavailable_days`, `resolve_daily_cap`,
`LESSON_LENGTH_HOURS`), le stesse usate dal modello CP-SAT.
`test_generated_timetables_have_no_violations` verifica che gli orari del
generatore risultino privi di violazioni per il validatore: se una regola cambia
da una parte sola, il test fallisce.

## Avvisi

I criteri soft non scartano: `check_swap` confronta per docente-giorno
`excess_gap_hours` e `long_runs` (da `compute_quality_metrics`) prima e dopo e
segnala ogni peggioramento. `suggest` ordina: prima senza avvisi, poi per numero
di docenti nella catena.

## Collegamento ai dati

Gli orari salvati contengono, oltre ai nomi, `teacher_id`, `class_id`,
`matter_id`, `assignment_id` (`ScheduleSlot.ids`). `load_lessons` usa
`assignment_id` se presente, altrimenti la chiave (docente, classe, materia) per
nome, unica grazie a `uq_class_matter`. Una lezione senza corrispondenza rende
l'orario non modificabile (409).

## Endpoint

Senza stato: il client invia l'id dell'orario di partenza e la lista dei cambi
applicati; il server li riapplica e rivalida (`replay`) a ogni richiesta.

| Endpoint | Corpo | Risposta |
|---|---|---|
| `POST /api/scheduling/schedules/{id}/swaps/draft` | `{applied}` | `{lessons: [...]}` della bozza |
| `POST /api/scheduling/schedules/{id}/swaps/suggest` | `{applied, teacher_id, slot}` | candidati `{s2, teachers, warnings}` |
| `POST /api/scheduling/schedules/{id}/swaps/save` | `{applied, nickname}` | nuovo orario salvato (`status = "MANUAL"`) |

`applied` e' una lista di `{teacher_id, s1: {day, hour}, s2: {day, hour}}`, con
`day` 0-4 e `hour` 1-6. Errori: 404 orario di un altro workspace, 409 con
`detail.unlinked` per lezioni non ricollegate, 422 per un cambio non piu' valido
(`"swap N: ..."`) o per un salvataggio senza cambi. L'orario di partenza non
viene mai modificato.

## Context

Vedi `proposal.md` - Why. Tre fatti del codice attuale orientano il design.

`SavedSchedule.schedule_data` contiene solo `by_class` / `by_teacher` / `by_day`
con **nomi** (docente, classe, materia) ed etichette di giorno e ora. Gli id che
`ScheduleSlot` ha in memoria (`scheduler.py:202`) si perdono al salvataggio.

I vincoli hard vivono solo come vincoli CP-SAT in `ScheduleGenerator`
(`scheduler.py:590-800`). Non esiste un controllo "questo orario concreto e'
valido?"; le metriche soft invece si calcolano gia' da slot concreti
(`compute_quality_metrics`, `scheduler.py:336`).

La griglia globale docenti x giorni esiste solo come export Excel
(`frontend/src/utils/globalTeacherTimetableExcel.ts`).

## Goals / Non-Goals

**Goals:**
- Suggerimenti in tempo interattivo (sotto il secondo) per una cella.
- Un solo punto di verita' per le regole: la validazione dei cambi e il generatore
  non devono divergere su tetto giornaliero, fasce orarie, requisiti.

**Non-Goals:**
- Sostituzioni puntuali per una data (cambio a slot singolo).
- Spostare una lezione in uno slot libero della classe: la forma dell'orario di
  ogni classe e' fissa.
- Cambi fra piu' di due slot in una mossa: si ottengono componendo piu' cambi.
- Persistenza della bozza fra sessioni.

## Decisions

### La catena e' una componente del grafo docenti-classi su due slot

Presi s1 e s2, il grafo bipartito ha un nodo per docente e per classe e un arco
per ogni lezione in s1 o s2. Ogni nodo ha grado al piu' 2 (una lezione per slot),
quindi ogni componente e' un cammino o un ciclo. La catena di (T, s1, s2) e' la
componente di T; il cambio inverte lo slot di ogni suo arco.

```
  s1:  GV-1B   RM-3A   MG-2C
  s2:  GV-2C   RM-1B   MG-3A

  GV --s1-- 1B --s2-- RM --s1-- 3A --s2-- MG --s1-- 2C --s2-- GV   (ciclo)
```

Una classe con grado 1 nella componente perderebbe la lezione in uno slot:
scarto immediato. Un docente con grado 1 e' ammesso (passa in uno slot in cui era
libero), poi lo giudicano i vincoli. Per una cella ci sono quindi al massimo 29
candidati, uno per s2, ciascuno trovato in tempo lineare: niente solver, niente
ricerca combinatoria.

Alternativa scartata: enumerare permutazioni di docenti fino a una lunghezza K.
Esplode, e produce solo casi che la componente gia' contiene o che violano la
copertura delle classi.

### Validazione su orario concreto, regole estratte dal generatore

Un nuovo modulo `src/squola/swaps.py` valuta l'orario dopo il cambio, limitandosi
ai docenti della catena, alle loro assegnazioni e ai giorni di s1 e s2. Le regole
che oggi sono solo costanti e helper del generatore (`MAX_DAILY_ASSIGNMENT_HOURS`,
`resolve_daily_cap`, le fasce `[2,3,4,5]`, `fully_unavailable_days`, il giorno
libero flessibile, i blocchi da 2h/3h) vengono richiamate dal modulo, non
riscritte. Dove oggi una regola esiste solo inline nel modello CP-SAT (es. il
dominio `{2,3,4,5}`), la costante viene estratta a livello di modulo e usata da
entrambi.

Criterio "introduce una violazione": si conta ogni violazione per (vincolo,
entita', giorno) prima e dopo; il cambio e' scartato se un conteggio cresce. Gli
orari generati prima di una modifica dei dati (es. indisponibilita' aggiunta dopo)
restano cosi' modificabili senza sbloccare cambi che peggiorano la situazione.

Gli avvisi usano le stesse grandezze di `compute_quality_metrics`
(`excess_gap_hours`, `long_runs`) confrontate per docente-giorno prima e dopo.

Alternativa scartata: risolvere con CP-SAT fissando tutto tranne la catena.
Corretto per costruzione ma lento per 29 candidati per click, e porta dentro
anche i vincoli soft come ottimizzazione invece che come avviso.

### Backend senza stato: origine + lista di cambi

Gli endpoint ricevono l'id dell'orario di partenza e la sequenza di cambi gia'
applicati, ciascuno `(teacher_id, s1, s2)`:

```
POST /api/scheduling/schedules/{id}/swaps/draft
     { applied: [...] }
     -> { lessons: [ {day, hour, teacher, class, matter, ...id} ] }

POST /api/scheduling/schedules/{id}/swaps/suggest
     { applied: [ {teacher_id, s1, s2}, ... ], teacher_id, slot }
     -> [ { s2, teachers: [...prima/dopo...], warnings: [...] }, ... ]

POST /api/scheduling/schedules/{id}/swaps/save
     { applied: [...], nickname }
     -> SavedScheduleListResponse (nuovo orario)
```

Il server riapplica i cambi sull'origine e rivalida ognuno prima di suggerire o
salvare. Il frontend tiene solo la lista `applied`: annullare e' togliere
l'ultimo elemento. La griglia della bozza la restituisce il server (`draft`),
cosi' la logica del cambio vive in un posto solo e il client non la reimplementa.

Alternativa scartata: il client invia la griglia intera. Richiederebbe di
validare un orario arbitrario (monte ore, copertura, ogni vincolo) invece di una
sequenza di mosse che per costruzione preservano monte ore e copertura.

### Id negli slot salvati, ricollegamento per nome per i vecchi

`_group_by_*` aggiungono `teacher_id`, `class_id`, `matter_id`,
`assignment_id` a ogni voce. Per un orario senza id si costruisce la mappa
`(nome docente, nome classe, nome materia) -> assegnazione` dai dati attuali; una
chiave senza corrispondenza o con piu' corrispondenze marca la lezione come non
ricollegata e l'endpoint di suggerimento risponde 409 con l'elenco.

Il nuovo orario salvato ha `status = "MANUAL"`, `solve_time_seconds = 0`,
nickname di default `"<nome origine> (cambi)"` modificabile.

### Pagina frontend

Nuova rotta `/scheduling/:id/swaps`, raggiunta da un bottone sull'orario salvato
in `SchedulingPage.tsx`. La griglia riprende layout e colori classe dell'export
Excel; la conversione slot -> righe docente va estratta da
`globalTeacherTimetableExcel.ts` in una funzione condivisa invece di essere
duplicata. Al passaggio su un suggerimento le celle coinvolte si evidenziano
nella griglia con lo stato "dopo".

## Risks / Trade-offs

- [Regole duplicate fra CP-SAT e validatore divergono nel tempo] -> estrarre le
  costanti condivise e aggiungere un test che valida con il nuovo modulo ogni
  orario prodotto dal generatore nei test esistenti: deve risultare privo di
  violazioni.
- [Pochi candidati: la forma fissa delle classi e la catena forzata possono dare
  zero cambi validi per una cella] -> accettato; i cambi si compongono, e
  mostrare "nessun cambio possibile" e' un'informazione corretta.
- [Catene lunghe poco pratiche da comunicare ai docenti] -> l'ordinamento le
  mette in fondo; un limite si aggiunge se serve.
- [Ricollegamento per nome ambiguo con omonimi] -> rifiuto esplicito invece di
  scegliere.

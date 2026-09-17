# Vincoli del dominio

I vincoli si dividono in due categorie:
- **Hard**: devono essere sempre soddisfatti, altrimenti l'orario non è valido
- **Soft**: preferenze ottimizzate dal solver, non obbligatorie

---

## Vincoli Hard

### Insegnanti
- Un insegnante non può essere in due classi nello stesso slot
- Gli slot in cui un insegnante è indisponibile devono essere esclusi dal planning (vincolo **indisponibilità**)
  - Le indisponibilità sono configurabili dalla scheda insegnante (`/teachers/:id`)
  - È possibile bloccare singoli slot o un intero giorno (shortcut UI che aggiunge tutti e 6 gli slot del giorno)
  - Modellate come record `TeacherUnavailability` (`day_of_week`, `hour_slot`) nella tabella `teacher_unavailabilities`
- Ogni giorno, il carico orario totale di un insegnante (somma di tutte le sue assegnazioni) deve essere **0, oppure tra 2 e 5 ore** (vincolo di legge sull'orario giornaliero). Un giorno da una sola ora, o da più di 5, rende l'orario non valido.

### Classi
- In una classe può esserci un solo insegnante per slot

### Materie
- Ogni materia deve essere insegnata esattamente per il numero di ore settimanali previste (`hours_per_week`)
- Una singola assegnazione materia-classe puo' occupare **al massimo 3 ore in un giorno** (`MAX_DAILY_ASSIGNMENT_HOURS`). Il tetto vale sul totale giornaliero, non sulle ore consecutive: `3 ore + buco + 1 ora` della stessa materia nello stesso giorno e' vietato quanto 4 ore di fila. Sostituisce il precedente vincolo sulle finestre di 4 ore consecutive, che lasciava passare il caso spezzato

### Requisiti delle materie (`MatterRequirements`)
Vincoli aggiuntivi opzionali assegnabili a una materia o a una singola assegnazione:

| Tag | Significato |
|---|---|
| `at_least_twice_per_week` | La materia deve comparire in almeno 2 giorni distinti |
| `one_lesson_of_two_hours_per_week` | Almeno una volta a settimana le ore devono essere consecutive (2h) |
| `one_lesson_of_three_hours_per_week` | Almeno una volta a settimana le ore devono essere consecutive (3h) |

> ⚠️ **Conflitto noto**: `at_least_twice_per_week` su un'assegnazione da 2 ore/settimana forza esattamente 1 ora in 2 giorni diversi. Se quell'insegnante non ha altre lezioni in uno di quei giorni per raggiungere il minimo legale di 2 ore, l'assegnazione è **impossibile da pianificare** in isolamento, e trascina in `INFEASIBLE` l'intera generazione (il modello CP-SAT è unico e condiviso da tutti gli insegnanti). `GET /api/scheduling/preview` rileva questo caso per singolo insegnante (indipendentemente dal resto della pianificazione) e lo segnala in `issues`; lo stesso controllo arricchisce il messaggio d'errore di `POST /api/scheduling/generate` quando la generazione fallisce per questo motivo.

---

## Vincoli Soft (funzione obiettivo)

Il solver minimizza **una sola somma pesata** di penalita'. Ogni termine vale per
ogni insegnante, indipendentemente dalla sua `SchedulePreference`: un insegnante
senza preferenza non contribuiva con alcun termine, e il solver restituiva
percio' il primo orario legale che incontrava.

| Termine | Cosa penalizza | Peso |
|---|---|---|
| `W_DAILY_BALANCE` | Scostamento del carico giornaliero dalla banda `[floor(T/D), ceil(T/D)]`, con `T` ore settimanali dell'insegnante e `D` giorni lavorabili | 16 |
| `W_EXTRA_GAP` | Ore di buco **oltre la prima** di una giornata | 12 |
| `W_CLASS_BLOCK` | Ogni inizio di un gruppo di ore consecutive in una stessa classe | 10 |
| `W_LONG_RUN` | Ogni finestra di 4 ore di lezione consecutive | 6 |
| `W_GAP` | Ogni ora di buco | 2 |
| `W_TIME_PREFERENCE` | Distanza dall'estremo di giornata preferito (`EARLY`/`LATE`) | 1 |

Costanti di modulo in `src/squola/scheduler.py`, da tarare sui dati reali.

Note sulla calibrazione:
- `W_LONG_RUN > W_GAP + 2 * W_TIME_PREFERENCE` e' verificato da un assert: senza,
  comprare l'ora di stacco in una giornata da 4 ore non conviene mai a un
  insegnante con preferenza oraria.
- La banda e' **derivata**, non fissata a "3/4 ore": per 18 ore su 5 giorni da'
  esattamente `[3,4]`, ma si adatta da sola a chi ha ore ridotte o insegna anche
  in un'altra scuola.
- Una filata da 5 ore contiene due finestre da 4 e costa quindi il doppio di una
  da 4: la gerarchia "3 ottime, 4 ok, 5 tante" non richiede un secondo termine.
- La prima ora di buco costa poco di proposito: in una giornata lunga lo stacco
  e' desiderato. Dalla seconda in poi costa molto.

### Preferenze dell'insegnante (`SchedulePreference`)

| Valore | Comportamento |
|---|---|
| `EARLY` | Preferisce le prime ore della mattina |
| `LATE` | Preferisce le ultime ore disponibili |
| `MINIMIZE_GAPS` | **Modulatore**: raddoppia i pesi su buchi e contiguita' per quell'insegnante |
| `MAXIMIZE_GAPS` | **Modulatore**: dimezza gli stessi pesi |
| `NONE` | Nessuna preferenza; i criteri sulla forma della giornata si applicano comunque |

`MINIMIZE_GAPS` e `MAXIMIZE_GAPS` attenuano o rafforzano, non invertono mai il
segno: chiedere al solver di frammentare una giornata contraddirebbe il resto del
modello. In precedenza `MINIMIZE_GAPS` aveva coefficiente `hour - 1`, cioe' era
`EARLY` traslato, e nessuna variabile del modello rappresentava un buco.

## Diagnostica di qualita'

`POST /api/scheduling/generate` riporta in `metadata.quality` un totale per
ciascuna dimensione (`class_blocks`, `gap_hours`, `long_runs`,
`balance_deviation`) e, sotto `worst`, le coppie insegnante-giorno che vi
contribuiscono di piu'. Serve a tarare i pesi senza rileggere le griglie a mano.
Le metriche **non** sono persistite con gli orari salvati.

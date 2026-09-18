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
| `W_EXCESS_GAP` | Ogni ora di buco **oltre la franchigia** della giornata | 986 |
| `W_DAILY_BALANCE` | Scostamento del carico giornaliero dalla banda `[floor(T/D), ceil(T/D)]`, con `T` ore settimanali dell'insegnante e `D` giorni lavorabili | 16 |
| `W_CLASS_BLOCK` | Ogni inizio di un gruppo di ore consecutive in una stessa classe | 10 |
| `W_BREAK_DAY_STRICT` | La giornata che usa la sua franchigia, per `MINIMIZE_GAPS` | 8 |
| `W_LONG_RUN` | Ogni finestra di 4 ore di lezione consecutive | 6 |
| `W_BREAK_DAY` | La giornata che usa la sua franchigia, per tutti gli altri | 1 |
| `W_TIME_PREFERENCE` | Distanza dall'estremo di giornata preferito (`EARLY`/`LATE`) | 1 |

Costanti di modulo in `src/squola/scheduler.py`, da tarare sui dati reali.

### La franchigia di un'ora

Una giornata da almeno 4 ore (`LONG_RUN_WINDOW`) ha diritto a **un'ora di buco**,
che non e' un difetto: serve a spezzare la giornata lunga. Una giornata piu' corta
non ha franchigia, e gia' il suo primo buco e' un'eccedenza.

Le tre regole chieste dagli insegnanti - un buco va bene, due ore di buco mai, due
buchi in un giorno mai - sono **la stessa grandezza**: un intervallo da due ore e
due intervalli da un'ora valgono entrambi due ore di buco. La regola e' quindi
"al massimo un'ora di buco al giorno" e basta una variabile per esprimerla.

Da qui viene anche la proporzionalita' fra monte ore e buchi, senza un criterio
separato: chi ha poche ore ha giornate corte, chi ha giornate corte non matura la
franchigia. Un insegnante da 8 ore settimanali ha giornate da 2 ore e finisce a
zero buchi, senza che il modello nomini mai le sue 8 ore.

Le ore in cui l'insegnante e' **indisponibile non sono buchi**: non e' a scuola e
non sta aspettando. Conta solo il tempo libero in cui avrebbe potuto insegnare.

Note sulla calibrazione:
- `W_EXCESS_GAP` e' **derivato** dagli altri pesi, non scelto a mano: e' il
  massimo che tutti gli altri termini insieme possono guadagnare in una settimana,
  piu' uno. Cosi' nessun altro criterio puo' mai comprare una seconda ora di buco,
  e la costante non si scolla se un altro peso cambia. Il fattore settimanale e non
  giornaliero e' necessario: spostare una lezione per aprire un buco nel giorno D
  cambia anche il giorno E.
- Nelle giornate che maturano la franchigia lo stacco elimina **sempre** almeno una
  filata lunga (4 ore senza buco in 6 slot sono per forza consecutive), quindi vale
  `W_LONG_RUN` in una giornata da 4 ore e il doppio in una da 5. I due pesi sullo
  stacco stanno ai due lati del guadagno minore, verificato da due assert:
  `W_LONG_RUN > W_BREAK_DAY + 2 * W_TIME_PREFERENCE` tiene lo stacco conveniente
  per tutti nella giornata da 4 ore, e
  `W_LONG_RUN < W_BREAK_DAY_STRICT + 2 * W_TIME_PREFERENCE < 2 * W_LONG_RUN`
  colloca `MINIMIZE_GAPS` nella banda in cui rinuncia allo stacco nella giornata da
  4 ore ma non in quella da 5.
- La banda e' **derivata**, non fissata a "3/4 ore": per 18 ore su 5 giorni da'
  esattamente `[3,4]`, ma si adatta da sola a chi ha ore ridotte o insegna anche
  in un'altra scuola.
- Una filata da 5 ore contiene due finestre da 4 e costa quindi il doppio di una
  da 4: la gerarchia "3 ottime, 4 ok, 5 tante" non richiede un secondo termine.
- Il peso dominante rallenta la convergenza del resto dell'obiettivo. Su 18
  docenti / 15 classi / 360 ore, a 30 secondi `class_blocks` e `long_runs` sono
  visibilmente peggiori che a 120; le ore eccedenti restano 0 in entrambi i casi.
  Con un budget breve la resa peggiora sulle dimensioni minori.

### Preferenze dell'insegnante (`SchedulePreference`)

| Valore | Comportamento |
|---|---|
| `EARLY` | Preferisce le prime ore della mattina |
| `LATE` | Preferisce le ultime ore disponibili |
| `MINIMIZE_GAPS` | Tiene contigua la giornata da 4 ore; spezza solo quella da 5 |
| `MAXIMIZE_GAPS` | Vuole l'ora di stacco su **ogni** giornata lunga della settimana |
| `NONE` | Nessuna preferenza; i criteri sulla forma della giornata si applicano comunque |

Le due preferenze sui buchi agiscono **sulla settimana, non sulla giornata**: su
quante giornate usano la loro franchigia, mai su quanto a fondo una singola
giornata viene tagliata. `MAXIMIZE_GAPS` significa "un buco al giorno per tutta la
settimana", non "tanti buchi in un giorno" - quest'ultima lettura e' comunque
vietata a chiunque dalla franchigia.

Nessuna delle due tocca la contiguita' delle ore nella stessa classe: non la
riguarda, e legarvela produceva orari sistematicamente diversi fra insegnanti per
una ragione che nessuno aveva chiesto.

In precedenza erano **modulatori** che scalavano insieme i pesi su buchi e
contiguita'. Questo permetteva a `MAXIMIZE_GAPS` di ottenere piu' ore di buco
nella stessa giornata, esito che i criteri assoluti ora vietano, e rendeva
`MINIMIZE_GAPS` cosi' aggressivo da annullare l'assert sulla calibrazione:
`W_LONG_RUN > W_GAP + 2 * W_TIME_PREFERENCE` confrontava il peso base mentre il
modello usava quello modulato, e per un insegnante `MINIMIZE_GAPS` con preferenza
oraria valeva `6 > 6`, falso. L'assert passava dichiarando una garanzia che il
modello non offriva.

## Diagnostica di qualita'

`POST /api/scheduling/generate` riporta in `metadata.quality` un totale per
ciascuna dimensione e, sotto `worst`, le coppie insegnante-giorno che vi
contribuiscono di piu'. Serve a tarare i pesi senza rileggere le griglie a mano.

| Dimensione | Significato | In `worst` |
|---|---|---|
| `class_blocks` | Gruppi consecutivi per classe eccedenti il minimo | si |
| `excess_gap_hours` | Ore di buco oltre la franchigia della giornata | si |
| `long_runs` | Finestre di 4 ore di lezione consecutive | si |
| `balance_deviation` | Scostamento del carico giornaliero dalla banda | si |
| `break_days` | Giornate che usano la loro franchigia | no |
| `missed_break_days` | Giornate lunghe senza la loro ora di stacco | no |

Le ultime due sono informative e restano fuori da `worst`: una giornata servita
come l'insegnante ha chiesto non e' un difetto, e classificarla come tale
seppellirebbe quelli veri. `missed_break_days` indica un difetto solo per chi ha
`MAXIMIZE_GAPS`, informazione che le metriche non hanno perche' sono calcolate
dai soli slot.

Le metriche **non** sono persistite con gli orari salvati.

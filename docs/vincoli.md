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

### Requisiti delle materie (`MatterRequirements`)
Vincoli aggiuntivi opzionali assegnabili a una materia o a una singola assegnazione:

| Tag | Significato |
|---|---|
| `at_least_twice_per_week` | La materia deve comparire in almeno 2 giorni distinti |
| `one_lesson_of_two_hours_per_week` | Almeno una volta a settimana le ore devono essere consecutive (2h) |
| `one_lesson_of_three_hours_per_week` | Almeno una volta a settimana le ore devono essere consecutive (3h) |

> ⚠️ **Conflitto noto**: `at_least_twice_per_week` su un'assegnazione da 2 ore/settimana forza esattamente 1 ora in 2 giorni diversi. Se quell'insegnante non ha altre lezioni in uno di quei giorni per raggiungere il minimo legale di 2 ore, l'assegnazione è **impossibile da pianificare** in isolamento, e trascina in `INFEASIBLE` l'intera generazione (il modello CP-SAT è unico e condiviso da tutti gli insegnanti). `GET /api/scheduling/preview` rileva questo caso per singolo insegnante (indipendentemente dal resto della pianificazione) e lo segnala in `issues`; lo stesso controllo arricchisce il messaggio d'errore di `POST /api/scheduling/generate` quando la generazione fallisce per questo motivo.

---

## Vincoli Soft (preferenze insegnante)

Espressi tramite `SchedulePreference`, usati come obiettivo di ottimizzazione dal solver:

| Valore | Comportamento |
|---|---|
| `EARLY` | Preferisce le prime ore della mattina |
| `LATE` | Preferisce le ultime ore disponibili |
| `MINIMIZE_GAPS` | Raggruppa le lezioni, minimizza i buchi |
| `MAXIMIZE_GAPS` | Distribuisce le lezioni, massimizza il tempo libero |
| `NONE` | Nessuna preferenza |

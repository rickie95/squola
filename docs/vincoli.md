# Vincoli del dominio

I vincoli si dividono in due categorie:
- **Hard**: devono essere sempre soddisfatti, altrimenti l'orario non è valido
- **Soft**: preferenze ottimizzate dal solver, non obbligatorie

---

## Vincoli Hard

### Insegnanti
- Un insegnante non può essere in due classi nello stesso slot
- Gli slot in cui un insegnante è occupato in un'altra scuola devono essere esclusi (**blacklist**)

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

# Squola — Domain Glossary

## Workspace
Contenitore di ownership dei dati dell'app (insegnanti, classi, materie, assegnazioni, orari). In questa fase ogni utente registra e possiede un workspace.

## User
Identità autenticabile dell'applicazione. Ha username globale univoco e accede ai dati del proprio workspace.

## Sessione autenticata (`AuthSession`)
Sessione persistente server-side associata a uno user e identificata via cookie HTTP-only.

## Indisponibilità (`TeacherUnavailability`)
Uno slot orario (giorno + ora) in cui un insegnante non è disponibile per il planning — ad esempio perché impegnato in un'altra scuola. Il solver esclude questi slot dall'assegnazione. Di default un insegnante non ha indisponibilità (tutti gli slot sono assegnabili).

Modellata come record `(day_of_week: 0–4, hour_slot: 1–6)` nella tabella `teacher_unavailabilities`. Un "giorno intero bloccato" è rappresentato da 6 record distinti (uno per ogni ora), non da un concetto separato.

> Codice: `src/squola/models.py` → `TeacherUnavailability`, endpoint `POST /teachers/{id}/unavailabilities`.

## Slot / Hour Slot
Un'ora scolastica identificata da un numero 1–6 (corrispondente alle fasce 08:00–14:00). La settimana ha 5 giorni (0=Lunedì, 4=Venerdì) × 6 slot = 30 slot per insegnante.

## SchedulePreference
Preferenza di scheduling di un insegnante: `EARLY`, `LATE`, `MINIMIZE_GAPS`, `MAXIMIZE_GAPS`, `NONE`. Usata dal solver CP-SAT come obiettivo di ottimizzazione (vincolo soft).

## ClassMatterAssignment
L'assegnazione di un insegnante a una materia in una classe specifica, con il numero di ore settimanali. È l'unità su cui il solver crea le variabili di decisione.

## MatterRequirements
Vincoli aggiuntivi (hard) applicabili a una materia o a una singola `ClassMatterAssignment`: `at_least_twice_per_week`, `one_lesson_of_two_hours_per_week`, `one_lesson_of_three_hours_per_week`, `max_one_hour_per_day`, `max_two_hours_per_day`.

## Cap giornaliero (`max_one_hour_per_day`, `max_two_hours_per_day`)
Il numero massimo di ore di **una singola `ClassMatterAssignment`** che possono finire nello stesso giorno. È un totale giornaliero, non la lunghezza di un blocco consecutivo: con `max_two_hours_per_day`, due ore consecutive più una terza dopo un buco restano tre ore in un giorno, quindi vietate.

Un'assegnazione che non dichiara nessuno dei due resta al cap di sistema `MAX_DAILY_ASSIGNMENT_HOURS` (3 ore). Se li dichiara entrambi vince il più stretto, quindi 1 ora. Il cap vale per assegnazione, non per classe né per insegnante: due materie diverse nella stessa classe hanno ciascuna il proprio.

> Codice: `src/squola/scheduler.py` → `resolve_daily_cap`, `_add_daily_assignment_cap_constraint`.

## Requisiti di default di una materia (`Matter.default_requirements`)
I requisiti che una materia trasmette alle sue assegnazioni. Non sono solo un pre-riempimento del form: cambiarli via `PUT /matters/{id}` li propaga a **tutte le assegnazioni già esistenti** di quella materia nel workspace.

La propagazione è un delta, non una sovrascrittura: ciò che la materia guadagna viene aggiunto alle assegnazioni, ciò che perde viene tolto, e un requisito messo sulla singola assegnazione — che non compare né nei vecchi né nei nuovi default — sopravvive a entrambe le operazioni.

## Combinazione non pianificabile
Alcune combinazioni di requisiti sono impossibili per pura aritmetica, indipendentemente dal resto dell'orario: un cap giornaliero più stretto della lezione lunga richiesta (`max_two_hours_per_day` con `one_lesson_of_three_hours_per_week`), o ore settimanali superiori a `cap × 5 giorni`. Ogni scrittura che imposta requisiti — creazione e modifica di una materia, creazione e modifica di un'assegnazione — le rifiuta con `400` senza scrivere nulla, invece di lasciarle emergere come `INFEASIBLE` a fine generazione. Le infattibilità che dipendono dal resto dell'orario (indisponibilità degli insegnanti, altre classi) restano compito del solver.

> Codice: `src/squola/scheduler.py` → `requirement_conflict`.

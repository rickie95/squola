# Squola — Domain Glossary

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
Vincoli aggiuntivi (hard) applicabili a una materia o a una singola `ClassMatterAssignment`: `at_least_twice_per_week`, `one_lesson_of_two_hours_per_week`, `one_lesson_of_three_hours_per_week`.

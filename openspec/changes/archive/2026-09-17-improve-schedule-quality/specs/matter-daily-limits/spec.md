## Purpose

Limita quante ore di una stessa assegnazione materia-classe possono ricadere in
una singola giornata, per evitare che una classe riceva la stessa materia troppo a
lungo o ripetutamente nello stesso giorno.

## ADDED Requirements

### Requirement: Tetto giornaliero per assegnazione materia-classe
Il sistema SHALL collocare al massimo tre ore di una stessa assegnazione
materia-classe in una singola giornata. Il tetto SHALL valere sul totale
giornaliero dell'assegnazione, indipendentemente dal fatto che le ore siano
consecutive o separate da altre lezioni o da ore libere. Il tetto SHALL essere un
vincolo hard e SHALL applicarsi a ogni assegnazione indipendentemente dai
requisiti aggiuntivi della materia e dalle preferenze del docente.

#### Scenario: Quattro ore consecutive della stessa materia
- **WHEN** i restanti vincoli consentirebbero di collocare quattro ore consecutive della stessa materia nella stessa classe in un giorno
- **THEN** il sistema non restituisce quella disposizione in un orario generato

#### Scenario: Quattro ore della stessa materia separate da un'interruzione
- **WHEN** i restanti vincoli consentirebbero di collocare tre ore della stessa materia nella stessa classe in un giorno e una quarta ora della stessa materia piu' tardi nello stesso giorno
- **THEN** il sistema non restituisce quella disposizione in un orario generato

#### Scenario: Tre ore della stessa materia sono ammesse
- **WHEN** un orario colloca tre ore della stessa assegnazione materia-classe in un giorno
- **THEN** il sistema considera valido quel carico giornaliero

#### Scenario: Tre ore in giorni consecutivi sono ammesse
- **WHEN** un orario colloca tre ore della stessa assegnazione materia-classe in un giorno e altre tre nel giorno successivo
- **THEN** il sistema considera valida quella distribuzione

### Requirement: Il tetto giornaliero puo' rendere la generazione infeasible
Il sistema SHALL segnalare la generazione come infeasible quando nessun orario puo'
soddisfare insieme le ore settimanali richieste, tutti gli altri vincoli hard e il
tetto giornaliero per assegnazione. Il sistema SHALL NOT restituire un orario che
viola il tetto.

#### Scenario: Monte ore incompatibile con il tetto
- **WHEN** un'assegnazione richiede piu' ore settimanali di quante il tetto giornaliero consenta di collocare nei giorni disponibili
- **THEN** la generazione dell'orario riporta un esito infeasible

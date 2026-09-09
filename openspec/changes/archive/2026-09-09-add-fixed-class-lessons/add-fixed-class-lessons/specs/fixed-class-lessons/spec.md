## Purpose

Consente di fissare lezioni di una classe in una griglia settimanale prima della generazione, affinche' l'orario prodotto preservi le decisioni gia' prese.

## ADDED Requirements

### Requirement: Configurazione della griglia di lezioni fisse
Il sistema SHALL mostrare nella scheda di una classe una griglia modificabile con le colonne da Lunedi' a Venerdi' e le righe per tutti gli slot orari della settimana. Per ciascuna cella, il sistema SHALL consentire all'utente di selezionare o sostituire esclusivamente un insegnamento gia' assegnato alla classe, oppure di rimuovere la selezione. Le celle salvate SHALL mostrare materia e docente dell'assegnamento selezionato.

#### Scenario: Fissare una materia in una cella libera
- **WHEN** l'utente seleziona Italiano, gia' assegnato alla classe, per Martedi' alla prima ora e salva
- **THEN** il sistema memorizza la lezione fissa e la mostra nella cella con la relativa materia e docente

#### Scenario: Rimuovere una lezione fissa
- **WHEN** l'utente svuota una cella che contiene una lezione fissa
- **THEN** il sistema rimuove il vincolo corrispondente e mostra la cella come libera

#### Scenario: Impedire la scelta di una materia non assegnata
- **WHEN** l'utente apre la selezione di una cella della griglia
- **THEN** il sistema presenta solo gli assegnamenti materia-docente appartenenti alla classe selezionata

### Requirement: Validazione immediata dei vincoli fissi
Il sistema SHALL rifiutare il salvataggio di una lezione fissa se lo slot e' fuori dall'orario settimanale configurato, se l'assegnamento non appartiene alla classe e al workspace attivi, se il docente e' indisponibile, se lo stesso docente e' gia' fissato in un'altra classe nello stesso slot, oppure se il numero di slot fissi per un assegnamento supera le sue ore settimanali. Il sistema SHALL restituire un errore esplicativo senza modificare i vincoli esistenti.

#### Scenario: Conflitto con indisponibilita' del docente
- **WHEN** l'utente tenta di fissare una lezione in uno slot in cui il docente dell'assegnamento e' indisponibile
- **THEN** il sistema rifiuta il salvataggio e comunica il conflitto

#### Scenario: Conflitto tra classi dello stesso docente
- **WHEN** l'utente tenta di fissare una lezione per un docente gia' fissato in un'altra classe nello stesso giorno e ora
- **THEN** il sistema rifiuta il salvataggio e comunica il conflitto

#### Scenario: Superamento delle ore settimanali
- **WHEN** l'utente tenta di salvare un numero di slot fissi superiore alle ore settimanali dell'assegnamento
- **THEN** il sistema rifiuta lo slot eccedente e mantiene invariati i vincoli gia' salvati

### Requirement: Coerenza del ciclo di vita degli assegnamenti
Il sistema SHALL eliminare i vincoli fissi associati quando viene rimossa la relativa assegnazione materia dalla classe. Il sistema SHALL rifiutare l'aggiornamento di un assegnamento che riduce le ore settimanali al di sotto del numero dei suoi slot fissi. La clonazione di una classe SHALL copiare gli assegnamenti materia-docente ma SHALL NOT copiare le lezioni fisse.

#### Scenario: Rimozione di un assegnamento
- **WHEN** l'utente rimuove da una classe un assegnamento che ha lezioni fisse
- **THEN** il sistema elimina anche tutte le lezioni fisse di quell'assegnamento

#### Scenario: Riduzione incompatibile del monte ore
- **WHEN** l'utente riduce le ore settimanali di un assegnamento sotto il numero delle sue lezioni fisse
- **THEN** il sistema rifiuta l'aggiornamento e comunica il motivo

#### Scenario: Clonazione della classe
- **WHEN** l'utente clona una classe che contiene lezioni fisse
- **THEN** la nuova classe contiene gli stessi assegnamenti materia-docente ma nessuna lezione fissa

### Requirement: Rispetto dei vincoli nella generazione
Il sistema SHALL trattare ogni lezione fissa salvata come vincolo hard durante la generazione dell'orario. Un orario generato con stato ottimale o realizzabile SHALL contenere ogni lezione fissa nello stesso giorno, ora, classe, materia e docente configurati dall'utente. Il sistema SHALL continuare ad applicare tutti gli altri vincoli hard e le preferenze esistenti.

#### Scenario: Generazione con due ore fisse consecutive
- **WHEN** una classe ha Italiano fissato per Martedi' alla prima e alla seconda ora e viene generato un orario realizzabile
- **THEN** l'orario generato colloca Italiano con il docente assegnato in entrambe quelle celle

#### Scenario: Vincoli fissi incompatibili con altri requisiti
- **WHEN** i vincoli fissi validi rendono l'intero problema non realizzabile insieme agli altri vincoli hard
- **THEN** il sistema non genera un orario parziale e segnala che non esiste un orario valido

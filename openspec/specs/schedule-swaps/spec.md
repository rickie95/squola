# Schedule Swaps Specification

## Purpose

Permette di ritoccare a mano un orario salvato con cambi fra docenti che
preservano il monte ore di ogni classe e i vincoli del generatore, proponendo
solo i cambi che l'orario puo' permettersi.

## Requirements

### Requirement: Griglia globale modificabile
Il sistema SHALL offrire, per ogni orario salvato, una pagina di cambi che mostra
la griglia globale dei docenti: una riga per docente, una colonna per ogni coppia
giorno-ora, e in ogni cella occupata la classe (con il suo colore) e la materia.
L'utente SHALL poter selezionare una cella occupata per chiedere i cambi possibili
di quella lezione.

#### Scenario: Apertura della pagina da un orario salvato
- **WHEN** l'utente apre la pagina dei cambi di un orario salvato
- **THEN** il sistema mostra la griglia globale con tutte le lezioni di quell'orario

#### Scenario: Selezione di una lezione
- **WHEN** l'utente seleziona la cella del docente T nello slot s1
- **THEN** il sistema elenca i cambi possibili che spostano quella lezione

#### Scenario: Cella vuota
- **WHEN** l'utente seleziona una cella senza lezione
- **THEN** il sistema non propone cambi

### Requirement: Il cambio scambia due slot lungo una catena
Un cambio SHALL essere definito da una lezione (docente T, slot s1) e da un
secondo slot s2 diverso da s1. La catena del cambio SHALL comprendere T e,
ripetutamente, ogni docente che insegna nello slot s1 o s2 in una classe dove
insegna un docente gia' nella catena nell'altro dei due slot. Applicare il cambio
SHALL portare ogni lezione della catena da s1 a s2 e viceversa, lasciando ogni
lezione con lo stesso docente, la stessa classe e la stessa materia.

#### Scenario: Scambio semplice fra due docenti
- **WHEN** in 3A insegnano MR in s1 e GV in s2, e GV e' libero in s1 e MR in s2
- **THEN** il cambio (MR, s1, s2) porta GV in 3A in s1 e MR in 3A in s2

#### Scenario: Scambio a tre docenti
- **WHEN** in s1 GV e' in 1B, RM in 3A, MG in 2C, e in s2 GV e' in 2C, RM in 1B, MG in 3A
- **THEN** il cambio (GV, s1, s2) produce in s1 GV in 2C, RM in 1B, MG in 3A, e in s2 GV in 1B, RM in 3A, MG in 2C

#### Scenario: Monte ore invariato
- **WHEN** un cambio viene applicato
- **THEN** ogni coppia classe-materia conserva lo stesso numero di ore settimanali e lo stesso docente

#### Scenario: Cambio senza effetto
- **WHEN** applicare il cambio lascerebbe ogni slot di ogni classe con la stessa lezione
- **THEN** il sistema non lo propone

### Requirement: Le classi non restano mai scoperte
Il sistema SHALL scartare un cambio che lascia una classe senza lezione in uno
slot in cui prima ne aveva una, o gliene assegna una in uno slot prima libero.
L'insieme degli slot occupati di ogni classe SHALL restare identico.

#### Scenario: Classe con lezione solo in uno dei due slot
- **WHEN** la catena contiene una classe che ha lezione in s1 ma e' libera in s2
- **THEN** il sistema scarta il cambio

### Requirement: I cambi rispettano i vincoli hard
Il sistema SHALL scartare un cambio che, sull'orario risultante, introduce una
violazione assente prima del cambio di uno qualsiasi di questi vincoli, valutati
sui dati attuali di docenti, classi e materie:
- un docente in due classi nello stesso slot;
- un docente in uno slot in cui e' indisponibile;
- un giorno di un docente con un numero di ore diverso da 0 o da 2-5, e il giorno
  libero garantito a chi lo ha richiesto;
- il tetto giornaliero di ore di un'assegnazione (3, o quello piu' stretto dei
  suoi requisiti);
- i requisiti `at_least_twice_per_week`, `one_lesson_of_two_hours_per_week`,
  `one_lesson_of_three_hours_per_week`.

Il sistema SHALL scartare un cambio la cui catena contiene una lezione fissa.

#### Scenario: Tre ore della stessa materia nello stesso giorno
- **WHEN** un cambio porterebbe a 4 le ore di matematica di 3A in un giorno
- **THEN** il sistema scarta il cambio

#### Scenario: Docente indisponibile
- **WHEN** un cambio porterebbe un docente in uno slot in cui e' indisponibile
- **THEN** il sistema scarta il cambio

#### Scenario: Giornata da un'ora
- **WHEN** un cambio lascerebbe a un docente una sola ora in un giorno
- **THEN** il sistema scarta il cambio

#### Scenario: Lezione fissa nella catena
- **WHEN** la catena di un cambio contiene una lezione fissa
- **THEN** il sistema scarta il cambio

#### Scenario: Violazione gia' presente
- **WHEN** l'orario viola gia' un vincolo prima del cambio e il cambio non la peggiora
- **THEN** il sistema non scarta il cambio per quel vincolo

### Requirement: Avvisi sui criteri soft
Il sistema SHALL proporre con un avviso i cambi validi che peggiorano, per un
docente coinvolto, le ore di buco oltre la franchigia o le finestre di 4 ore di
lezione consecutive. L'avviso SHALL indicare il docente, il giorno e il criterio
peggiorato.

#### Scenario: Cambio che apre un secondo buco
- **WHEN** un cambio porta un docente a due ore di buco in un giorno
- **THEN** il sistema propone il cambio con un avviso che indica docente, giorno e ore di buco

### Requirement: Ordine dei suggerimenti
Il sistema SHALL elencare prima i cambi senza avvisi e poi quelli con avvisi; a
parita', prima i cambi con meno docenti nella catena.

#### Scenario: Cambio pulito e cambio con avviso
- **WHEN** fra i cambi validi uno ha avvisi e uno no
- **THEN** quello senza avvisi compare per primo

### Requirement: Anteprima del cambio
Per ogni cambio proposto il sistema SHALL mostrare i docenti coinvolti e, per
ciascuno, la classe prima e dopo in s1 e in s2.

#### Scenario: Consultazione di un suggerimento
- **WHEN** l'utente esamina un cambio proposto
- **THEN** il sistema mostra per ogni docente della catena la classe prima e dopo nei due slot

### Requirement: Bozza e salvataggio come nuovo orario
I cambi applicati SHALL accumularsi in una bozza, e l'utente SHALL poter
annullare l'ultimo cambio applicato. I suggerimenti SHALL essere calcolati sulla
bozza corrente. L'orario di partenza SHALL restare invariato; solo il salvataggio
esplicito SHALL creare un nuovo orario salvato con i cambi applicati.

#### Scenario: Cambi successivi
- **WHEN** l'utente applica un cambio e seleziona un'altra lezione
- **THEN** i suggerimenti tengono conto del cambio gia' applicato

#### Scenario: Annullamento
- **WHEN** l'utente annulla l'ultimo cambio
- **THEN** la bozza torna allo stato precedente a quel cambio

#### Scenario: Salvataggio
- **WHEN** l'utente salva una bozza con almeno un cambio
- **THEN** il sistema crea un nuovo orario salvato e l'orario di partenza non cambia

#### Scenario: Abbandono senza salvare
- **WHEN** l'utente lascia la pagina senza salvare
- **THEN** nessun orario viene creato o modificato

#### Scenario: Salvataggio di un cambio non valido
- **WHEN** viene richiesto il salvataggio di una sequenza di cambi di cui uno non e' valido sui dati attuali
- **THEN** il sistema rifiuta il salvataggio e indica il cambio non valido

### Requirement: Collegamento dell'orario ai dati attuali
Gli orari salvati SHALL includere, per ogni lezione, gli identificativi di
docente, classe, materia e assegnazione. Per un orario salvato senza
identificativi il sistema SHALL ricollegare le lezioni ai dati attuali tramite i
nomi; se una lezione non corrisponde a esattamente un'assegnazione attuale con
quel docente, quella classe e quella materia, la pagina SHALL mostrare l'orario
indicando le lezioni non ricollegate e SHALL non proporre cambi.

#### Scenario: Orario recente
- **WHEN** l'utente apre la pagina dei cambi di un orario salvato con gli identificativi
- **THEN** il sistema propone i cambi normalmente

#### Scenario: Orario vecchio ricollegabile
- **WHEN** un orario senza identificativi corrisponde per nome ai dati attuali
- **THEN** il sistema propone i cambi normalmente

#### Scenario: Orario vecchio non ricollegabile
- **WHEN** un orario senza identificativi contiene un docente rinominato o un'assegnazione cancellata
- **THEN** la pagina indica le lezioni non ricollegate e non propone cambi

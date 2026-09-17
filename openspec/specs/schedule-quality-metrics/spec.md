# Schedule Quality Metrics Specification

## Purpose

Espone nella risposta di generazione una diagnostica quantitativa della qualita'
dell'orario prodotto, per rendere verificabili difetti oggi rilevabili solo
leggendo a mano le griglie settimanali.

## Requirements

### Requirement: La generazione espone metriche di qualita' aggregate
La risposta di una generazione conclusa con esito ottimale o realizzabile SHALL
includere, oltre ai metadati gia' previsti, un totale per ciascuna dimensione di
qualita' dell'orario: gruppi consecutivi per classe eccedenti il minimo, ore di
buco, filate di lezione di quattro o piu' ore, e scostamento complessivo del
carico giornaliero dei docenti dalla banda attesa.

#### Scenario: Metriche presenti in una generazione riuscita
- **WHEN** un utente genera un orario e la generazione produce un esito ottimale o realizzabile
- **THEN** la risposta contiene un valore numerico per ciascuna dimensione di qualita'

#### Scenario: Generazione senza soluzione
- **WHEN** una generazione riporta un esito infeasible o l'assenza di dati
- **THEN** la risposta non contiene metriche di qualita' e riporta l'esito come gia' previsto

### Requirement: La generazione identifica le giornate peggiori
La risposta di una generazione conclusa con esito ottimale o realizzabile SHALL
elencare le coppie docente-giorno che contribuiscono maggiormente a ciascuna
dimensione di qualita', identificando il docente, il giorno e il valore misurato.

#### Scenario: Individuare una giornata frammentata
- **WHEN** un orario generato contiene per un docente una giornata con piu' gruppi consecutivi per classe di quanti le sue classi di quel giorno ne richiedano
- **THEN** la risposta elenca quella coppia docente-giorno con il valore misurato

### Requirement: Le metriche non sono persistite
Il sistema SHALL NOT memorizzare le metriche di qualita' insieme agli orari
salvati. Il recupero di un orario salvato SHALL restituire gli stessi dati previsti
prima di questa capability.

#### Scenario: Apertura di un orario salvato
- **WHEN** un utente apre un orario precedentemente salvato
- **THEN** il sistema restituisce l'orario senza metriche di qualita'

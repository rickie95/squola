# Schedule Quality Metrics Specification

## Purpose

Espone nella risposta di generazione una diagnostica quantitativa della qualita'
dell'orario prodotto, per rendere verificabili difetti oggi rilevabili solo
leggendo a mano le griglie settimanali.

## Requirements

### Requirement: La generazione espone metriche di qualita' aggregate
La risposta di una generazione conclusa con esito ottimale o realizzabile SHALL
includere, oltre ai metadati gia' previsti, un totale per ciascuna dimensione di
qualita' dell'orario: gruppi consecutivi per classe eccedenti il minimo, filate di
lezione di quattro o piu' ore, scostamento complessivo del carico giornaliero dei
docenti dalla banda attesa, e tre grandezze distinte sui buchi:
- le ore di buco eccedenti la franchigia della giornata, che indicano un difetto;
- le giornate che utilizzano la propria franchigia, che non indicano un difetto;
- le giornate lunghe prive della propria ora di stacco, che indicano un difetto per
  i soli docenti con preferenza di distribuzione.

Il sistema SHALL calcolare le ore di buco escludendo gli slot di indisponibilita'
dei docenti, cosi' che la diagnostica misuri le stesse ore che il sistema penalizza
durante la generazione.

#### Scenario: Metriche presenti in una generazione riuscita
- **WHEN** un utente genera un orario e la generazione produce un esito ottimale o realizzabile
- **THEN** la risposta contiene un valore numerico per ciascuna dimensione di qualita', con le tre grandezze sui buchi distinte fra loro

#### Scenario: Giornata con il solo stacco previsto
- **WHEN** un orario generato contiene per un docente una giornata lunga con una sola ora di buco
- **THEN** la risposta conteggia quella giornata fra quelle che utilizzano la franchigia e non riporta per essa alcuna ora di buco eccedente

#### Scenario: Indisponibilita' fra due lezioni
- **WHEN** un orario generato colloca due lezioni di un docente ai lati di uno slot in cui quel docente e' indisponibile
- **THEN** la risposta non conteggia quello slot fra le ore di buco

#### Scenario: Generazione senza soluzione
- **WHEN** una generazione riporta un esito infeasible o l'assenza di dati
- **THEN** la risposta non contiene metriche di qualita' e riporta l'esito come gia' previsto

### Requirement: La generazione identifica le giornate peggiori
La risposta di una generazione conclusa con esito ottimale o realizzabile SHALL
elencare le coppie docente-giorno che contribuiscono maggiormente a ciascuna
dimensione di qualita' che indica un difetto, identificando il docente, il giorno e
il valore misurato. Il sistema SHALL NOT includere in tale elenco le dimensioni che
non indicano un difetto, cosi' che una giornata servita come il docente desidera non
compaia fra le peggiori.

#### Scenario: Individuare una giornata frammentata
- **WHEN** un orario generato contiene per un docente una giornata con piu' gruppi consecutivi per classe di quanti le sue classi di quel giorno ne richiedano
- **THEN** la risposta elenca quella coppia docente-giorno con il valore misurato

#### Scenario: Individuare una giornata oltre la franchigia
- **WHEN** un orario generato contiene per un docente una giornata con piu' ore di buco di quante la sua franchigia ne consenta
- **THEN** la risposta elenca quella coppia docente-giorno con il numero di ore eccedenti

#### Scenario: Una giornata con il solo stacco non e' fra le peggiori
- **WHEN** un orario generato contiene per un docente con preferenza di distribuzione una giornata lunga con la sola ora di stacco richiesta
- **THEN** la risposta non elenca quella coppia docente-giorno fra quelle che contribuiscono ai difetti

### Requirement: Le metriche non sono persistite
Il sistema SHALL NOT memorizzare le metriche di qualita' insieme agli orari
salvati. Il recupero di un orario salvato SHALL restituire gli stessi dati previsti
prima di questa capability.

#### Scenario: Apertura di un orario salvato
- **WHEN** un utente apre un orario precedentemente salvato
- **THEN** il sistema restituisce l'orario senza metriche di qualita'

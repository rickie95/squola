## Purpose

Definisce come le ore di un docente devono essere disposte all'interno di una
singola giornata: contiguita' delle ore svolte nella stessa classe, ampiezza dei
buchi e lunghezza delle filate di lezione consecutive.

## ADDED Requirements

### Requirement: Le ore della stessa classe sono contigue
A parita' di vincoli hard soddisfatti, il sistema SHALL preferire gli orari in cui
le ore che un docente svolge in una stessa classe in uno stesso giorno occupano
slot consecutivi. Il sistema SHALL trattare come equivalente ogni disposizione che
minimizza, per ciascuna coppia (docente, giorno), il numero di gruppi consecutivi
distinti per classe. Quando un docente insegna piu' materie nella stessa classe, le
ore di materie diverse nella stessa classe SHALL contare come un unico gruppo
contiguo.

#### Scenario: Avvicendamento ripetuto fra due classi
- **WHEN** un docente ha in un giorno due ore in una classe e due ore in un'altra classe, e entrambe le disposizioni sono compatibili con i vincoli hard
- **THEN** il sistema genera la disposizione che raggruppa le ore di ciascuna classe anziche' alternarle ora per ora

#### Scenario: Ore della stessa classe separate da un buco
- **WHEN** un docente ha in un giorno due ore nella stessa classe e un orario alternativo compatibile con i vincoli hard le rende consecutive
- **THEN** il sistema genera l'orario in cui le due ore sono consecutive

#### Scenario: Ora aggiuntiva della stessa classe dopo un'interruzione
- **WHEN** un docente ha in un giorno un blocco di ore in una classe e un'ulteriore ora nella stessa classe collocabile in adiacenza al blocco
- **THEN** il sistema colloca l'ora aggiuntiva in adiacenza al blocco anziche' separata da altre lezioni o da un buco

#### Scenario: Materie diverse nella stessa classe non sono un avvicendamento
- **WHEN** un docente svolge consecutivamente in una stessa classe ore di due materie diverse
- **THEN** il sistema non considera quella successione come una disposizione da evitare

### Requirement: Le filate di lezione consecutive sono limitate
A parita' di vincoli hard soddisfatti, il sistema SHALL preferire gli orari che
evitano filate di quattro o piu' ore di lezione consecutive per un docente in una
giornata, indipendentemente dalle classi coinvolte. Il sistema SHALL penalizzare
una filata di cinque ore piu' di una filata di quattro.

#### Scenario: Giornata da quattro ore
- **WHEN** un docente ha quattro ore in un giorno e i vincoli hard consentono sia quattro ore consecutive sia due blocchi da due separati da un'ora libera
- **THEN** il sistema genera la disposizione con l'ora libera intermedia

#### Scenario: Giornata da cinque ore
- **WHEN** un docente ha cinque ore in un giorno e i vincoli hard consentono di collocare un'ora libera all'interno della giornata
- **THEN** il sistema genera una disposizione con un'ora libera intermedia anziche' cinque ore consecutive

#### Scenario: Giornata da tre ore
- **WHEN** un docente ha tre ore in un giorno e i vincoli hard consentono di renderle consecutive
- **THEN** il sistema genera le tre ore consecutive senza introdurre ore libere intermedie

### Requirement: I buchi oltre il primo sono fortemente penalizzati
Il sistema SHALL calcolare come buco ogni slot senza lezione compreso fra due slot
con lezione dello stesso docente nello stesso giorno. A parita' di vincoli hard
soddisfatti, il sistema SHALL penalizzare le ore di buco successive alla prima di
una giornata in misura sensibilmente maggiore della prima.

#### Scenario: Buco singolo contro buco doppio
- **WHEN** i vincoli hard consentono per un docente in un giorno sia una disposizione con un'ora di buco sia una con due ore di buco consecutive, a parita' di ogni altra dimensione
- **THEN** il sistema genera la disposizione con una sola ora di buco

#### Scenario: Ore libere a inizio o fine giornata non sono buchi
- **WHEN** un docente ha ore libere prima della sua prima lezione o dopo la sua ultima lezione del giorno
- **THEN** il sistema non conteggia quelle ore come buchi

### Requirement: Le preferenze sui buchi modulano la forma della giornata
Il sistema SHALL applicare i criteri sulla forma della giornata a ogni docente,
qualunque sia la sua preferenza di scheduling, inclusa l'assenza di preferenza. Le
preferenze di raggruppamento e di distribuzione SHALL agire come modulatori
dell'intensita' di tali criteri: la preferenza di raggruppamento SHALL rafforzarli
e la preferenza di distribuzione SHALL attenuarli. Nessuna preferenza SHALL
invertirne il segno.

#### Scenario: Docente senza preferenza
- **WHEN** un docente non ha impostato alcuna preferenza di scheduling
- **THEN** il sistema applica comunque i criteri di contiguita', filata e buco alla sua giornata

#### Scenario: Preferenza di distribuzione
- **WHEN** un docente ha impostato la preferenza di distribuzione delle lezioni
- **THEN** il sistema attenua le penalita' su buchi e contiguita' per quel docente ma non genera per lui una giornata piu' frammentata di quanto quelle penalita' attenuate giustifichino

### Requirement: Le preferenze di fascia oraria non prevalgono sulla forma della giornata
Il sistema SHALL bilanciare le preferenze di fascia oraria mattutina o pomeridiana
con i criteri sulla forma della giornata in modo che un docente con una preferenza
di fascia oraria non riceva sistematicamente una giornata peggiore, per
contiguita', filate e buchi, di un docente senza preferenze.

#### Scenario: Docente con preferenza di fascia oraria
- **WHEN** un docente con preferenza per le prime ore ha un orario in cui anticipare una lezione introdurrebbe un avvicendamento fra classi o un buco aggiuntivo
- **THEN** il sistema non anticipa quella lezione al solo scopo di soddisfare la preferenza di fascia oraria

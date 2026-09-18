# Teacher Day Shape Specification

## Purpose

Definisce come le ore di un docente devono essere disposte all'interno di una
singola giornata: contiguita' delle ore svolte nella stessa classe, ampiezza dei
buchi e lunghezza delle filate di lezione consecutive.

## Requirements

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
una filata di cinque ore piu' di una filata di quattro. Per un docente con
preferenza di raggruppamento il sistema SHALL applicare questo criterio alle sole
filate di cinque ore: in una giornata da quattro ore la preferenza di
raggruppamento SHALL prevalere e il sistema SHALL generare le quattro ore
consecutive.

#### Scenario: Giornata da quattro ore
- **WHEN** un docente senza preferenza di raggruppamento ha quattro ore in un giorno e i vincoli hard consentono sia quattro ore consecutive sia due blocchi da due separati da un'ora libera
- **THEN** il sistema genera la disposizione con l'ora libera intermedia

#### Scenario: Giornata da quattro ore con preferenza di raggruppamento
- **WHEN** un docente con preferenza di raggruppamento ha quattro ore in un giorno e i vincoli hard consentono sia quattro ore consecutive sia due blocchi da due separati da un'ora libera
- **THEN** il sistema genera le quattro ore consecutive

#### Scenario: Giornata da cinque ore
- **WHEN** un docente ha cinque ore in un giorno e i vincoli hard consentono di collocare un'ora libera all'interno della giornata
- **THEN** il sistema genera una disposizione con un'ora libera intermedia anziche' cinque ore consecutive

#### Scenario: Giornata da cinque ore con preferenza di raggruppamento
- **WHEN** un docente con preferenza di raggruppamento ha cinque ore in un giorno e i vincoli hard consentono di collocare un'ora libera all'interno della giornata
- **THEN** il sistema genera comunque la disposizione con l'ora libera intermedia

#### Scenario: Giornata da tre ore
- **WHEN** un docente ha tre ore in un giorno e i vincoli hard consentono di renderle consecutive
- **THEN** il sistema genera le tre ore consecutive senza introdurre ore libere intermedie

### Requirement: I buchi oltre il primo sono fortemente penalizzati
Il sistema SHALL calcolare come buco ogni slot senza lezione compreso fra due slot
con lezione dello stesso docente nello stesso giorno, **escludendo gli slot in cui
il docente e' indisponibile**: in quelle ore il docente non e' a scuola e non sta
attendendo. Ogni giornata dispone di una franchigia di un'ora di buco alle
condizioni definite dal requisito sulla franchigia. Il sistema SHALL penalizzare
le ore di buco eccedenti la franchigia della giornata in misura superiore a quanto
ogni altro criterio sulla forma della giornata possa complessivamente guadagnare
in quella stessa giornata, cosi' che nessun altro criterio possa giustificare una
seconda ora di buco.

#### Scenario: Buco singolo contro buco doppio
- **WHEN** i vincoli hard consentono per un docente in un giorno sia una disposizione con un'ora di buco sia una con due ore di buco consecutive, a parita' di ogni altra dimensione
- **THEN** il sistema genera la disposizione con una sola ora di buco

#### Scenario: Due buchi separati nella stessa giornata
- **WHEN** i vincoli hard consentono per un docente in un giorno sia una disposizione con un solo intervallo libero fra le lezioni sia una con due intervalli liberi separati da lezioni
- **THEN** il sistema genera la disposizione con un solo intervallo libero

#### Scenario: Una seconda ora di buco non e' comprabile
- **WHEN** una disposizione con due ore di buco in una giornata migliorerebbe per quel docente la contiguita' delle classi, il bilanciamento del carico o la preferenza di fascia oraria
- **THEN** il sistema genera comunque una disposizione che non supera la franchigia di quella giornata

#### Scenario: Ore libere a inizio o fine giornata non sono buchi
- **WHEN** un docente ha ore libere prima della sua prima lezione o dopo la sua ultima lezione del giorno
- **THEN** il sistema non conteggia quelle ore come buchi

#### Scenario: Ora di indisponibilita' fra due lezioni
- **WHEN** un docente ha una lezione prima e una lezione dopo uno slot in cui e' indisponibile
- **THEN** il sistema non conteggia quello slot come buco e non lo somma alla franchigia della giornata

#### Scenario: Attesa reale accanto a un'indisponibilita'
- **WHEN** fra due lezioni di un docente ricadono sia uno slot di indisponibilita' sia uno slot libero in cui il docente potrebbe insegnare
- **THEN** il sistema conteggia come buco il solo slot libero

### Requirement: Le preferenze di fascia oraria non prevalgono sulla forma della giornata
Il sistema SHALL bilanciare le preferenze di fascia oraria mattutina o pomeridiana
con i criteri sulla forma della giornata in modo che un docente con una preferenza
di fascia oraria non riceva sistematicamente una giornata peggiore, per
contiguita', filate e buchi, di un docente senza preferenze.

#### Scenario: Docente con preferenza di fascia oraria
- **WHEN** un docente con preferenza per le prime ore ha un orario in cui anticipare una lezione introdurrebbe un avvicendamento fra classi o un buco aggiuntivo
- **THEN** il sistema non anticipa quella lezione al solo scopo di soddisfare la preferenza di fascia oraria

### Requirement: La franchigia di un'ora di buco spetta alle giornate lunghe
Il sistema SHALL riconoscere la franchigia di un'ora di buco alle sole giornate in
cui il docente svolge un numero di ore di lezione pari o superiore alla soglia
oltre la quale una filata continua di lezioni e' considerata troppo lunga. Nelle
giornate al di sotto di quella soglia la franchigia SHALL essere nulla e gia' la
prima ora di buco SHALL essere penalizzata come un'ora eccedente. Il sistema SHALL
derivare da questa regola la proporzionalita' fra monte ore e buchi, senza un
criterio separato sul monte ore settimanale.

#### Scenario: Giornata lunga
- **WHEN** un docente svolge in un giorno un numero di ore pari o superiore alla soglia di filata lunga e i vincoli hard consentono di collocarvi un'ora libera intermedia
- **THEN** il sistema puo' generare la giornata con quell'ora libera senza che questa sia trattata come un difetto

#### Scenario: Giornata corta
- **WHEN** un docente svolge in un giorno un numero di ore inferiore alla soglia di filata lunga
- **THEN** il sistema genera quelle ore senza alcuna ora libera intermedia, salvo che i vincoli hard non lo consentano

#### Scenario: Docente con monte ore ridotto
- **WHEN** un docente ha un monte ore settimanale che le sue giornate lavorabili distribuiscono tutte al di sotto della soglia di filata lunga
- **THEN** il sistema genera per quel docente una settimana priva di buchi, salvo che i vincoli hard non lo consentano

### Requirement: Le preferenze sui buchi agiscono sulla settimana
Il sistema SHALL applicare i criteri sulla forma della giornata a ogni docente,
qualunque sia la sua preferenza di scheduling, inclusa l'assenza di preferenza. Le
preferenze di raggruppamento e di distribuzione SHALL agire sul numero di giornate
della settimana che utilizzano la propria franchigia, non sull'intensita' dei
criteri interni alla giornata: la preferenza di raggruppamento SHALL ridurre il
numero di giornate con un'ora di buco, la preferenza di distribuzione SHALL
aumentarlo fino a una giornata lunga con il proprio stacco. Nessuna preferenza
SHALL consentire il superamento della franchigia di una giornata, ne' influire sul
criterio di contiguita' delle ore della stessa classe.

#### Scenario: Docente senza preferenza
- **WHEN** un docente non ha impostato alcuna preferenza di scheduling
- **THEN** il sistema applica comunque i criteri di contiguita', filata e buco alla sua giornata e mantiene contenuto il numero di giornate con un'ora di buco

#### Scenario: Preferenza di distribuzione
- **WHEN** un docente ha impostato la preferenza di distribuzione delle lezioni e i vincoli hard consentono di collocare un'ora libera in piu' di una delle sue giornate lunghe
- **THEN** il sistema gli assegna un'ora libera in ciascuna di quelle giornate anziche' concentrare piu' ore libere in una sola

#### Scenario: La preferenza di distribuzione non supera la franchigia
- **WHEN** un docente ha impostato la preferenza di distribuzione delle lezioni
- **THEN** il sistema non genera per lui alcuna giornata con piu' di un'ora di buco, ne' alcuna ora di buco in una giornata corta

#### Scenario: Preferenza di raggruppamento
- **WHEN** un docente ha impostato la preferenza di raggruppamento delle lezioni e una sua giornata ammette sia una disposizione contigua sia una con l'ora di stacco
- **THEN** il sistema genera la disposizione contigua ogni volta che la filata che ne risulta non raggiunge le cinque ore, riducendo cosi' il numero di giornate con un'ora di buco rispetto a un docente senza preferenza

#### Scenario: Le preferenze sui buchi non toccano la contiguita' delle classi
- **WHEN** due docenti con lo stesso orario di lezione hanno preferenze sui buchi diverse
- **THEN** il sistema applica a entrambi la stessa intensita' di criterio sulla contiguita' delle ore svolte in una stessa classe
